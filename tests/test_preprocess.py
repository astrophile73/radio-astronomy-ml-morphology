"""Regression tests for the preprocessing pipeline.

The first test is the one that matters: if ``r1.preprocess`` does not reproduce the stored
``FIRST_clean_X_final.npy``, then no number derived from that array can be reused, and the
diagnostics have to be recomputed from the FITS files instead.
"""

from __future__ import annotations

import numpy as np
import pytest

from r1 import config, data, preprocess

# Reproducing all 1996 cutouts takes a few minutes; the subset is the default and the
# full check runs with --runslow.
SUBSET = 120


@pytest.fixture(scope="module")
def stored():
    X = data.candidate_images()
    names = data.candidate_names()["FIRST"].tolist()
    assert len(X) == len(names) == 1996, (len(X), len(names))
    return X, names


def _compare(stored_X, names, idx):
    paths = data.candidate_fits_paths([names[i] for i in idx])
    got, kept = preprocess.preprocess_many(paths, mode=config.CHOSEN_MODE)
    assert kept == list(range(len(idx))), "some cutouts failed to preprocess"
    want = stored_X[idx]
    assert got.shape == want.shape
    return got, want


def _assert_reproduces(got, want, max_mask_disagreements):
    """The reproduction contract for ``preprocess_cutout``.

    Measured on 2026-11-23 against the stored array (astropy 8.0.1, numpy 2.5.3): over all
    1996 candidates, 4 images and 6 pixels of 44.9 million differ. Every difference is a
    pixel sitting exactly on the 3-sigma cut, where a last-bit difference in ``std_bg``
    between astropy versions decides inclusion; the ratio of retained pixel values is
    exactly 1.0. So the contract asserted here is the one that actually matters
    scientifically: retained values agree to within 1e-4 relative, the mask moves by no
    more than a handful of boundary pixels, and no aggregate statistic moves at all.
    Bitwise equality is deliberately *not* asserted, because it is not reproducible across
    astropy versions and nothing downstream depends on it.
    """
    both = (got > 0) & (want > 0)
    np.testing.assert_allclose(got[both], want[both], rtol=1e-4, atol=1e-6)

    n_disagree = int(((got > 0) != (want > 0)).sum())
    assert n_disagree <= max_mask_disagreements, (
        f"{n_disagree} mask disagreements exceeds the documented bound "
        f"{max_mask_disagreements}; the 3-sigma threshold behaviour has changed materially"
    )

    # Aggregate statistics must be unchanged: these are what H1 and the diagnostics use.
    sg, sw = preprocess.image_stats(got), preprocess.image_stats(want)
    assert np.median(sg["n_nonzero"]) == np.median(sw["n_nonzero"])
    np.testing.assert_allclose(
        np.nanmedian(sg["median_nonzero"]), np.nanmedian(sw["median_nonzero"]), rtol=1e-6
    )


def test_reproduces_stored_array_subset(stored):
    stored_X, names = stored
    rng = np.random.default_rng(config.SEED)
    idx = np.sort(rng.choice(len(names), size=SUBSET, replace=False))
    got, want = _compare(stored_X, names, idx)
    _assert_reproduces(got, want, max_mask_disagreements=4)


@pytest.mark.slow
def test_reproduces_stored_array_full(stored):
    """Full-sample contract: at most 10 boundary pixels across all 1996 images."""
    stored_X, names = stored
    got, want = _compare(stored_X, names, np.arange(len(names)))
    _assert_reproduces(got, want, max_mask_disagreements=10)
    n_imgs = int((np.abs(got - want).reshape(len(want), -1) > 0).any(1).sum())
    assert n_imgs <= 6, f"{n_imgs} images differ; expected at most 6"


def test_output_range_and_dtype(stored):
    stored_X, names = stored
    img = preprocess.preprocess_cutout(data.candidate_fits_paths([names[0]])[0])
    assert img.shape == (config.CUTOUT_PIXELS, config.CUTOUT_PIXELS)
    assert img.dtype == np.float32
    assert img.min() >= 0.0 and img.max() <= 1.0
    # The 3-sigma cut leaves a hard zero background, as MiraBest's convention expects.
    assert (img == 0).any()


def test_rejects_wrong_shape(tmp_path):
    from astropy.io import fits

    p = tmp_path / "bad.fits"
    fits.PrimaryHDU(np.zeros((100, 100), dtype=np.float32)).writeto(p)
    with pytest.raises(ValueError, match="unexpected shape"):
        preprocess.preprocess_cutout(p)


def test_preprocess_many_reports_failures(tmp_path):
    """A bad file must be reported by index, not silently dropped (notebook cell 12 bug)."""
    from astropy.io import fits

    good = tmp_path / "good.fits"
    bad = tmp_path / "bad.fits"
    fits.PrimaryHDU(np.random.default_rng(0).normal(size=(150, 150)).astype(np.float32)).writeto(good)
    fits.PrimaryHDU(np.zeros((10, 10), dtype=np.float32)).writeto(bad)
    X, kept = preprocess.preprocess_many([good, bad, good])
    assert kept == [0, 2]
    assert len(X) == 2


def test_alternative_scales_leave_the_default_path_untouched(stored):
    """scale='max' must stay byte-identical to the published behaviour."""
    stored_X, names = stored
    p = data.candidate_fits_paths([names[3]])[0]
    default = preprocess.preprocess_cutout(p)
    explicit = preprocess.preprocess_cutout(p, scale="max")
    np.testing.assert_allclose(default, explicit, rtol=0, atol=0)
    np.testing.assert_allclose(default, stored_X[3], rtol=1e-4, atol=1e-6)


@pytest.mark.parametrize("scale", ["p99", "lcc_max"])
def test_alternative_scales_are_bounded_and_change_the_image(stored, scale):
    stored_X, names = stored
    p = data.candidate_fits_paths([names[3]])[0]
    img = preprocess.preprocess_cutout(p, scale=scale)
    assert img.dtype == np.float32
    assert img.min() >= 0.0 and img.max() <= 1.0 + 1e-6
    # A robust scale must raise the typical pixel value relative to dividing by the max.
    base = preprocess.preprocess_cutout(p, scale="max")
    m = base > 0
    assert img[m].mean() >= base[m].mean()
    # The 3-sigma mask itself must not move: only the scaling differs.
    np.testing.assert_array_equal(img > 0, base > 0)


def test_unknown_scale_is_rejected(stored):
    stored_X, names = stored
    p = data.candidate_fits_paths([names[0]])[0]
    with pytest.raises(ValueError, match="unknown scale"):
        preprocess.preprocess_cutout(p, scale="nonsense")


def test_cutout_geometry_matches_mirabest():
    """4.5 arcmin at 1.8 arcsec/px is 150 px, which is MiraBest's image format.

    Guards the README's "3 arcmin" error from creeping back into the code.
    """
    assert config.CUTOUT_PIXELS == 150
    assert config.CUTOUT_SIZE_ARCMIN == pytest.approx(4.5)
