"""Label-free instability diagnostics and their uncertainties.

Every quantity here returns a point estimate with a bootstrap 95% interval, because a
number without an uncertainty does not go in the paper (CLAUDE.md §4).
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from . import config, models


# ---------------------------------------------------------------------------
# Uncertainty
# ---------------------------------------------------------------------------


def bootstrap_ci(
    x: np.ndarray,
    stat: Callable[[np.ndarray], float] = np.mean,
    n_boot: int = config.N_BOOTSTRAP,
    seed: int = config.SEED,
) -> tuple[float, float]:
    """Percentile bootstrap 95% interval for ``stat`` over the rows of ``x``."""
    x = np.asarray(x)
    n = len(x)
    if n == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        vals[b] = stat(x[rng.integers(0, n, n)])
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def paired_bootstrap_ci(
    a: np.ndarray,
    b: np.ndarray,
    stat: Callable[[np.ndarray, np.ndarray], float],
    n_boot: int = config.N_BOOTSTRAP,
    seed: int = config.SEED,
) -> tuple[float, float]:
    """Bootstrap interval for a statistic of two paired arrays, resampling sources."""
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)
    if n == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        vals[i] = stat(a[idx], b[idx])
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Used for accuracy on the n = 104 held-out set, where the finite test set and not
    seed variance dominates the uncertainty budget.
    """
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float((centre - half) / denom), float((centre + half) / denom)


# ---------------------------------------------------------------------------
# Per-source instability flags
# ---------------------------------------------------------------------------


def dihedral_flip_flags(view_probs: np.ndarray) -> np.ndarray:
    """True where the ensemble-mean label is not identical across all 8 symmetries.

    A flip means the classifier's answer depends on the image's orientation, which no
    physical FR classification can. Definition matches ``main.ipynb`` cell 31.
    """
    labels = models.ensemble_mean_per_view(view_probs) > 0.5
    return labels.any(axis=0) & ~labels.all(axis=0)


def seed_disagreement_flags(view_probs: np.ndarray) -> np.ndarray:
    """True where the 5 single-seed identity-view labels are not unanimous."""
    labels = models.identity_per_seed(view_probs) > 0.5
    return labels.min(axis=0) != labels.max(axis=0)


def ambiguity(view_probs: np.ndarray) -> np.ndarray:
    """|P - 0.5| on the TTA mean; 0 is maximally ambiguous, 0.5 is confident."""
    return np.abs(models.tta_mean(view_probs) - 0.5)


def in_uncertain_band(view_probs: np.ndarray, lo: float = 0.05, hi: float = 0.95) -> np.ndarray:
    """True where the TTA-mean probability falls in the ambiguous band."""
    p = models.tta_mean(view_probs)
    return (p > lo) & (p < hi)


# ---------------------------------------------------------------------------
# Cohort summaries
# ---------------------------------------------------------------------------


def rate_with_ci(flags: np.ndarray, seed: int = config.SEED) -> dict:
    """Fraction of True with a bootstrap interval and the Wilson interval alongside."""
    flags = np.asarray(flags, dtype=bool)
    n = len(flags)
    k = int(flags.sum())
    lo, hi = bootstrap_ci(flags.astype(float), np.mean, seed=seed)
    wlo, whi = wilson_ci(k, n)
    return {
        "n": n,
        "k": k,
        "rate": k / n if n else np.nan,
        "ci_lo": lo,
        "ci_hi": hi,
        "wilson_lo": wlo,
        "wilson_hi": whi,
    }


def median_with_ci(x: np.ndarray, seed: int = config.SEED) -> dict:
    x = np.asarray(x, dtype=float)
    lo, hi = bootstrap_ci(x, np.median, seed=seed)
    return {"n": len(x), "median": float(np.median(x)), "ci_lo": lo, "ci_hi": hi}


def cohort_summary(view_probs: np.ndarray, name: str) -> dict:
    """All label-free diagnostics for one cohort, each with an interval."""
    return {
        "cohort": name,
        "flip": rate_with_ci(dihedral_flip_flags(view_probs)),
        "seed_disagree": rate_with_ci(seed_disagreement_flags(view_probs)),
        "uncertain_band": rate_with_ci(in_uncertain_band(view_probs)),
        "ambiguity": median_with_ci(ambiguity(view_probs)),
    }


def intervals_overlap(a: dict, b: dict) -> bool:
    """Do two bootstrap intervals from rate_with_ci / median_with_ci overlap?"""
    return not (a["ci_hi"] < b["ci_lo"] or b["ci_hi"] < a["ci_lo"])
