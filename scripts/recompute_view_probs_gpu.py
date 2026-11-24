"""Recompute every cached view-probability tensor on one device, so that no comparison
in the project carries an uncontrolled device term.

Motivation: the KF-1 reference was computed on GPU and every other tensor on CPU, while
KF-1a clears its pre-registered threshold by 0.3 pp. Rather than measure a device delta and
keep a mixed set, all tensors are regenerated on the current device and the CPU set is kept
beside them so the delta is recorded rather than assumed.

The existing CPU tensors are moved to research/_view_probs_cpu/ (not deleted), every tensor
is regenerated into research/_view_probs/, and the two are compared cohort by cohort: the
flip rate under each, and the number of individual sources whose flip flag changed.

Run:  python -u scripts/recompute_view_probs_gpu.py
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics, models, preprocess  # noqa: E402

CACHE = config.RESEARCH_DIR / "_view_probs"
OLD = config.RESEARCH_DIR / "_view_probs_cpu"


def candidate_array(scale: str) -> np.ndarray:
    if scale == "max":
        return data.candidate_images()  # the stored, regression-tested array
    names = data.candidate_names()["FIRST"].tolist()
    X, kept = preprocess.preprocess_many(data.candidate_fits_paths(names),
                                         mode=config.CHOSEN_MODE, scale=scale)
    if kept != list(range(len(names))):
        raise RuntimeError(f"{len(names)-len(kept)} cutouts failed under scale={scale}")
    return X


def pipeline_rendered_array() -> np.ndarray:
    rows = data.cohort("confident", splits=("test",))
    paths = [data.paired_cutout_path(r) for _, r in rows.iterrows()]
    missing = [p for p in paths if not p.exists()]
    if missing:
        raise RuntimeError(f"{len(missing)} paired cutouts missing")
    X, kept = preprocess.preprocess_many(paths, mode=config.CHOSEN_MODE)
    if kept != list(range(len(paths))):
        raise RuntimeError("a held-out paired cutout failed to preprocess")
    return X


def build(name: str) -> np.ndarray:
    if name == "candidates":
        return candidate_array("max")
    if name.startswith("candidates_scale_"):
        return candidate_array(name.replace("candidates_scale_", ""))
    if name == "mirabest_test_pipeline_rendered":
        return pipeline_rendered_array()
    spec = {
        "mirabest_confident_test": ("confident", ("test",)),
        "mirabest_confident_train": ("confident", ("train",)),
        "mirabest_uncertain": ("uncertain", ("train", "test")),
        "mirabest_hybrid": ("hybrid", ("train", "test")),
    }[name]
    return data.mirabest_images(data.cohort(spec[0], splits=spec[1]))


def main() -> None:
    device = models.device()
    print(f"=== recomputing all view-probability tensors on {device} ===", flush=True)
    if device.type != "cuda":
        print("REFUSING: this script exists to put every tensor on the GPU. CUDA is not "
              "available, so running it would only re-create the CPU set.", flush=True)
        sys.exit(1)

    names = sorted(p.stem for p in CACHE.glob("*.npy"))
    if not names:
        raise RuntimeError(f"no tensors found in {CACHE}")
    print(f"tensors to regenerate: {', '.join(names)}\n", flush=True)

    OLD.mkdir(parents=True, exist_ok=True)
    for n in names:
        src = CACHE / f"{n}.npy"
        if not (OLD / f"{n}.npy").exists():
            shutil.copy2(src, OLD / f"{n}.npy")
    print(f"CPU tensors preserved in {OLD}\n", flush=True)

    ens = models.load_ensemble()
    report = {"device": str(device), "cohorts": {}}
    t_start = time.time()

    for n in names:
        X = build(n)
        t0 = time.time()
        vp_new = models.predict_views(X, ens)
        vp_old = np.load(OLD / f"{n}.npy")
        if vp_old.shape != vp_new.shape:
            raise RuntimeError(f"{n}: shape changed {vp_old.shape} -> {vp_new.shape}")
        np.save(CACHE / f"{n}.npy", vp_new)

        f_old = diagnostics.dihedral_flip_flags(vp_old)
        f_new = diagnostics.dihedral_flip_flags(vp_new)
        changed = int((f_old != f_new).sum())
        r_old = 100 * f_old.mean()
        r_new = 100 * f_new.mean()
        max_dp = float(np.abs(vp_new - vp_old).max())
        report["cohorts"][n] = {
            "n": int(len(X)), "flip_cpu_pc": r_old, "flip_gpu_pc": r_new,
            "delta_pp": r_new - r_old, "sources_whose_flag_changed": changed,
            "max_abs_prob_diff": max_dp,
        }
        print(f"  {n:34s} n={len(X):5d}  {time.time()-t0:5.0f}s  "
              f"flip CPU {r_old:5.2f}% -> GPU {r_new:5.2f}%  "
              f"delta {r_new-r_old:+5.2f} pp  flags changed {changed:3d}  "
              f"max|dP| {max_dp:.2e}", flush=True)

    print(f"\ntotal {time.time()-t_start:.0f}s", flush=True)

    worst = max(abs(c["delta_pp"]) for c in report["cohorts"].values())
    report["max_abs_delta_pp"] = worst
    print(f"\nlargest flip-rate shift across all cohorts: {worst:.2f} pp")
    print("KF-1a clears its pre-registered 10 pp threshold by 0.3 pp, so this is the "
          "measured size of the device term that margin was exposed to.")

    p = config.RESEARCH_DIR / "device_consistency.json"
    p.write_text(json.dumps(report, indent=2, default=float))
    print(f"\nWrote {p}")
    print("\nAll downstream scripts read research/_view_probs/, so re-run them now:")
    print("  gate2_instability.py, gate3_leg1a_leg2.py, gate3_leg1b_scaling.py,")
    print("  gate3_leg3_components.py, gate4_h3_restriction.py, gate4b_h3_pixel_size.py,")
    print("  make_figure.py")


if __name__ == "__main__":
    main()
