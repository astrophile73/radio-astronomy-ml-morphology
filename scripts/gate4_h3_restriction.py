"""Gate 4 / H3: does restricting to MiraBest-like sources recover stability?

Criterion pre-registered in research/DECISIONS.md (2026-11-23), three tiers: full recovery,
partial recovery, or none. Applied to subset 4 (size-restricted and single-component) and
reported for every subset.

No new inference: every subset indexes the cached Gate 2 tensor, so the per-source
predictions are identical to Gate 2's and only the membership changes.

Run:  python -u scripts/gate4_h3_restriction.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics  # noqa: E402

CACHE = config.RESEARCH_DIR / "_view_probs"
REFERENCE_UPPER = 0.135  # upper bound of the 7.7% [2.9, 13.5] pipeline-rendered reference


def main() -> None:
    print("=== Gate 4 / H3: size and single-component restriction ===", flush=True)

    cand = data.clean_candidates().reset_index(drop=True)
    names = data.candidate_names()["FIRST"].tolist()
    assert list(cand.FIRST.values) == names, "candidate CSV order does not match the npy order"

    flags_path = config.RESEARCH_DIR / "candidate_component_flags.csv"
    if not flags_path.exists():
        raise RuntimeError("run scripts/gate3_leg3_components.py first (component flags)")
    cf = pd.read_csv(flags_path)
    assert list(cf.FIRST.values) == names, "component flag order does not match"

    vp = np.load(CACHE / "candidates.npy")
    ref_vp = np.load(CACHE / "mirabest_test_pipeline_rendered.npy")

    # MiraBest confident size range, recomputed here rather than hard-coded.
    conf = data.cohort("confident")
    lo, hi = np.percentile(conf.size_arcsec.values, [10, 90])
    print(f"MiraBest confident size p10-p90: [{lo:.1f}, {hi:.1f}] arcsec", flush=True)

    size_ok = (cand.Maj.values >= lo) & (cand.Maj.values <= hi)
    single_225 = ~cf["has_neighbour_2p25arcmin"].values.astype(bool)
    single_1 = ~cf["has_neighbour_1arcmin"].values.astype(bool)

    subsets = {
        "unrestricted": np.ones(len(cand), dtype=bool),
        "size_restricted": size_ok,
        "single_component_2.25arcmin": single_225,
        "single_component_1arcmin": single_1,
        "both_size_and_single_2.25arcmin": size_ok & single_225,
    }

    unres = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(vp))
    ref = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(ref_vp))
    print(f"\nreference (pipeline-rendered held-out): {100*ref['rate']:.1f}% "
          f"[{100*ref['ci_lo']:.1f}, {100*ref['ci_hi']:.1f}] (n={ref['n']})")
    print(f"unrestricted candidates:                {100*unres['rate']:.1f}% "
          f"[{100*unres['ci_lo']:.1f}, {100*unres['ci_hi']:.1f}] (n={unres['n']})")

    print("\n" + "=" * 108)
    print(f"{'subset':34s} {'n':>5s}  {'flip rate':24s} {'seed disagree':24s} "
          f"{'median |P-0.5|':20s}")
    print("=" * 108)

    out = {"reference": ref, "unrestricted": unres,
           "mirabest_size_range_arcsec": [float(lo), float(hi)], "subsets": {}}

    for name, mask in subsets.items():
        n = int(mask.sum())
        if n == 0:
            print(f"{name:34s} {n:5d}  EMPTY")
            continue
        sub = vp[:, :, mask]
        flip = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(sub))
        seed = diagnostics.rate_with_ci(diagnostics.seed_disagreement_flags(sub))
        amb = diagnostics.median_with_ci(diagnostics.ambiguity(sub))
        band = diagnostics.rate_with_ci(diagnostics.in_uncertain_band(sub))

        below_ref_upper = flip["rate"] < REFERENCE_UPPER
        overlaps_ref = diagnostics.intervals_overlap(flip, ref)
        drop_pp = 100 * (unres["rate"] - flip["rate"])
        disjoint_unres = not diagnostics.intervals_overlap(flip, unres)

        if below_ref_upper and overlaps_ref:
            tier = "FULL RECOVERY"
        elif drop_pp >= 5.0 and disjoint_unres:
            tier = "PARTIAL RECOVERY"
        else:
            tier = "NO RECOVERY"

        out["subsets"][name] = {
            "n": n, "flip": flip, "seed_disagree": seed, "ambiguity": amb,
            "uncertain_band": band, "drop_pp_vs_unrestricted": drop_pp,
            "point_below_reference_upper": bool(below_ref_upper),
            "ci_overlaps_reference": bool(overlaps_ref),
            "ci_disjoint_from_unrestricted": bool(disjoint_unres),
            "tier": tier,
        }
        print(f"{name:34s} {n:5d}  "
              f"{100*flip['rate']:5.1f}% [{100*flip['ci_lo']:4.1f},{100*flip['ci_hi']:5.1f}]"
              f"{'':6s} "
              f"{100*seed['rate']:5.1f}% [{100*seed['ci_lo']:4.1f},{100*seed['ci_hi']:5.1f}]"
              f"{'':6s} "
              f"{amb['median']:.3f} [{amb['ci_lo']:.3f},{amb['ci_hi']:.3f}]")

    print("\n" + "=" * 108)
    print("PRE-REGISTERED CRITERION (verdict carried by 'both_size_and_single_2.25arcmin')")
    print("=" * 108)
    for name, r in out["subsets"].items():
        if name == "unrestricted":
            continue
        print(f"  {name:34s} n={r['n']:5d}  drop {r['drop_pp_vs_unrestricted']:+5.1f} pp | "
              f"point < 13.5%: {str(r['point_below_reference_upper']):5s} | "
              f"CI overlaps ref: {str(r['ci_overlaps_reference']):5s} | "
              f"CI disjoint from unrestricted: {str(r['ci_disjoint_from_unrestricted']):5s}"
              f"  -> {r['tier']}")

    decisive = out["subsets"].get("both_size_and_single_2.25arcmin")
    out["verdict"] = decisive["tier"] if decisive else "NOT EVALUABLE"
    print(f"\n>>> H3: {out['verdict']}")
    if decisive and decisive["n"] < 100:
        print(f"    NOTE: n = {decisive['n']} < 100, so the pre-registered power caveat applies:")
        print("    the interval is wide and the point-estimate leg carries the verdict.")
    print("    Reminder, as pre-registered: this is a selection, not an intervention, and")
    print("    centring was not tested - only single-component.")

    p = config.RESEARCH_DIR / "gate4_h3_restriction.json"
    p.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {p}")


if __name__ == "__main__":
    main()
