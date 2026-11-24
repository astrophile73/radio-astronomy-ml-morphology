"""Tests for the instability metrics and the MiraBest cohort construction."""

from __future__ import annotations

import numpy as np
import pytest

from r1 import config, data, diagnostics, models


# ---------------------------------------------------------------------------
# Dihedral views and the flip metric
# ---------------------------------------------------------------------------


def test_dihedral_views_are_eight_distinct_symmetries():
    rng = np.random.default_rng(0)
    A = rng.normal(size=(3, 150, 150)).astype(np.float32)
    views = models.dihedral_views(A)
    assert len(views) == 8
    assert all(v.shape == A.shape for v in views)
    np.testing.assert_array_equal(views[0], A)  # view 0 is the identity
    flat = {v[0].tobytes() for v in views}
    assert len(flat) == 8, "the 8 symmetries must give 8 distinct images"


def test_dihedral_views_preserve_pixel_multiset():
    rng = np.random.default_rng(1)
    A = rng.normal(size=(2, 150, 150)).astype(np.float32)
    for v in models.dihedral_views(A):
        np.testing.assert_allclose(np.sort(v.ravel()), np.sort(A.ravel()))


def _probs(per_view_per_seed):
    """Build a (8, n_models, n) tensor from a list of per-view, per-seed probabilities."""
    return np.array(per_view_per_seed, dtype=float)


def test_flip_flags_detect_only_label_changes():
    # source 0: all views agree FR-II; source 1: one view crosses the boundary
    v = np.full((8, 2, 2), 0.9)
    v[:, :, 1] = 0.6
    v[3, :, 1] = 0.4
    flags = diagnostics.dihedral_flip_flags(v)
    assert flags.tolist() == [False, True]


def test_flip_flags_use_the_ensemble_mean_not_individual_seeds():
    """One dissenting seed must not count as a flip if the ensemble mean holds."""
    v = np.full((8, 5, 1), 0.8)
    v[2, 0, 0] = 0.1  # single seed dissents on one view; mean stays above 0.5
    assert diagnostics.dihedral_flip_flags(v).tolist() == [False]


def test_seed_disagreement_uses_identity_view_only():
    v = np.full((8, 5, 1), 0.8)
    v[0, 0, 0] = 0.2  # seed 0 disagrees on the identity view
    assert diagnostics.seed_disagreement_flags(v).tolist() == [True]
    v2 = np.full((8, 5, 1), 0.8)
    v2[5, 0, 0] = 0.2  # disagreement on a rotated view is not seed disagreement
    assert diagnostics.seed_disagreement_flags(v2).tolist() == [False]


def test_tta_mean_averages_views_and_seeds():
    v = np.zeros((8, 5, 1))
    v[:, :, 0] = np.arange(40).reshape(8, 5)
    assert models.tta_mean(v)[0] == pytest.approx(np.arange(40).mean())


def test_ambiguity_and_band():
    v = np.zeros((8, 1, 3))
    v[:, 0, :] = np.array([0.5, 0.99, 0.02])
    np.testing.assert_allclose(diagnostics.ambiguity(v), [0.0, 0.49, 0.48])
    assert diagnostics.in_uncertain_band(v).tolist() == [True, False, False]


# ---------------------------------------------------------------------------
# Uncertainty helpers
# ---------------------------------------------------------------------------


def test_wilson_ci_brackets_the_point_estimate():
    lo, hi = diagnostics.wilson_ci(92, 104)
    assert lo < 92 / 104 < hi
    # The n = 104 interval is far wider than the 1.3 pp seed spread.
    assert (hi - lo) / 2 > 0.04


def test_wilson_ci_edge_cases():
    assert diagnostics.wilson_ci(0, 10)[0] == pytest.approx(0.0, abs=1e-9)
    assert diagnostics.wilson_ci(10, 10)[1] == pytest.approx(1.0, abs=1e-9)


def test_bootstrap_ci_is_deterministic_and_brackets():
    x = np.random.default_rng(0).normal(size=200)
    a = diagnostics.bootstrap_ci(x, np.mean, n_boot=1000, seed=0)
    b = diagnostics.bootstrap_ci(x, np.mean, n_boot=1000, seed=0)
    assert a == b, "the same seed must give the same interval"
    assert a[0] < x.mean() < a[1]


def test_rate_with_ci_counts_correctly():
    flags = np.array([True] * 30 + [False] * 70)
    out = diagnostics.rate_with_ci(flags)
    assert out["n"] == 100 and out["k"] == 30
    assert out["rate"] == pytest.approx(0.30)
    assert out["ci_lo"] < 0.30 < out["ci_hi"]


def test_intervals_overlap():
    a = {"ci_lo": 0.1, "ci_hi": 0.2}
    b = {"ci_lo": 0.15, "ci_hi": 0.3}
    c = {"ci_lo": 0.25, "ci_hi": 0.4}
    assert diagnostics.intervals_overlap(a, b)
    assert not diagnostics.intervals_overlap(a, c)


# ---------------------------------------------------------------------------
# Cohort construction must match the published sample sizes
# ---------------------------------------------------------------------------


def test_mirabest_catalogue_parses_every_source():
    cat = data.mirabest_catalogue()
    assert len(cat) == 1256
    assert (cat.split == "train").sum() == 1099
    assert (cat.split == "test").sum() == 157
    assert cat.size_arcsec.gt(0).all()
    assert cat.cls.isin(config.MIRABEST_LABEL_NAMES).all()


def test_label_index_matches_class_code():
    """batches.meta's label_names must line up with the filename class codes."""
    cat = data.mirabest_catalogue()
    for _, r in cat.sample(50, random_state=0).iterrows():
        assert config.MIRABEST_LABEL_NAMES[r.label] == r.cls


def test_cohort_sizes_match_the_published_numbers():
    conf = data.cohort("confident")
    assert len(conf) == 833
    assert (conf.split == "train").sum() == 729
    assert (conf.split == "test").sum() == 104
    assert len(data.cohort("uncertain")) == 389
    assert len(data.cohort("hybrid")) == 34


def test_confident_true_labels_are_the_frii_codes():
    conf = data.cohort("confident")
    assert set(conf[conf.true_label == 1].cls) == {"200", "201"}
    assert set(conf[conf.true_label == 0].cls) == {"100", "102", "104"}


def test_paired_cutouts_exist_for_every_held_out_source():
    """Gate 1 depends on all 104 held-out paired cutouts being on disk."""
    test_conf = data.cohort("confident", splits=("test",))
    assert len(test_conf) == 104
    missing = [str(data.paired_cutout_path(r)) for _, r in test_conf.iterrows()
               if not data.paired_cutout_path(r).exists()]
    assert missing == [], f"{len(missing)} paired cutouts missing"


def test_legacy_paired_name_is_ambiguous_for_training_split():
    """The notebook's MB_<split>_<batch_index>.fits collides 7 ways on the training split.

    batch_index counts within a batch and every MiraBest batch holds 157 sources, so the
    729 confident training sources collapse onto 107 filenames. Regression guard for the
    mis-pairing that invalidated the notebook's n = 833 T2 result.
    """
    assert data.legacy_name_is_unambiguous("test")
    assert not data.legacy_name_is_unambiguous("train")

    conf = data.cohort("confident")
    train = conf[conf.split == "train"]
    legacy = {f"MB_{r.split}_{r.batch_index}.fits" for _, r in train.iterrows()}
    assert len(train) == 729
    assert len(legacy) == 107, "the collision this guards against has changed shape"

    test = conf[conf.split == "test"]
    legacy_test = {f"MB_{r.split}_{r.batch_index}.fits" for _, r in test.iterrows()}
    assert len(legacy_test) == len(test) == 104, "the test split must stay collision-free"


def test_canonical_paired_name_is_unique_for_every_source():
    conf = data.cohort("confident")
    paths = {str(data.canonical_paired_cutout_path(r)) for _, r in conf.iterrows()}
    assert len(paths) == len(conf) == 833


def test_training_paired_cutouts_are_not_silently_resolved():
    """A training source must not resolve onto a legacy file belonging to another galaxy."""
    conf = data.cohort("confident")
    train = conf[conf.split == "train"]
    resolved = [data.paired_cutout_path(r) for _, r in train.iterrows()]
    # No canonical training cutouts have been downloaded, so none should resolve.
    assert not any(p.exists() for p in resolved), (
        "a training source resolved to an existing paired cutout; verify it is that "
        "source's own download and not a batch_index collision"
    )


def test_mirabest_images_match_catalogue_order():
    rows = data.cohort("confident", splits=("test",)).iloc[:5]
    X = data.mirabest_images(rows)
    assert X.shape == (5, 150, 150)
    assert X.min() >= 0.0 and X.max() <= 1.0
