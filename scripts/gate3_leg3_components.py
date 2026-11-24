"""Gate 3 leg 3 / G3-3: component-versus-source quantification.

Criterion pre-registered in research/DECISIONS.md (2026-11-23): descriptive, no pass/fail.
Reports the fraction of candidates with another FIRST component within 1' and 2.25', with
bootstrap CIs, and the dihedral flip rate split by that flag.

Method note (DECISIONS.md, 2026-11-23): the pre-registered method was a bulk fetch of the
full catalogue with the recovered row count verified against the catalogue total. The TAP
host the notebooks hard-code is dead and the VizieR CfA mirror rate limits so hard that
multi-position queries managed one batch of 25 in ten minutes. The catalogue is therefore
taken from its authoritative source, the FIRST survey's own distribution at STScI, which
restores the pre-registered method exactly: one bulk fetch, row count verified.
first_14dec17 is the release VizieR serves as VIII/92/first14, and it reads back as
946 432 rows - the same total the notebook obtained from VizieR.

Prerequisite (one 69 MB download, cached):
    curl -L -o data_external/first_catalogue/first_14dec17.fits.gz \\
        https://sundog.stsci.edu/first/catalogs/first_14dec17.fits.gz

Run:  python -u scripts/gate3_leg3_components.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.utils.exceptions import AstropyWarning

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics  # noqa: E402

warnings.simplefilter("ignore", category=AstropyWarning)

CATALOGUE_FILE = config.REPO_ROOT / "data_external" / "first_catalogue" / "first_14dec17.fits.gz"
EXPECTED_ROWS = 946_432  # the total the notebook read from VizieR VIII/92/first14
SELF_MATCH_ARCSEC = 2.0  # FIRST's beam is 5.4", so nothing distinct is catalogued this close


def load_catalogue() -> pd.DataFrame:
    if not CATALOGUE_FILE.exists():
        raise FileNotFoundError(
            f"{CATALOGUE_FILE} not found. Download it first:\n"
            "  curl -L -o data_external/first_catalogue/first_14dec17.fits.gz \\\n"
            "    https://sundog.stsci.edu/first/catalogs/first_14dec17.fits.gz"
        )
    t = Table.read(CATALOGUE_FILE)
    print(f"catalogue rows read: {len(t)} (expected {EXPECTED_ROWS})", flush=True)
    if len(t) != EXPECTED_ROWS:
        raise RuntimeError(
            f"read {len(t)} rows, expected {EXPECTED_ROWS}; this is not the release the "
            "candidate sample was drawn from, so the density would not be comparable."
        )
    return pd.DataFrame({
        "ra": np.asarray(t["RA"], dtype=float),
        "dec": np.asarray(t["DEC"], dtype=float),
        "major": np.asarray(t["MAJOR"], dtype=float),
        "fint": np.asarray(t["FINT"], dtype=float),
    })


def main() -> None:
    print("=== Gate 3 leg 3 / G3-3: component vs source ===", flush=True)
    cat = load_catalogue()
    cand = data.clean_candidates().reset_index(drop=True)
    print(f"matching {len(cand)} candidates against {len(cat)} components", flush=True)

    cand_c = SkyCoord(cand.RAJ2000.values * u.deg, cand.DEJ2000.values * u.deg)
    cat_c = SkyCoord(cat.ra.values * u.deg, cat.dec.values * u.deg)

    i_cand, i_cat, sep, _ = cat_c.search_around_sky(cand_c, 2.25 * u.arcmin)
    sep_as = sep.arcsec
    # Every candidate is itself in the catalogue; drop that pair.
    is_self = sep_as < SELF_MATCH_ARCSEC
    n_self = int(is_self.sum())
    print(f"pairs within 2.25': {len(i_cand)}, of which {n_self} are self-matches", flush=True)
    if n_self != len(cand):
        raise RuntimeError(
            f"{n_self} self-matches for {len(cand)} candidates; every candidate must match "
            "itself exactly once, otherwise the coordinates or the release are wrong."
        )
    i_cand, i_cat, sep_as = i_cand[~is_self], i_cat[~is_self], sep_as[~is_self]

    out = {
        "catalogue_rows": int(len(cat)),
        "catalogue_file": CATALOGUE_FILE.name,
        "n_candidates": int(len(cand)),
        "n_other_component_pairs": int(len(i_cand)),
    }

    flags = {}
    for radius in (1.0, 2.25):
        m = sep_as <= radius * 60.0
        counts = np.zeros(len(cand), dtype=int)
        np.add.at(counts, i_cand[m], 1)
        has = counts > 0
        flags[radius] = has
        r = diagnostics.rate_with_ci(has)
        out[f"frac_with_neighbour_{radius}arcmin"] = r
        out[f"neighbour_count_{radius}arcmin"] = {
            "median": float(np.median(counts)), "mean": float(counts.mean()),
            "max": int(counts.max())}
        print(f"\n  another component within {radius:.2f}': {100*r['rate']:.1f}% "
              f"[{100*r['ci_lo']:.1f}, {100*r['ci_hi']:.1f}]  ({r['k']}/{r['n']})")
        print(f"     count per candidate: median {np.median(counts):.0f}, "
              f"mean {counts.mean():.2f}, max {counts.max()}")

    nearest = pd.Series(sep_as).groupby(i_cand).min()
    out["nearest_other_component_arcsec"] = {
        "n_with_any_within_2.25arcmin": int(len(nearest)),
        "median": float(nearest.median()),
        "p10": float(nearest.quantile(0.10)),
        "p90": float(nearest.quantile(0.90)),
    }
    print(f"\n  nearest other component (for the {len(nearest)} candidates that have one "
          f"within 2.25'):\n     median {nearest.median():.1f}\", "
          f"p10 {nearest.quantile(.10):.1f}\", p90 {nearest.quantile(.90):.1f}\"")

    vp = np.load(config.RESEARCH_DIR / "_view_probs" / "candidates.npy")
    flip = diagnostics.dihedral_flip_flags(vp)
    print("\n  === flip rate split by multi-component flag (cached Gate 2 tensor) ===")
    for radius, has in flags.items():
        multi = diagnostics.rate_with_ci(flip[has])
        single = diagnostics.rate_with_ci(flip[~has])
        disjoint = not diagnostics.intervals_overlap(multi, single)
        contributing = bool(disjoint and multi["rate"] > single["rate"])
        out[f"flip_split_{radius}arcmin"] = {
            "multi_component": multi, "single_component": single,
            "cis_disjoint": bool(disjoint), "contributing_cause": contributing}
        print(f"    within {radius:.2f}': multi {100*multi['rate']:5.1f}% "
              f"[{100*multi['ci_lo']:4.1f},{100*multi['ci_hi']:5.1f}] (n={multi['n']:4d})  "
              f"single {100*single['rate']:5.1f}% "
              f"[{100*single['ci_lo']:4.1f},{100*single['ci_hi']:5.1f}] (n={single['n']:4d})  "
              f"disjoint: {str(disjoint):5s} -> component confusion "
              f"{'IS' if contributing else 'is NOT'} a contributing cause")

    pd.DataFrame({
        "FIRST": cand.FIRST.values,
        "has_neighbour_1arcmin": flags[1.0],
        "has_neighbour_2p25arcmin": flags[2.25],
    }).to_csv(config.RESEARCH_DIR / "candidate_component_flags.csv", index=False)

    p = config.RESEARCH_DIR / "gate3_leg3_components.json"
    p.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {p}")
    print(f"Wrote {config.RESEARCH_DIR / 'candidate_component_flags.csv'}")


if __name__ == "__main__":
    main()
