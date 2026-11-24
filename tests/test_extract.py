"""Tests for the catalogue-side replacement of data_extraction.ipynb.

The notebook cannot run any more (its TAP host is dead), so these tests are what
establish that r1.extract reproduces the published sample from the STScI catalogue.
They need the 69 MB catalogue file and are skipped when it is absent.
"""

from __future__ import annotations

import numpy as np
import pytest

from r1 import data, extract

pytestmark = pytest.mark.skipif(
    not extract.CATALOGUE_FILE.exists(),
    reason="FIRST catalogue not downloaded; see r1.extract.download_catalogue()",
)


@pytest.fixture(scope="module")
def catalogue():
    return extract.load_catalogue()


@pytest.fixture(scope="module")
def published():
    return data.clean_candidates()


# ---------------------------------------------------------------------------
# IAU names: FIRST truncates, it does not round
# ---------------------------------------------------------------------------


def test_iau_name_reproduces_every_published_name(published):
    got = [extract.iau_name(r, d) for r, d in zip(published.RAJ2000, published.DEJ2000)]
    bad = [(a, b) for a, b in zip(got, published.FIRST) if a != b]
    assert bad == [], f"{len(bad)} names differ, first few: {bad[:5]}"


def test_iau_name_truncates_rather_than_rounds():
    # 16h06m03.89s would round to 03.9 and truncate to 03.8; FIRST uses 03.8.
    ra = (16 + 6 / 60 + 3.89 / 3600) * 15
    assert extract.iau_name(ra, 64.3389)[:11] == "J160603.8+6"


def test_iau_name_carries_at_sixty():
    """Truncation can leave a field at exactly 60, which must carry.

    Anchored on the real source that exposed this: Dec +32.05 is not exactly
    representable in binary, so the arcsecond field computes as 59.99999999998977.
    Truncating naively gives the nonsensical "+320260"; the published name is
    "+320300". A plain floor without the epsilon reintroduces the bug.
    """
    assert extract.iau_name(155.183004, 32.05) == "J102043.9+320300"
    # A value genuinely below 60 must not carry.
    assert extract.iau_name(10.0, 32 + 2 / 60 + 59.5 / 3600).endswith("+320259")


def test_iau_name_handles_negative_declination():
    n = extract.iau_name(10.0, -5.5)
    assert n.count("-") == 1 and "+" not in n


# ---------------------------------------------------------------------------
# Catalogue identity and sample reproduction
# ---------------------------------------------------------------------------


def test_catalogue_row_count_is_the_published_release(catalogue):
    assert len(catalogue) == extract.EXPECTED_ROWS == 946_432


def test_recno_aligns_with_the_published_candidates(catalogue, published):
    """The STScI file must be row-identical to the VizieR table the sample came from."""
    m = catalogue.merge(published[["recno", "RAJ2000", "DEJ2000"]], on="recno",
                        suffixes=("_cat", "_pub"))
    assert len(m) == len(published)
    sep = np.hypot((m.RAJ2000_cat - m.RAJ2000_pub)
                   * np.cos(np.radians(m.DEJ2000_pub)),
                   m.DEJ2000_cat - m.DEJ2000_pub) * 3600
    assert sep.max() < 0.05, f"max position offset {sep.max():.3f} arcsec"


def test_selection_reproduces_the_published_candidates(catalogue, published):
    """With VizieR rounding, every published candidate is reselected."""
    cand = extract.select_extended_candidates(extract.select_sample(catalogue),
                                              vizier_rounding=True)
    missing = set(published.recno) - set(cand.recno)
    assert missing == set(), f"{len(missing)} published candidates not reselected"


def test_full_precision_selection_loses_the_boundary_sources(catalogue, published):
    """Regression guard on the rounding finding, so it cannot be silently 'fixed'.

    Five published candidates sit at exactly SNR 7.000 on VizieR's rounded columns and
    below 7 on full precision. Selecting without rounding must therefore lose exactly
    those, and the difference must stay small enough not to matter scientifically.
    """
    cand = extract.select_extended_candidates(extract.select_sample(catalogue),
                                              vizier_rounding=False)
    missing = set(published.recno) - set(cand.recno)
    assert 0 < len(missing) <= 10, f"{len(missing)} missing; the rounding effect changed"
    assert len(missing) / len(published) < 0.01


def test_sample_selection_is_deterministic(catalogue):
    a = extract.select_sample(catalogue)
    b = extract.select_sample(catalogue)
    assert a.recno.tolist() == b.recno.tolist()
    assert len(a) == 10_000


def test_morphology_gate_thresholds_are_the_published_ones():
    assert extract.MIN_FLUX_RATIO == 1.25
    assert extract.MIN_MAJ_ARCSEC == 6.0
    assert extract.MIN_SNR == 7.0
