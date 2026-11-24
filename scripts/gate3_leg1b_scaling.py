"""Gate 3 leg 1b / G3-1b: is the flip rate an artefact of per-image-max normalisation?

Criterion pre-registered in research/DECISIONS.md (2026-11-23):
    The P1-3 conclusion is robust only if, under BOTH alternative scalings, the candidate
    flip rate still exceeds the primary reference by >= 10 pp with disjoint bootstrap 95%
    CIs. If either variant breaks that, the result is declared normalisation-dependent.

The primary reference is the pipeline-rendered held-out value selected by G3-1a.

The default preprocessing is NOT changed on the basis of this test. It is a sensitivity
analysis, not a tuning opportunity.

Run:  python -u scripts/gate3_leg1b_scaling.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as spstats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics, models, preprocess  # noqa: E402

CACHE = config.RESEARCH_DIR / "_view_probs"
SCALES = ["p99", "lcc_max"]


def fmt(d: dict) -> str:
    return f"{100*d['rate']:5.1f}% [{100*d['ci_lo']:5.1f}, {100*d['ci_hi']:5.1f}] ({d['k']}/{d['n']})"


def main() -> None:
    print("=== Gate 3 leg 1b / G3-1b: normalisation sensitivity ===", flush=True)
    names = data.candidate_names()["FIRST"].tolist()
    paths = data.candidate_fits_paths(names)

    # The reference selected by G3-1a.
    ref_file = CACHE / "mirabest_test_pipeline_rendered.npy"
    if not ref_file.exists():
        raise RuntimeError("run scripts/gate3_leg1a_leg2.py first; G3-1a selects the reference")
    ref = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(np.load(ref_file)))
    print(f"primary reference (pipeline-rendered held-out): {fmt(ref)}\n", flush=True)

    base_vp = np.load(CACHE / "candidates.npy")
    base = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(base_vp))
    print(f"published scaling 'max': {fmt(base)}", flush=True)

    ens = None
    out = {"reference_pipeline_rendered": ref, "scale_max": base, "variants": {}}

    for scale in SCALES:
        f = CACHE / f"candidates_scale_{scale}.npy"
        if f.exists() and np.load(f).shape == base_vp.shape:
            vp = np.load(f)
            print(f"\nscale={scale}: cached", flush=True)
        else:
            t0 = time.time()
            X, kept = preprocess.preprocess_many(paths, mode=config.CHOSEN_MODE, scale=scale)
            if kept != list(range(len(paths))):
                raise RuntimeError(f"{len(paths)-len(kept)} cutouts failed under {scale}")
            print(f"\nscale={scale}: preprocessed {len(X)} in {time.time()-t0:.0f}s",
                  flush=True)
            if ens is None:
                ens = models.load_ensemble()
            t0 = time.time()
            vp = models.predict_views(X, ens)
            np.save(f, vp)
            print(f"  inference {time.time()-t0:.0f}s -> {f.name}", flush=True)

        flip = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(vp))
        band = diagnostics.rate_with_ci(diagnostics.in_uncertain_band(vp))
        amb = diagnostics.median_with_ci(diagnostics.ambiguity(vp))

        gap = 100 * (flip["rate"] - ref["rate"])
        disjoint = not diagnostics.intervals_overlap(flip, ref)
        passed = gap >= 10.0 and disjoint

        # How much did the scaling move the scores at all? If it barely changes the
        # predictions, the test is uninformative rather than reassuring.
        p_base = models.tta_mean(base_vp)
        p_var = models.tta_mean(vp)
        rho = float(spstats.spearmanr(p_base, p_var).statistic)
        med_shift = float(np.median(np.abs(p_var - p_base)))

        out["variants"][scale] = {
            "flip": flip, "uncertain_band": band, "ambiguity": amb,
            "gap_pp_vs_reference": gap, "cis_disjoint": bool(disjoint),
            "verdict": "PASS" if passed else "FAIL",
            "spearman_vs_max": rho, "median_abs_dP_vs_max": med_shift,
        }
        print(f"  flip rate      : {fmt(flip)}")
        print(f"  band P in band : {fmt(band)}")
        print(f"  median |P-0.5| : {amb['median']:.3f} [{amb['ci_lo']:.3f}, {amb['ci_hi']:.3f}]")
        print(f"  vs 'max' scaling: Spearman {rho:.3f}, median |dP| {med_shift:.4f}")
        print(f"  criterion: gap >= 10 pp -> {gap >= 10} ({gap:+.1f} pp); "
              f"CIs disjoint -> {disjoint}  =>  {'PASS' if passed else 'FAIL'}")

    all_pass = all(v["verdict"] == "PASS" for v in out["variants"].values())
    out["verdict"] = "PASS" if all_pass else "FAIL"
    print(f"\n>>> G3-1b: {out['verdict']}")
    if all_pass:
        print("    The flip-rate result is not an artefact of per-image-max normalisation.")
    else:
        print("    The result is normalisation-dependent; report all three scalings.")

    p = config.RESEARCH_DIR / "gate3_leg1b_scaling.json"
    p.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {p}")


if __name__ == "__main__":
    main()
