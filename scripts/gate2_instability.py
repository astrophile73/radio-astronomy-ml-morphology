"""Gate 2 / P1-3, P1-4, H4: instability diagnostics with their missing controls.

Criteria pre-registered in research/DECISIONS.md (2026-11-21):

  P1-3 (dihedral flip rate) and P1-4 (seed disagreement) are usable label-free OOD scores
  only if (i) the candidate rate exceeds the MiraBest confident-test rate by >= 10 pp AND
  (ii) the two bootstrap 95% CIs do not overlap. If the MiraBest confident-test rate is
  itself above 15%, the metric is declared too noisy to serve as an OOD score regardless
  of the gap.

  H4 re-confirms that ensemble ambiguity |P - 0.5| ranks MiraBest's held-out
  hybrid/uncertain sources as more ambiguous than its confident ones, now with CIs.

One inference pass over all five cohorts serves all three, and the raw (8, n_models, n)
probability tensors are cached so that any later re-analysis costs nothing.

Run:  python -u scripts/gate2_instability.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as spstats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics, models  # noqa: E402

CACHE = config.REPO_ROOT / "research" / "_view_probs"
MIRABEST_COHORTS = [
    ("mirabest_confident_test", "confident", ("test",), False),
    ("mirabest_confident_train", "confident", ("train",), True),
    ("mirabest_uncertain", "uncertain", ("train", "test"), False),
    ("mirabest_hybrid", "hybrid", ("train", "test"), False),
]


def cohort_arrays() -> dict[str, np.ndarray]:
    """Images for every cohort. MiraBest cohorts use MiraBest's own images, which is the
    domain the ensemble was trained on; candidates use the stored preprocessed array."""
    out = {"candidates": data.candidate_images()}
    for name, coh, splits, _ in MIRABEST_COHORTS:
        out[name] = data.mirabest_images(data.cohort(coh, splits=splits))
    return out


def view_probs_for(name: str, X: np.ndarray, ens) -> np.ndarray:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{name}.npy"
    if f.exists():
        vp = np.load(f)
        if vp.shape == (8, len(ens), len(X)):
            print(f"  {name:28s} cached  {vp.shape}", flush=True)
            return vp
    t0 = time.time()
    vp = models.predict_views(X, ens)
    np.save(f, vp)
    print(f"  {name:28s} {len(X):5d} images in {time.time()-t0:6.1f}s -> {f.name}", flush=True)
    return vp


def fmt_rate(d: dict) -> str:
    return (f"{100*d['rate']:5.1f}%  CI [{100*d['ci_lo']:5.1f}, {100*d['ci_hi']:5.1f}]  "
            f"({d['k']:4d}/{d['n']:4d})")


def fmt_med(d: dict) -> str:
    return f"{d['median']:.3f}  CI [{d['ci_lo']:.3f}, {d['ci_hi']:.3f}]"


def check_criterion(metric: str, cand: dict, ref: dict) -> dict:
    gap_pp = 100 * (cand["rate"] - ref["rate"])
    overlap = diagnostics.intervals_overlap(cand, ref)
    ref_too_noisy = ref["rate"] > 0.15
    passed = (gap_pp >= 10.0) and (not overlap) and (not ref_too_noisy)
    return {
        "metric": metric,
        "candidate_rate": cand["rate"],
        "reference_rate": ref["rate"],
        "gap_pp": gap_pp,
        "cis_overlap": overlap,
        "reference_above_15pc": ref_too_noisy,
        "verdict": "PASS" if passed else "FAIL",
    }


def main() -> None:
    print("=== Gate 2 / P1-3, P1-4, H4: instability with controls ===", flush=True)
    print(f"device: {models.device()}  threads: {config.torch_threads()}", flush=True)

    ens = models.load_ensemble()
    arrays = cohort_arrays()
    print("\ninference:", flush=True)
    probs = {name: view_probs_for(name, X, ens) for name, X in arrays.items()}

    print("\nsummarising (bootstrap 10,000, seed 0)...", flush=True)
    summ = {name: diagnostics.cohort_summary(vp, name) for name, vp in probs.items()}

    contaminated = {n for n, _, _, c in MIRABEST_COHORTS if c}
    print("\n" + "=" * 100)
    print(f"{'cohort':28s} {'dihedral flip rate':34s} {'seed disagreement':34s}")
    print("=" * 100)
    for name in ["candidates", "mirabest_confident_test", "mirabest_uncertain",
                 "mirabest_hybrid", "mirabest_confident_train"]:
        s = summ[name]
        tag = "  [contaminated]" if name in contaminated else ""
        print(f"{name:28s} {fmt_rate(s['flip']):34s} {fmt_rate(s['seed_disagree']):34s}{tag}")

    print("\n" + "=" * 100)
    print(f"{'cohort':28s} {'median |P-0.5|':30s} {'frac P in (0.05,0.95)':34s}")
    print("=" * 100)
    for name in ["candidates", "mirabest_confident_test", "mirabest_uncertain",
                 "mirabest_hybrid", "mirabest_confident_train"]:
        s = summ[name]
        tag = "  [contaminated]" if name in contaminated else ""
        print(f"{name:28s} {fmt_med(s['ambiguity']):30s} {fmt_rate(s['uncertain_band']):34s}{tag}")

    ref = summ["mirabest_confident_test"]
    cand = summ["candidates"]
    checks = [
        check_criterion("dihedral_flip_rate (P1-3)", cand["flip"], ref["flip"]),
        check_criterion("seed_disagreement (P1-4)", cand["seed_disagree"], ref["seed_disagree"]),
        check_criterion("uncertain_band (exploratory)", cand["uncertain_band"], ref["uncertain_band"]),
    ]
    print("\n" + "=" * 100)
    print("PRE-REGISTERED CRITERIA (gap >= 10 pp, CIs disjoint, reference <= 15%)")
    print("=" * 100)
    for c in checks:
        print(f"  {c['metric']:32s} candidate {100*c['candidate_rate']:5.1f}%  vs reference "
              f"{100*c['reference_rate']:5.1f}%  gap {c['gap_pp']:+5.1f} pp  "
              f"CIs overlap: {str(c['cis_overlap']):5s}  ref>15%: {str(c['reference_above_15pc']):5s}"
              f"  -> {c['verdict']}")

    # --- H4: does ambiguity rank MiraBest's own hybrid/uncertain sources correctly? ---
    print("\n" + "=" * 100)
    print("H4: ambiguity ranking of MiraBest's held-out hybrid/uncertain sources")
    print("=" * 100)
    amb = {n: diagnostics.ambiguity(probs[n]) for n in probs}
    h4 = {}
    for name in ["mirabest_uncertain", "mirabest_hybrid"]:
        u = spstats.mannwhitneyu(amb[name], amb["mirabest_confident_test"], alternative="less")
        lower = float(np.median(amb[name])) < float(np.median(amb["mirabest_confident_test"]))
        h4[name] = {"median": float(np.median(amb[name])), "p_value": float(u.pvalue),
                    "more_ambiguous_than_confident_test": lower}
        print(f"  {name:24s} median |P-0.5| = {np.median(amb[name]):.3f} vs confident-test "
              f"{np.median(amb['mirabest_confident_test']):.3f}  "
              f"Mann-Whitney p = {u.pvalue:.3g}  -> "
              f"{'more ambiguous' if lower else 'NOT more ambiguous'}")
    print(f"  NOTE: mirabest_hybrid has n = {len(amb['mirabest_hybrid'])}; its interval is wide "
          "and must be shown wherever this is quoted.")

    out = config.RESEARCH_DIR / "gate2_instability.json"
    out.write_text(json.dumps(
        {"summaries": summ, "criteria": checks, "h4": h4,
         "cohort_sizes": {k: int(len(v)) for k, v in arrays.items()}}, indent=2, default=float))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
