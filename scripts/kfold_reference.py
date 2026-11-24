"""KF-1: a well-powered held-out reference by 5-fold cross-validation over MiraBest.

Criteria pre-registered in research/DECISIONS.md (2026-11-23): KF-1a restates P1-3 against
this reference and can withdraw P1-3's pass; KF-1b re-tests P1-4's 15% ceiling, which is NOT
moved; KF-1c is a sanity check that the k-fold recipe reproduces the published accuracy.

Why: every candidate-side claim is currently compared against 8 flips in 104 sources,
7.7% [2.9, 13.5]. This gives every one of the 833 confident sources a prediction from models
that never saw it, raising the reference n from 104 to 833.

The candidate predictions are deliberately NOT recomputed here; candidates keep being scored
by the published ensemble. See the pre-registration for why, and for the caveat that entails.

Run (GPU strongly preferred; 25 trainings):
    python -u scripts/kfold_reference.py
    python -u scripts/kfold_reference.py --folds 5 --seeds 5 --epochs 25
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics, models  # noqa: E402

OUT_DIR = config.RESEARCH_DIR / "_kfold"
CACHE = config.RESEARCH_DIR / "_view_probs"


class Dihedral:
    """The 8 symmetries of the square, applied to a [1, 150, 150] tensor.

    Equivalent to the PIL-based RandomDihedral in main.ipynb cell 24, implemented on tensors
    so the fold training does not depend on PIL round-tripping.
    """

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        k = random.randint(0, 3)
        if k:
            x = torch.rot90(x, k, dims=(1, 2))
        if random.random() < 0.5:
            x = torch.flip(x, dims=(2,))
        return x


def stratified_folds(labels: np.ndarray, n_folds: int, seed: int) -> np.ndarray:
    """Fold index per source, stratified on the label. Deterministic given seed."""
    rng = np.random.default_rng(seed)
    fold = np.empty(len(labels), dtype=int)
    for cls in np.unique(labels):
        idx = np.nonzero(labels == cls)[0]
        rng.shuffle(idx)
        fold[idx] = np.arange(len(idx)) % n_folds
    return fold


def train_one(X: np.ndarray, y: np.ndarray, seed: int, epochs: int, batch: int,
              device: torch.device) -> nn.Module:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    aug = Dihedral()
    ds = TensorDataset(torch.tensor(X, dtype=torch.float32).unsqueeze(1),
                       torch.tensor(y, dtype=torch.long))
    g = torch.Generator()
    g.manual_seed(seed)
    dl = DataLoader(ds, batch_size=batch, shuffle=True, generator=g)

    m = models.build_model().to(device)
    opt = optim.Adam(m.parameters(), lr=1e-4, weight_decay=1e-4)
    crit = nn.CrossEntropyLoss()
    for _ in range(epochs):
        m.train()
        for xb, yb in dl:
            xb = torch.stack([aug(x) for x in xb]).to(device)
            yb = yb.to(device)
            opt.zero_grad()
            crit(m(xb), yb).backward()
            opt.step()
    return m.eval()  # final epoch, no selection: see the pre-registration


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--retrain", action="store_true",
                    help="ignore a cached k-fold tensor and train the 25 models again")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = models.device()
    print(f"=== KF-1: {args.folds}-fold x {args.seeds}-seed reference ===", flush=True)
    print(f"device: {device}", flush=True)
    if device.type != "cuda":
        print("WARNING: running on CPU. 25 trainings will take hours. Install the CUDA "
              "wheel first (see research/STATE.md).", flush=True)

    rows = data.cohort("confident")
    X = data.mirabest_images(rows)
    y = rows.true_label.values.astype(int)
    print(f"{len(rows)} confident sources, class balance "
          f"FR-I {int((y == 0).sum())} / FR-II {int((y == 1).sum())}", flush=True)

    fold = stratified_folds(y, args.folds, config.SEED)
    np.save(OUT_DIR / "fold_assignment.npy", fold)
    for f in range(args.folds):
        m = fold == f
        print(f"  fold {f}: n={m.sum():3d}  FR-II fraction {y[m].mean():.3f}", flush=True)

    # Held-out view probabilities for every source, filled fold by fold.
    vp_all = np.zeros((8, args.seeds, len(rows)))

    # Reuse a completed run when only the downstream comparison needs refreshing (for
    # example after the candidate tensors were moved to another device). Retraining 25
    # models to recompute a comparison would change the reference for no reason.
    cached = OUT_DIR / "kfold_view_probs.npy"
    if cached.exists() and np.load(cached).shape == vp_all.shape:
        vp_all = np.load(cached)
        print(f"\nreusing {cached.name} ({vp_all.shape}); pass --retrain to force training",
              flush=True)
        if args.retrain:
            vp_all = np.zeros((8, args.seeds, len(rows)))
        else:
            return finish(vp_all, y, args, device)

    t_start = time.time()
    for f in range(args.folds):
        te = fold == f
        tr = ~te
        print(f"\n--- fold {f}: train {tr.sum()}, held out {te.sum()} ---", flush=True)
        fold_models = []
        for s in range(args.seeds):
            t0 = time.time()
            m = train_one(X[tr], y[tr], seed=1000 * f + s, epochs=args.epochs,
                          batch=args.batch, device=device)
            fold_models.append(m)
            print(f"    seed {s}: trained in {time.time()-t0:.0f}s", flush=True)
        vp_all[:, :, te] = models.predict_views(X[te], fold_models)
        acc = ((vp_all[:, :, te].mean(axis=(0, 1)) > 0.5).astype(int) == y[te]).mean()
        print(f"    fold held-out accuracy (TTA mean): {100*acc:.1f}%", flush=True)
        del fold_models
        if device.type == "cuda":
            torch.cuda.empty_cache()

    np.save(OUT_DIR / "kfold_view_probs.npy", vp_all)
    print(f"\ntotal training time {time.time()-t_start:.0f}s", flush=True)
    finish(vp_all, y, args, device)


def finish(vp_all: np.ndarray, y: np.ndarray, args, device) -> None:
    """Reporting half: the reference, and the pre-registered criteria against it.

    Split out so the comparison can be refreshed without retraining when only the
    candidate tensors have changed (e.g. after moving them to another device).
    """
    # ---- the reference ----
    flip = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(vp_all))
    seed_d = diagnostics.rate_with_ci(diagnostics.seed_disagreement_flags(vp_all))
    band = diagnostics.rate_with_ci(diagnostics.in_uncertain_band(vp_all))
    amb = diagnostics.median_with_ci(diagnostics.ambiguity(vp_all))
    pred = (models.tta_mean(vp_all) > 0.5).astype(int)
    k_correct = int((pred == y).sum())
    acc_ci = diagnostics.wilson_ci(k_correct, len(y))

    # ---- the comparisons ----
    cand_vp = np.load(CACHE / "candidates.npy")
    cand_flip = diagnostics.rate_with_ci(diagnostics.dihedral_flip_flags(cand_vp))
    cand_seed = diagnostics.rate_with_ci(diagnostics.seed_disagreement_flags(cand_vp))
    old_ref = diagnostics.rate_with_ci(
        diagnostics.dihedral_flip_flags(np.load(CACHE / "mirabest_test_pipeline_rendered.npy")))

    def check(name, cand, ref, ceiling=False):
        gap = 100 * (cand["rate"] - ref["rate"])
        disjoint = not diagnostics.intervals_overlap(cand, ref)
        ok = gap >= 10.0 and disjoint and (not ceiling or ref["rate"] < 0.15)
        print(f"  {name:28s} candidate {100*cand['rate']:5.1f}%  reference "
              f"{100*ref['rate']:5.1f}% [{100*ref['ci_lo']:4.1f},{100*ref['ci_hi']:5.1f}]  "
              f"gap {gap:+5.1f} pp  disjoint {str(disjoint):5s}"
              + (f"  ref<15% {str(ref['rate'] < 0.15):5s}" if ceiling else "")
              + f"  -> {'PASS' if ok else 'FAIL'}")
        return {"gap_pp": gap, "cis_disjoint": bool(disjoint),
                "verdict": "PASS" if ok else "FAIL"}

    print("\n" + "=" * 96)
    print(f"K-FOLD REFERENCE (n = {len(y)} held-out predictions)")
    print("=" * 96)
    print(f"  dihedral flip rate : {100*flip['rate']:5.1f}% "
          f"[{100*flip['ci_lo']:4.1f}, {100*flip['ci_hi']:5.1f}]  ({flip['k']}/{flip['n']})")
    print(f"  seed disagreement  : {100*seed_d['rate']:5.1f}% "
          f"[{100*seed_d['ci_lo']:4.1f}, {100*seed_d['ci_hi']:5.1f}]")
    print(f"  P in (0.05, 0.95)  : {100*band['rate']:5.1f}% "
          f"[{100*band['ci_lo']:4.1f}, {100*band['ci_hi']:5.1f}]")
    print(f"  median |P-0.5|     : {amb['median']:.3f} [{amb['ci_lo']:.3f}, {amb['ci_hi']:.3f}]")
    print(f"  held-out accuracy  : {100*k_correct/len(y):5.1f}% Wilson "
          f"[{100*acc_ci[0]:.1f}, {100*acc_ci[1]:.1f}]")
    print(f"\n  for comparison, the n=104 pipeline-rendered reference was "
          f"{100*old_ref['rate']:.1f}% [{100*old_ref['ci_lo']:.1f}, {100*old_ref['ci_hi']:.1f}] "
          f"- CI width {100*(old_ref['ci_hi']-old_ref['ci_lo']):.1f} pp vs "
          f"{100*(flip['ci_hi']-flip['ci_lo']):.1f} pp now")

    print("\n" + "=" * 96)
    print("PRE-REGISTERED CRITERIA")
    print("=" * 96)
    kf1a = check("KF-1a (P1-3 restated)", cand_flip, flip)
    kf1b = check("KF-1b (P1-4 re-test)", cand_seed, seed_d, ceiling=True)
    acc_ok = acc_ci[0] <= 0.887 <= acc_ci[1] or (0.809 <= k_correct / len(y) <= 0.933)
    print(f"  {'KF-1c (recipe sanity)':28s} k-fold accuracy "
          f"{100*k_correct/len(y):.1f}% vs published 88.7% [80.9, 93.3]  -> "
          f"{'PASS' if acc_ok else 'FAIL'}")
    if not acc_ok:
        print("      The k-fold training did not reproduce the published recipe; nothing")
        print("      from this run is used until that is explained.")
    if kf1a["verdict"] == "FAIL":
        print("\n  NOTE: P1-3's pass is WITHDRAWN - it depended on an underpowered reference.")

    out = {"n_reference": int(len(y)), "folds": args.folds, "seeds": args.seeds,
           "epochs": args.epochs, "device": str(device),
           "reference": {"flip": flip, "seed_disagree": seed_d, "uncertain_band": band,
                         "ambiguity": amb,
                         "accuracy": {"k": k_correct, "n": int(len(y)),
                                      "rate": k_correct / len(y), "wilson": list(acc_ci)}},
           "old_reference_n104": old_ref,
           "candidates": {"flip": cand_flip, "seed_disagree": cand_seed},
           "criteria": {"KF_1a": kf1a, "KF_1b": kf1b,
                        "KF_1c": {"verdict": "PASS" if acc_ok else "FAIL"}}}
    p = config.RESEARCH_DIR / "kfold_reference.json"
    p.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {p}")
    print("Reminder: candidates are still scored by the published ensemble, so this compares")
    print("a model set with a matched-recipe model set, not identical weights.")


if __name__ == "__main__":
    main()
