"""Dataset access: MiraBest batches and the blind FIRST candidate sample.

The MiraBest batches are read directly from ``mirabest_data/F_batches`` when that is
readable. On this machine the directory denies read access (PermissionError 13), so
``batch_dir()`` falls back to extracting the distributed tarball into
``mirabest_data/_batches_cache``. The tarball's MD5 is checked by MiraBest_F.py upstream;
here only the member layout is relied on.
"""

from __future__ import annotations

import pickle
import re
import tarfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

TRAIN_BATCHES = [f"data_batch_{i}" for i in range(1, 8)]
TEST_BATCHES = ["test_batch"]

# MiraBest_F encodes each source in its PNG filename:
#   <class>_<RA><+/-Dec>_<z>_<size_arcsec>.png
_FILENAME_RE = re.compile(r"/(\d+)_([\d.]+)([+-][\d.]+)_([\d.]+)_([\d.]+)\.png")


def _readable(d: Path) -> bool:
    try:
        with open(d / "data_batch_1", "rb"):
            return True
    except OSError:
        return False


@lru_cache(maxsize=1)
def batch_dir() -> Path:
    """Return a readable directory containing the MiraBest F_batches files."""
    if _readable(config.MIRABEST_BATCH_DIR):
        return config.MIRABEST_BATCH_DIR
    cache = config.MIRABEST_CACHE_DIR / "F_batches"
    if _readable(cache):
        return cache
    if not config.MIRABEST_TARBALL.exists():
        raise FileNotFoundError(
            f"{config.MIRABEST_BATCH_DIR} is unreadable and {config.MIRABEST_TARBALL} "
            "is missing; re-download MiraBest_F or fix the directory permissions."
        )
    config.MIRABEST_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with tarfile.open(config.MIRABEST_TARBALL) as t:
        t.extractall(config.MIRABEST_CACHE_DIR)
    if not _readable(cache):
        raise OSError(f"extracted {config.MIRABEST_TARBALL} but {cache} is still unreadable")
    return cache


@lru_cache(maxsize=16)
def _load_batch(name: str) -> dict:
    with open(batch_dir() / name, "rb") as f:
        return pickle.load(f, encoding="latin1")


def mirabest_catalogue(splits: tuple[str, ...] = ("train", "test")) -> pd.DataFrame:
    """One row per MiraBest source, parsed from the batch filenames.

    Columns: split, batch, batch_index, label, cls, ra, dec, z, size_arcsec.
    ``batch_index`` indexes the *full* batch, which is what the paired-cutout filenames
    ``MB_<split>_<batch_index>.fits`` were written against.
    """
    files = {"train": TRAIN_BATCHES, "test": TEST_BATCHES}
    rows = []
    for split in splits:
        for name in files[split]:
            e = _load_batch(name)
            for i, (fn, label) in enumerate(zip(e["filenames"], e["labels"])):
                m = _FILENAME_RE.search(fn)
                if m is None:
                    raise ValueError(f"unparsable MiraBest filename: {fn!r}")
                rows.append(
                    {
                        "split": split,
                        "batch": name,
                        "batch_index": i,
                        "label": int(label),
                        "cls": m.group(1),
                        "ra": float(m.group(2)),
                        "dec": float(m.group(3)),
                        "z": float(m.group(4)),
                        "size_arcsec": float(m.group(5)),
                    }
                )
    return pd.DataFrame(rows)


def mirabest_images(rows: pd.DataFrame) -> np.ndarray:
    """Load the MiraBest images for the given catalogue rows, in the order given.

    Pixel convention matches the notebook: uint8 0-255 reshaped to 150 x 150 and divided
    by 255, i.e. MiraBest's own preprocessing, not ``preprocess_cutout``.
    """
    out = np.empty((len(rows), config.CUTOUT_PIXELS, config.CUTOUT_PIXELS), dtype=np.float32)
    for pos, (_, r) in enumerate(rows.iterrows()):
        e = _load_batch(r.batch)
        d = np.asarray(e["data"])[r.batch_index]
        out[pos] = d.reshape(config.CUTOUT_PIXELS, config.CUTOUT_PIXELS).astype(np.float32) / 255.0
    return out


def cohort(name: str, splits: tuple[str, ...] = ("train", "test")) -> pd.DataFrame:
    """Rows for one of the cohorts defined in config.COHORT_LABELS."""
    cat = mirabest_catalogue(splits)
    labels = config.COHORT_LABELS[name]
    sub = cat[cat.label.isin(labels)].reset_index(drop=True)
    if name == "confident":
        sub = sub.assign(true_label=sub.label.isin(config.FRII_LABELS).astype(int))
    return sub


def legacy_name_is_unambiguous(split: str) -> bool:
    """Does the notebook's ``MB_<split>_<batch_index>.fits`` scheme identify a source?

    Only if the split has a single batch. ``batch_index`` counts within a batch and every
    MiraBest batch holds 157 sources, so for the 7-batch training split the legacy name
    collides 7 ways. See ``paired_cutout_path``.
    """
    return len({"train": TRAIN_BATCHES, "test": TEST_BATCHES}[split]) == 1


def canonical_paired_cutout_path(row) -> Path:
    """Collision-free name for a paired cutout: batch included."""
    return config.PAIRED_DIR / f"MB_{row.split}_{row.batch}_{row.batch_index}.fits"


def paired_cutout_path(row) -> Path:
    """Path to the FIRST cutout re-downloaded at a MiraBest source's position.

    ``main.ipynb`` cell 26 named these ``MB_<split>_<batch_index>.fits``. ``batch_index``
    is an index *within a batch*, and all 8 MiraBest batches run 0-156, so that name is
    only unique for the single-batch test split. For the 7-batch training split, 729
    confident sources collapse onto 107 filenames, up to 7 sources each, and the download
    helper skipped any name that already existed - so most training sources were paired
    with a cutout downloaded for a different galaxy. Those files cannot be attributed to a
    source after the fact, because 8 download threads raced for each name.

    This function therefore prefers the canonical name, accepts the legacy name only where
    it is provably unambiguous, and otherwise returns the canonical path (which will not
    exist) so that callers skip the source instead of silently using the wrong image.
    """
    canonical = canonical_paired_cutout_path(row)
    if canonical.exists():
        return canonical
    if legacy_name_is_unambiguous(row.split):
        legacy = config.PAIRED_DIR / f"MB_{row.split}_{row.batch_index}.fits"
        if legacy.exists():
            return legacy
    return canonical


def clean_candidates() -> pd.DataFrame:
    """The blind FIRST candidate sample that survived the quality gate (n = 1996)."""
    return pd.read_csv(config.CLEAN_CANDIDATES_CSV)


def candidate_images() -> np.ndarray:
    """The stored preprocessed candidate array, in the order of CLEAN_NAMES_CSV."""
    return np.load(config.CLEAN_X_NPY)


def candidate_names() -> pd.DataFrame:
    return pd.read_csv(config.CLEAN_NAMES_CSV)


def candidate_fits_paths(names: list[str]) -> list[Path]:
    return [config.CANDIDATE_DIR / f"FIRST_{n}.fits" for n in names]
