"""FITS cutout preprocessing.

``preprocess_cutout`` is ported from ``main.ipynb`` cell 12 with its numerical behaviour
unchanged. ``tests/test_preprocess.py`` asserts that it reproduces the stored
``FIRST_clean_X_final.npy`` exactly, which is what licenses reusing every number that
array produced.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.utils.exceptions import AstropyWarning

from . import config

warnings.simplefilter("ignore", category=AstropyWarning)


def _scale_value(data: np.ndarray, scale: str) -> float:
    """The divisor used to bring a thresholded image into [0, 1].

    ``'max'`` is the published behaviour: the single brightest pixel sets the scale. The
    others exist only for the G3-1b sensitivity analysis, because a candidate's 3-sigma mask
    is fragmented (median 25 components) and a noise spike can set its scale where it would
    not set a MiraBest source's.
    """
    nz = data[data > 0]
    if nz.size == 0:
        return 0.0
    if scale == "max":
        return float(data.max())
    if scale == "p99":
        return float(np.percentile(nz, 99))
    if scale == "lcc_max":
        from scipy import ndimage

        lab, k = ndimage.label(data > 0)
        if k == 0:
            return 0.0
        sizes = ndimage.sum(data > 0, lab, range(1, k + 1))
        biggest = int(np.argmax(sizes)) + 1
        return float(data[lab == biggest].max())
    raise ValueError(f"unknown scale {scale!r}")


def preprocess_cutout(
    fits_path: str | Path, mode: str = config.CHOSEN_MODE, scale: str = "max"
) -> np.ndarray:
    """Background-subtract, threshold at 3 sigma, optionally asinh-stretch, scale to [0, 1].

    Matches the MiraBest convention of a dark background with bright structure.
    ``mode='linear'`` skips the asinh step; ``mode='asinh'`` applies it.

    ``scale='max'`` is the published behaviour and its code path is left byte-identical;
    ``'p99'`` and ``'lcc_max'`` are used only by the Gate 3 sensitivity analysis and clip
    at 1. The default is never changed on the basis of that analysis.

    Raises ValueError if the cutout is not 150 x 150, as the notebook does, rather than
    silently resizing.
    """
    with fits.open(fits_path) as h:
        data = np.squeeze(h[0].data.astype(np.float32))
    if data.shape != (config.CUTOUT_PIXELS, config.CUTOUT_PIXELS):
        raise ValueError(f"unexpected shape {data.shape}")
    _, median_bg, std_bg = sigma_clipped_stats(data, sigma=3.0, maxiters=5)
    data = np.nan_to_num(data, nan=0.0) - median_bg
    data[data < 3.0 * std_bg] = 0.0
    if mode == "asinh":
        data = np.arcsinh(data / (std_bg if std_bg > 0 else 1e-4))
    if scale == "max":
        max_val = data.max()
        return data / max_val if max_val > 0 else np.zeros_like(data)
    v = _scale_value(data, scale)
    if v <= 0:
        return np.zeros_like(data)
    return np.clip(data / np.float32(v), 0.0, 1.0).astype(np.float32)


def preprocess_many(
    paths: list[str | Path], mode: str = config.CHOSEN_MODE, scale: str = "max"
) -> tuple[np.ndarray, list[int]]:
    """Preprocess a list of cutouts, returning the stack and the indices that succeeded.

    Unlike ``main.ipynb`` cell 12, failures are reported by index instead of being
    dropped by a bare ``except: pass``, so a caller can never silently misalign the
    image stack against its catalogue rows.
    """
    imgs: list[np.ndarray] = []
    kept: list[int] = []
    for i, p in enumerate(paths):
        try:
            imgs.append(preprocess_cutout(p, mode=mode, scale=scale))
            kept.append(i)
        except Exception:  # noqa: BLE001 - recorded, not hidden
            continue
    if not imgs:
        return np.empty((0, config.CUTOUT_PIXELS, config.CUTOUT_PIXELS), dtype=np.float32), []
    return np.stack(imgs), kept


def structure_stats(A: np.ndarray) -> dict[str, np.ndarray]:
    """Per-image structure measures of the 3-sigma mask, measured identically on any sample.

    The whole-mask bounding box is deliberately absent: it was pre-registered as a size proxy
    on 2026-11-21, measured, and withdrawn on 2026-11-23 because candidate masks are
    fragmented (median 25 components) so the box tracks isolated noise spikes near the frame
    edge and reports candidates as *larger* than MiraBest. The largest connected component is
    the structure-bearing statistic; its extent reproduces MiraBest's catalogued median
    angular size, which calibrates it. See research/DECISIONS.md.
    """
    from scipy import ndimage

    n = len(A)
    nz = np.zeros(n)
    lcc = np.zeros(n)
    lcc_extent = np.zeros(n)
    frac_lcc = np.zeros(n)
    n_comp = np.zeros(n)
    for i, a in enumerate(A):
        m = a > 0
        total = int(m.sum())
        nz[i] = total
        lab, k = ndimage.label(m)
        n_comp[i] = k
        if k == 0 or total == 0:
            continue
        sizes = ndimage.sum(m, lab, range(1, k + 1))
        j = int(np.argmax(sizes)) + 1
        lcc[i] = float(sizes[j - 1])
        frac_lcc[i] = lcc[i] / total
        ys, xs = np.nonzero(lab == j)
        lcc_extent[i] = float(max(ys.max() - ys.min(), xs.max() - xs.min()) + 1)
    return {
        "n_nonzero": nz,
        "largest_component_px": lcc,
        "largest_component_extent_px": lcc_extent,
        "frac_in_largest_component": frac_lcc,
        "n_components": n_comp,
    }


def image_stats(A: np.ndarray) -> dict[str, np.ndarray]:
    """Per-image summary statistics used to compare pixel-value distributions."""
    flat = A.reshape(len(A), -1)
    nz = flat > 0
    n = nz.sum(1)
    med_nz = np.array([np.median(a[a > 0]) if (a > 0).any() else np.nan for a in flat])
    return {
        "mean": flat.mean(1),
        "n_nonzero": n.astype(float),
        "frac_nonzero": n / flat.shape[1],
        "median_nonzero": med_nz,
    }
