"""Gate 4b / H3 follow-up: restrict on pixel-measured structure instead of catalogue Maj.

Criterion pre-registered in research/DECISIONS.md (2026-11-23), with the explicit guard that
this is the ONLY additional size definition to be tried. Same three tiers as H3.

Motivation, documented on 2026-11-21 before any of this ran: `Maj` is a deconvolved
single-component Gaussian FWHM and MiraBest's `size_arcsec` is the largest angular size of
the labelled source, so the P1-5 pre-registration already required a proxy measured
identically on both sides. H1 found those pixel proxies separate the samples far more cleanly
than `Maj` does, and a large `Maj` can mean a poorly constrained fit to a faint blended source
rather than genuine resolved structure.

No new inference: subsets index the cached Gate 2 tensor.

Run:  python -u scripts/gate4b_h3_pixel_size.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics, preprocess  # noqa: E402

CACHE = config.RESEARCH_DIR / "_view_probs"
REFERENCE_UPPER = 0.135  # upper bound of the 7.7% [2.9, 13.5] pipeline-rendered reference
STATS_CACHE = config.RESEARCH_DIR / "_structure_stats.npz"


def structure(name: str, A: np.ndarray) -> dict[str, np.ndarray]:
    if STATS_CACHE.exists():
        z = np.load(STATS_CACHE)
        if f"{name}__largest_component_extent_px" in z:
            return {k.split("__", 1)[1]: z[k] for k in z.files if k.startswith(f"{name}__")}
    s = preprocess.structure_stats(A)
    existing = {}
    if STATS_CACHE.exists():
        z = np.load(STATS_CACHE)
        existing = {k: z[k] for k in z.files}
    existing.update({f"{name}__{k}": v for k, v in s.items()})
    np.savez(STATS_CACHE, **existing)
    return s


def tier_for(flip: dict, unres: dict, ref: dict) -> tuple[str, dict]:
    below = flip["rate"] < REFERENCE_UPPER
    overlaps_ref = diagnostics.intervals_overlap(flip, ref)
    drop_pp = 100 * (unres["rate"] - flip["rate"])
    disjoint_unres = not diagnostics.intervals_overlap(flip, unres)
    if below and overlaps_ref:
        t = "FULL RECOVERY"
    elif drop_pp >= 5.0 and disjoint_unres:
        t = "PARTIAL RECOVERY"
    else:
        t = "NO RECOVERY"
    return t, {"drop_pp_vs_unrestricted": drop_pp,
               "point_below_reference_upper": bool(below),
               "ci_overlaps_reference": bool(overlaps_ref),
               "ci_disjoint_from_unrestricted": bool(disjoint_unres)}


def main() -> None:
    print("=== Gate 4b / H3 follow-up: pixel-measured structure restriction ===", flush=True)

    Xc = data.candidate_images()
    test_rows = data.cohort("confident", splits=("test",))
    Xt = data.mirabest_images(test_rows)
    print(f"measuring structure on {len(Xc)} candidates and {len(Xt)} held-out MiraBest "
          f"images (identical preprocessing convention)", flush=True)

    sc = structure("candidates", Xc)
    st = structure("mirabest_confident_test", Xt)

    ext_c = sc["largest_component_extent_px"]
    ext_t = st["largest_component_extent_px"]
    lo, hi = np.percentile(ext_t, [10, 90])
    px = config.FIRST_PIXEL_SCALE_ARCSEC
    print(f"\nMiraBest held-out largest-component extent: median {np.median(ext_t):.0f} px "
          f"({np.median(ext_t)*px:.1f}\"), p10-p90 [{lo:.0f}, {hi:.0f}] px "
          f"([{lo*px:.1f}, {hi*px:.1f}]\")")
    print(f"candidates:                                 median {np.median(ext_c):.0f} px "
          f"({np.median(ext_c)*px:.1f}\")")

    pixel_ok = (ext_c >= lo) & (ext_c <= hi)
    r_in = diagnostics.rate_with_ci(pixel_ok)
    print(f"\ncandidates inside that extent range: {100*r_in['rate']:.1f}% "
          f"[{100*r_in['ci_lo']:.1f}, {100*r_in['ci_hi']:.1f}]  ({r_in['k']}/{r_in['n']})")

    cf = pd.read_csv(config.RESEARCH_DIR / "candidate_component_flags.csv")
    names = data.candidate_names()["FIRST"].tolist()
    assert list(cf.FIRST.values) == names, "component flag order does not match"
    single_225 = ~cf["has_neighbour_2p25arcmin"].values.astype(bool)

    vp = np.load(CACHE / "candidates.npy")
    ref = diagnostics.rate_with_ci(
        diagnostics.dihedral_flip_flags(np.load(CACHE / "mirabest_test_pipeline_rendered.npy")))
    unres = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(vp))
    print(f"\nreference (pipeline-rendered held-out): {100*ref['rate']:.1f}% "
          f"[{100*ref['ci_lo']:.1f}, {100*ref['ci_hi']:.1f}] (n={ref['n']})")
    print(f"unrestricted candidates:                {100*unres['rate']:.1f}% "
          f"[{100*unres['ci_lo']:.1f}, {100*unres['ci_hi']:.1f}] (n={unres['n']})")

    subsets = {
        "pixel_size_restricted": pixel_ok,
        "pixel_size_and_single_component": pixel_ok & single_225,
    }

    out = {"reference": ref, "unrestricted": unres,
           "mirabest_extent_p10_p90_px": [float(lo), float(hi)],
           "mirabest_extent_p10_p90_arcsec": [float(lo * px), float(hi * px)],
           "frac_candidates_inside": r_in, "subsets": {}}

    print("\n" + "=" * 100)
    print(f"{'subset':34s} {'n':>5s}  {'flip rate':26s} {'median |P-0.5|':22s}")
    print("=" * 100)
    for name, mask in subsets.items():
        n = int(mask.sum())
        if n == 0:
            print(f"{name:34s} {n:5d}  EMPTY")
            continue
        sub = vp[:, :, mask]
        flip = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(sub))
        amb = diagnostics.median_with_ci(diagnostics.ambiguity(sub))
        seed = diagnostics.rate_with_ci(diagnostics.seed_disagreement_flags(sub))
        t, detail = tier_for(flip, unres, ref)
        out["subsets"][name] = {"n": n, "flip": flip, "ambiguity": amb,
                               "seed_disagree": seed, "tier": t, **detail}
        print(f"{name:34s} {n:5d}  "
              f"{100*flip['rate']:5.1f}% [{100*flip['ci_lo']:4.1f},{100*flip['ci_hi']:5.1f}]"
              f"{'':8s} {amb['median']:.3f} [{amb['ci_lo']:.3f},{amb['ci_hi']:.3f}]")

    print("\n" + "=" * 100)
    print("PRE-REGISTERED CRITERION (verdict carried by 'pixel_size_restricted')")
    print("=" * 100)
    for name, r in out["subsets"].items():
        print(f"  {name:34s} n={r['n']:5d}  drop {r['drop_pp_vs_unrestricted']:+5.1f} pp | "
              f"point < 13.5%: {str(r['point_below_reference_upper']):5s} | "
              f"CI overlaps ref: {str(r['ci_overlaps_reference']):5s} | "
              f"CI disjoint from unrestricted: {str(r['ci_disjoint_from_unrestricted']):5s}"
              f"  -> {r['tier']}")

    decisive = out["subsets"].get("pixel_size_restricted")
    out["verdict"] = decisive["tier"] if decisive else "NOT EVALUABLE"
    print(f"\n>>> H3 (pixel-size version): {out['verdict']}")
    print("    As pre-registered, this is the only additional size definition tried.")
    if out["verdict"] == "NO RECOVERY":
        print("    H3 is therefore closed as NOT SUPPORTED on both size definitions.")
    print("    Still a selection, not an intervention; centring remains untested.")

    p = config.RESEARCH_DIR / "gate4b_h3_pixel_size.json"
    p.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {p}")


if __name__ == "__main__":
    main()
