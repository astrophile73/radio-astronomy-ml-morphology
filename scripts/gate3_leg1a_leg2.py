"""Gate 3 legs 1a and 2: the pipeline-rendered reference, and leakage-radius sensitivity.

Criteria pre-registered in research/DECISIONS.md (2026-11-23 for G3-1a, 2026-11-21 for
G3-2 / P1-7).

G3-1a asks whether our own preprocessing inflates instability. Gate 2's 8.7% reference was
measured on MiraBest's own rendering of its held-out sources, so it confounds "our pipeline"
with "MiraBest's rendering". Re-measuring the flip rate on the *same 104 galaxies* as
rendered by preprocess_cutout from SkyView cutouts isolates the pipeline: same code, same
cutout service, same normalisation, only the sky differs from the candidates.

G3-2 re-gates the candidate sample at the 2.25' half-field instead of 30" and re-runs the
three headline diagnostics by indexing the cached Gate 2 tensor.

Run:  python -u scripts/gate3_leg1a_leg2.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics, models, preprocess  # noqa: E402

CACHE = config.RESEARCH_DIR / "_view_probs"


def fmt(d: dict) -> str:
    return f"{100*d['rate']:5.1f}% [{100*d['ci_lo']:5.1f}, {100*d['ci_hi']:5.1f}] ({d['k']}/{d['n']})"


def leg1a() -> dict:
    print("=== G3-1a: flip rate on the held-out sources as rendered by OUR pipeline ===",
          flush=True)
    rows = data.cohort("confident", splits=("test",))
    paths = [data.paired_cutout_path(r) for _, r in rows.iterrows()]
    missing = [p for p in paths if not p.exists()]
    if missing:
        raise RuntimeError(f"{len(missing)} paired cutouts missing; cannot run G3-1a")

    X_pipeline, kept = preprocess.preprocess_many(paths, mode=config.CHOSEN_MODE)
    assert kept == list(range(len(paths))), "a held-out cutout failed to preprocess"

    f = CACHE / "mirabest_test_pipeline_rendered.npy"
    if f.exists() and np.load(f).shape == (8, 5, len(X_pipeline)):
        vp_pipe = np.load(f)
        print(f"  cached: {vp_pipe.shape}", flush=True)
    else:
        ens = models.load_ensemble()
        vp_pipe = models.predict_views(X_pipeline, ens)
        np.save(f, vp_pipe)
        print(f"  inferred {len(X_pipeline)} images -> {f.name}", flush=True)

    vp_native = np.load(CACHE / "mirabest_confident_test.npy")
    vp_cand = np.load(CACHE / "candidates.npy")

    pipe = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(vp_pipe))
    native = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(vp_native))
    cand = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(vp_cand))

    print(f"\n  held-out, MiraBest's own rendering : {fmt(native)}")
    print(f"  held-out, OUR pipeline rendering   : {fmt(pipe)}")
    print(f"  blind candidates, OUR pipeline     : {fmt(cand)}")

    # Per-source paired comparison on the same 104 galaxies.
    fp = diagnostics.dihedral_flip_flags(vp_pipe)
    fn = diagnostics.dihedral_flip_flags(vp_native)
    both = int((fp & fn).sum())
    only_pipe = int((fp & ~fn).sum())
    only_native = int((~fp & fn).sum())
    neither = int((~fp & ~fn).sum())
    print(f"\n  paired on the same 104 galaxies: both flip {both}, "
          f"pipeline only {only_pipe}, MiraBest-rendering only {only_native}, "
          f"neither {neither}")

    gap = 100 * (cand["rate"] - pipe["rate"])
    disjoint = not diagnostics.intervals_overlap(cand, pipe)
    ref_ok = pipe["rate"] < 0.15
    verdict = "PASS" if (ref_ok and gap >= 10 and disjoint) else "FAIL"
    print(f"\n  criterion: pipeline-rendered reference < 15% -> {ref_ok} "
          f"({100*pipe['rate']:.1f}%)")
    print(f"             candidate gap >= 10 pp            -> {gap >= 10} ({gap:+.1f} pp)")
    print(f"             CIs disjoint                      -> {disjoint}")
    print(f"  >>> G3-1a: {verdict}")
    if verdict == "PASS":
        print("      The pipeline-rendered value replaces 8.7% as the primary P1-3 reference.")
    else:
        print("      Our preprocessing materially inflates instability; P1-3 must be")
        print("      restated against this reference and the contribution reported.")

    return {"reference_native": native, "reference_pipeline_rendered": pipe,
            "candidates": cand, "gap_pp": gap, "cis_disjoint": bool(disjoint),
            "reference_below_15pc": bool(ref_ok), "verdict": verdict,
            "paired": {"both": both, "pipeline_only": only_pipe,
                       "native_only": only_native, "neither": neither}}


def leg2() -> dict:
    print("\n=== G3-2 / P1-7: leakage-radius sensitivity, 30\" vs 2.25' ===", flush=True)
    cand = data.clean_candidates().reset_index(drop=True)
    mb = data.mirabest_catalogue()  # all 1256 sources, as the original gate used
    print(f"  {len(cand)} candidates vs {len(mb)} MiraBest positions", flush=True)

    cc = SkyCoord(cand.RAJ2000.values * u.deg, cand.DEJ2000.values * u.deg)
    mc = SkyCoord(mb.ra.values * u.deg, mb.dec.values * u.deg)
    _, sep, _ = cc.match_to_catalog_sky(mc)

    vp = np.load(CACHE / "candidates.npy")
    metrics = {
        "flip": diagnostics.dihedral_flip_flags(vp),
        "seed_disagree": diagnostics.seed_disagreement_flags(vp),
        "uncertain_band": diagnostics.in_uncertain_band(vp),
    }

    out = {"n_full": int(len(cand))}
    keep = sep.arcmin > 2.25
    out["n_removed_at_2p25arcmin"] = int((~keep).sum())
    out["n_kept"] = int(keep.sum())
    print(f"  the 2.25' gate removes a further {int((~keep).sum())} candidates, "
          f"leaving {int(keep.sum())}")
    print(f"  (the published 30\" gate had already removed 28 of 2044)\n")

    print(f"  {'metric':20s} {'30asec sample (published)':30s} {'2.25amin sample':30s} {'shift':>8s}")
    worst = 0.0
    for name, flags in metrics.items():
        full = diagnostics.rate_with_ci(flags)
        sub = diagnostics.rate_with_ci(flags[keep])
        shift = 100 * (sub["rate"] - full["rate"])
        worst = max(worst, abs(shift))
        out[name] = {"full": full, "gated_2p25": sub, "shift_pp": shift}
        print(f"  {name:20s} {fmt(full):30s} {fmt(sub):30s} {shift:+7.2f} pp")

    passed = worst < 5.0
    out["max_abs_shift_pp"] = worst
    out["verdict"] = "PASS" if passed else "FAIL"
    print(f"\n  criterion: every metric shifts by < 5 pp -> largest shift "
          f"{worst:.2f} pp -> {'PASS' if passed else 'FAIL'}")
    if not passed:
        print("      The 2.25' sample becomes primary and every Gate 2 number is restated.")
    return out


def main() -> None:
    res = {"G3_1a": leg1a(), "G3_2": leg2()}
    p = config.RESEARCH_DIR / "gate3_leg1a_leg2.json"
    p.write_text(json.dumps(res, indent=2, default=float))
    print(f"\nWrote {p}")


if __name__ == "__main__":
    main()
