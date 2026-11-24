"""Sample selection and cutout retrieval for the blind FIRST candidate set.

Replaces the catalogue half of ``data_extraction.ipynb``, which cannot run any more: it
selects its 10 000 sources through ``tapvizier.cds.unistra.fr``, and that host stopped
answering on both port 80 and 443 in November 2026 (CDS's ``viz-bin`` paths also return
404). Rather than depend on a TAP service that may or may not come back, the catalogue is
read from the FIRST survey's own distribution at STScI: one 69 MB file, no query language,
and a row count that can be checked against the published total.

The cutout half still uses NASA SkyView, which answers normally.

Typical use:

    from r1 import extract
    cat = extract.load_catalogue()                 # 946 432 rows, verified
    sample = extract.select_sample(cat)            # the 1-in-N spread used by the project
    cand = extract.select_extended_candidates(sample)
    extract.download_cutouts(cand, out_dir)        # network

The selection functions are pure and deterministic, so they are testable without network.
"""

from __future__ import annotations

import io
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

CATALOGUE_URL = "https://sundog.stsci.edu/first/catalogs/first_14dec17.fits.gz"
CATALOGUE_FILE = config.REPO_ROOT / "data_external" / "first_catalogue" / "first_14dec17.fits.gz"
EXPECTED_ROWS = 946_432

SKYVIEW_URL = "https://skyview.gsfc.nasa.gov/cgi-bin/pskcall"
FIRST_SURVEY = "vla first (1.4 ghz)"

# The morphology gate from main.ipynb cell 6, unchanged.
MIN_FLUX_RATIO = 1.25
MIN_MAJ_ARCSEC = 6.0
MIN_SNR = 7.0


def download_catalogue(dest: Path = CATALOGUE_FILE) -> Path:
    """Fetch the FIRST 14dec17 catalogue if it is not already on disk (69 MB)."""
    if dest.exists():
        return dest
    import requests

    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(CATALOGUE_URL, stream=True, timeout=(10, 600)) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        tmp.replace(dest)
    return dest


def load_catalogue(path: Path = CATALOGUE_FILE, verify: bool = True) -> pd.DataFrame:
    """The full FIRST component catalogue, with the row count verified.

    Columns are renamed to the VizieR spellings the rest of the project uses, so code
    written against the old TAP output keeps working.
    """
    from astropy.table import Table

    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Call r1.extract.download_catalogue(), or:\n"
            f"  curl -L -o {path} {CATALOGUE_URL}"
        )
    t = Table.read(path)
    if verify and len(t) != EXPECTED_ROWS:
        raise RuntimeError(
            f"read {len(t)} rows, expected {EXPECTED_ROWS}: this is not the release the "
            "published sample was drawn from, so results would not be comparable."
        )
    df = pd.DataFrame({
        "RAJ2000": np.asarray(t["RA"], dtype=float),
        "DEJ2000": np.asarray(t["DEC"], dtype=float),
        "Fpeak": np.asarray(t["FPEAK"], dtype=float),
        "Fint": np.asarray(t["FINT"], dtype=float),
        "Rms": np.asarray(t["RMS"], dtype=float),
        "Maj": np.asarray(t["MAJOR"], dtype=float),
        "Min": np.asarray(t["MINOR"], dtype=float),
        "PA": np.asarray(t["POSANG"], dtype=float),
    })
    df.insert(0, "recno", np.arange(1, len(df) + 1))
    df.insert(1, "FIRST", [iau_name(r, d) for r, d in zip(df.RAJ2000, df.DEJ2000)])
    return df


def iau_name(ra_deg: float, dec_deg: float) -> str:
    """The FIRST catalogue's Jhhmmss.s+ddmmss source name for a position.

    The cutout files are named after this, so it must match the published convention.
    FIRST **truncates** the sexagesimal fields rather than rounding them; rounding
    reproduces only about a quarter of the published names. Truncation can leave a field
    at exactly 60 after the floor, which carries.

    Verified against the 1996 published candidate names: 1996/1996.
    """
    import math

    eps = 1e-6
    ra_h = ra_deg / 15.0
    h = int(ra_h)
    m = int((ra_h - h) * 60)
    s = math.floor((ra_h - h - m / 60.0) * 3600.0 * 10 + eps) / 10.0
    if s >= 60.0:          # carry seconds -> minutes
        s -= 60.0
        m += 1
    if m >= 60:            # carry minutes -> hours
        m -= 60
        h = (h + 1) % 24

    sign = "+" if dec_deg >= 0 else "-"
    a = abs(dec_deg)
    d = int(a)
    am = int((a - d) * 60)
    asec = math.floor((a - d - am / 60.0) * 3600.0 + eps)
    if asec >= 60:         # carry arcsec -> arcmin
        asec -= 60
        am += 1
    if am >= 60:           # carry arcmin -> degrees
        am -= 60
        d += 1
    return f"J{h:02d}{m:02d}{s:04.1f}{sign}{d:02d}{am:02d}{asec:02d}"


def select_sample(catalogue: pd.DataFrame, n_sources: int = 10_000) -> pd.DataFrame:
    """Every step-th row by ``recno``, matching the notebook's MOD(recno, step) = 0.

    The catalogue is ordered by declination, so taking a fixed stride spreads the sample
    over the whole footprint and returns the same sources on every run.
    """
    step = len(catalogue) // n_sources
    sel = catalogue[catalogue.recno % step == 0]
    return sel.head(n_sources).reset_index(drop=True)


# VizieR served these columns rounded; the STScI file carries full precision. The gate
# below uses hard thresholds, so sources sitting exactly on one flip depending on which
# precision is used. These are the decimal places VizieR returned.
VIZIER_DECIMALS = {"Fpeak": 2, "Fint": 2, "Rms": 3, "Maj": 2, "Min": 2, "PA": 0}


def select_extended_candidates(sample: pd.DataFrame,
                               vizier_rounding: bool = True) -> pd.DataFrame:
    """The morphology gate: resolved, extended and bright enough to be worth a cutout.

    ``vizier_rounding`` rounds the input columns to the precision VizieR served before
    applying the thresholds, which is what the published sample was selected with. It
    matters: five of the 1996 published candidates have an SNR of exactly 7.000 on the
    rounded values and fall below 7 on the full-precision ones (e.g. 1.03/0.147 = 7.007
    against 1.03/0.147470 = 6.984). With rounding the published sample is reproduced
    exactly; without it, five sources are lost. Pass False to select on full precision,
    which is the better choice for any *new* sample.
    """
    df = sample.copy()
    if vizier_rounding:
        for col, dp in VIZIER_DECIMALS.items():
            if col in df:
                df[col] = df[col].round(dp)
    df["SNR"] = df.Fpeak / df.Rms
    df["Flux_Ratio"] = df.Fint / df.Fpeak
    keep = ((df.Flux_Ratio >= MIN_FLUX_RATIO)
            & (df.Maj >= MIN_MAJ_ARCSEC)
            & (df.SNR >= MIN_SNR))
    return df[keep].reset_index(drop=True)


def fetch_cutout(ra: float, dec: float, out_path: Path, npix: int = config.CUTOUT_PIXELS,
                 size_arcmin: float = config.CUTOUT_SIZE_ARCMIN, attempts: int = 3) -> str:
    """One SkyView FIRST cutout. Returns 'saved', 'exists', 'no data' or 'failed'.

    The bytes are written exactly as served: the FIRST headers contain tab characters that
    astropy's strict writer rejects on round-trip.
    """
    import requests
    from astropy.io import fits

    if out_path.exists():
        return "exists"
    params = {"position": f"{ra},{dec}", "survey": FIRST_SURVEY, "pixels": f"{npix},{npix}",
              "size": size_arcmin / 60.0, "projection": "Tan", "coordinates": "J2000",
              "return": "FITS"}
    for attempt in range(attempts):
        if attempt:
            time.sleep(5 * attempt)
        try:
            r = requests.get(SKYVIEW_URL, params=params, timeout=(10, 60))
            r.raise_for_status()
            if not r.content.startswith(b"SIMPLE"):
                # A busy SkyView returns an HTML page with status 200.
                msg = " ".join(re.sub(r"<[^>]+>", " ", r.text).split())
                raise ValueError(f"not FITS, server said: {msg[:120]}")
            with fits.open(io.BytesIO(r.content)) as h:
                in_footprint = (h[0].header.get("SURVEY") == "FIRST"
                                and np.any(np.nan_to_num(h[0].data)))
            if not in_footprint:
                return "no data"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(r.content)
            return "saved"
        except Exception:  # noqa: BLE001 - the status is the return value
            continue
    return "failed"


def download_cutouts(candidates: pd.DataFrame, out_dir: Path, workers: int = 8) -> dict:
    """Fetch a cutout per candidate, returning a status tally.

    Failures are counted and returned, never silently dropped.
    """
    from concurrent.futures import ThreadPoolExecutor

    out_dir = Path(out_dir)
    rows = list(candidates.itertuples())

    def one(row):
        return fetch_cutout(row.RAJ2000, row.DEJ2000, out_dir / f"FIRST_{row.FIRST}.fits")

    counts: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for status in pool.map(one, rows):
            counts[status] = counts.get(status, 0) + 1
    return counts
