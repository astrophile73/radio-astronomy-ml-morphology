"""Paths and constants for the R1 analysis.

Replaces the hard-coded ``I:\\...`` paths in the notebooks. Everything is resolved
relative to the repository root, so the analysis runs from a clean clone on any drive.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

FITS_ROOT = REPO_ROOT / "FIRST_FITS_CUTOUTS" / "FIRST"
CANDIDATE_DIR = FITS_ROOT / "EXTENDED_CANDIDATES"
PAIRED_DIR = FITS_ROOT / "MIRABEST_PAIRED_TEST"

MIRABEST_ROOT = REPO_ROOT / "mirabest_data"
MIRABEST_BATCH_DIR = MIRABEST_ROOT / "F_batches"
MIRABEST_TARBALL = MIRABEST_ROOT / "MiraBest_F_batches.tar.gz"
# Used only when MIRABEST_BATCH_DIR cannot be read; see r1.data.batch_dir().
MIRABEST_CACHE_DIR = MIRABEST_ROOT / "_batches_cache"

RESEARCH_DIR = REPO_ROOT / "research"

# Derived products written by the notebooks, consumed as fixtures here.
CLEAN_CANDIDATES_CSV = CANDIDATE_DIR / "FIRST_clean_candidates.csv"
CLEAN_NAMES_CSV = CANDIDATE_DIR / "FIRST_clean_names_final.csv"
CLEAN_X_NPY = CANDIDATE_DIR / "FIRST_clean_X_final.npy"
PREDICTIONS_CSV = CANDIDATE_DIR / "FIRST_predictions_master_v2.csv"

ENSEMBLE_CHECKPOINTS = [REPO_ROOT / f"ensemble_seed{i}.pth" for i in range(5)]

# ---------------------------------------------------------------------------
# Instrument and preprocessing constants
# ---------------------------------------------------------------------------

FIRST_PIXEL_SCALE_ARCSEC = 1.8
FIRST_BEAM_ARCSEC = 5.4
CUTOUT_PIXELS = 150
# 150 px x 1.8" = 270" = 4.5'. This matches MiraBest's 150 x 150 image format;
# the "3 arcmin" in the README and in main.ipynb cell 0 is an error in the prose.
CUTOUT_SIZE_ARCMIN = CUTOUT_PIXELS * FIRST_PIXEL_SCALE_ARCSEC / 60.0

# T1 selected 'linear' over 'asinh' by KS statistic; see DECISIONS.md 2026-11-21.
CHOSEN_MODE = "linear"

# ---------------------------------------------------------------------------
# External services
# ---------------------------------------------------------------------------

# The notebooks hard-code the VizieR TAP service at tapvizier.cds.unistra.fr. As of
# 2026-11-23 that host does not answer on port 80 or 443 (connect timeout), and CDS's
# viz-bin paths return 404, so data_extraction.ipynb cannot run as written. The Harvard
# CfA mirror serves the same catalogues and answers normally.
VIZIER_SERVER = "vizier.cfa.harvard.edu"
FIRST_CATALOGUE = "VIII/92/first14"

# MiraBest_F label index -> class code, from batches.meta['label_names'].
MIRABEST_LABEL_NAMES = ["100", "102", "104", "110", "112", "200", "201", "210", "300", "310"]

# Cohort definitions, taken from the MBFR* classes in MiraBest_F.py.
# Note: MBHybrid's docstring in MiraBest_F.py misstates its codes as [110, 112] and
# [210]; its code uses label indices [8] and [9], i.e. 300 and 310. The code is what
# the published n = 34 corresponds to, so the code is what is replicated here.
COHORT_LABELS = {
    "confident": [0, 1, 2, 5, 6],   # 100, 102, 104 (FR-I) + 200, 201 (FR-II)
    "uncertain": [3, 4, 7],         # 110, 112 (FR-I) + 210 (FR-II)
    "hybrid": [8, 9],               # 300, 310
}
# Within 'confident', which labels are FR-II (target 1).
FRII_LABELS = [5, 6]

# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

SEED = 0
N_BOOTSTRAP = 10_000


def torch_threads() -> int:
    """Use all cores for CPU inference; this analysis has no GPU dependency."""
    return int(os.environ.get("R1_THREADS", os.cpu_count() or 1))
