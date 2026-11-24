"""Gate 1 / P1-1: the paired pipeline test on held-out MiraBest sources only.

Criterion pre-registered in research/DECISIONS.md (2026-11-21):
    T2 passes only if the bootstrap 95% CI *lower bound* for label agreement is >= 95%
    AND the CI *upper bound* for median |dP| is < 0.05.

Why this test gates everything: every candidate number is a statement about images our own
code produced. If preprocess_cutout loses information that MiraBest's images retain, those
numbers describe the pipeline rather than the sky. Comparing both representations of the
same galaxies, on sources the ensemble never trained on, separates the two.

Run:  python scripts/gate1_paired_pipeline.py
"""

from __future__ import annotations

import json
import sys

import numpy as np
from scipy import stats as spstats

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from r1 import config, data, diagnostics, models, preprocess  # noqa: E402


def identity_ensemble_mean(view_probs: np.ndarray) -> np.ndarray:
    """Ensemble-mean P(FR-II) on the unrotated image - what T2 in the notebook used."""
    return view_probs[0].mean(axis=0)


def evaluate(rows, label: str) -> dict:
    paths = [data.paired_cutout_path(r) for _, r in rows.iterrows()]
    present = [p.exists() for p in paths]
    rows = rows[present].reset_index(drop=True)
    paths = [p for p, ok in zip(paths, present) if ok]

    X_pipeline, kept = preprocess.preprocess_many(paths, mode=config.CHOSEN_MODE)
    rows = rows.iloc[kept].reset_index(drop=True)
    X_native = data.mirabest_images(rows)

    ens = models.load_ensemble()
    P_native = identity_ensemble_mean(models.predict_views(X_native, ens))
    P_pipeline = identity_ensemble_mean(models.predict_views(X_pipeline, ens))

    y = rows.true_label.values
    lab_n = (P_native > 0.5).astype(int)
    lab_p = (P_pipeline > 0.5).astype(int)
    n = len(rows)

    agree = (lab_n == lab_p).astype(float)
    dP = np.abs(P_native - P_pipeline)

    res = {
        "label": label,
        "n": int(n),
        "agreement": float(agree.mean()),
        "agreement_ci": diagnostics.bootstrap_ci(agree, np.mean),
        "median_dP": float(np.median(dP)),
        "median_dP_ci": diagnostics.bootstrap_ci(dP, np.median),
        "spearman": float(spstats.spearmanr(P_native, P_pipeline).statistic),
        "spearman_ci": diagnostics.paired_bootstrap_ci(
            P_native, P_pipeline, lambda a, b: spstats.spearmanr(a, b).statistic
        ),
        "acc_native": float((lab_n == y).mean()),
        "acc_native_ci": diagnostics.bootstrap_ci((lab_n == y).astype(float), np.mean),
        "acc_native_wilson": diagnostics.wilson_ci(int((lab_n == y).sum()), n),
        "acc_pipeline": float((lab_p == y).mean()),
        "acc_pipeline_ci": diagnostics.bootstrap_ci((lab_p == y).astype(float), np.mean),
        "acc_pipeline_wilson": diagnostics.wilson_ci(int((lab_p == y).sum()), n),
        "frac_native_saturated": float(((P_native < 0.02) | (P_native > 0.98)).mean()),
    }
    res["pass_agreement"] = bool(res["agreement_ci"][0] >= 0.95)
    res["pass_median_dP"] = bool(res["median_dP_ci"][1] < 0.05)
    res["verdict"] = "PASS" if (res["pass_agreement"] and res["pass_median_dP"]) else "FAIL"
    return res


def show(r: dict) -> None:
    print(f"\n--- {r['label']} (n = {r['n']}) ---")
    print(f"  label agreement        : {100*r['agreement']:.1f}%  "
          f"CI [{100*r['agreement_ci'][0]:.1f}, {100*r['agreement_ci'][1]:.1f}]")
    print(f"  median |dP|            : {r['median_dP']:.4f}  "
          f"CI [{r['median_dP_ci'][0]:.4f}, {r['median_dP_ci'][1]:.4f}]")
    print(f"  Spearman rho           : {r['spearman']:.3f}  "
          f"CI [{r['spearman_ci'][0]:.3f}, {r['spearman_ci'][1]:.3f}]")
    print(f"  accuracy, native       : {100*r['acc_native']:.1f}%  "
          f"Wilson [{100*r['acc_native_wilson'][0]:.1f}, {100*r['acc_native_wilson'][1]:.1f}]")
    print(f"  accuracy, pipeline     : {100*r['acc_pipeline']:.1f}%  "
          f"Wilson [{100*r['acc_pipeline_wilson'][0]:.1f}, {100*r['acc_pipeline_wilson'][1]:.1f}]")
    print(f"  P_native saturated     : {100*r['frac_native_saturated']:.1f}% "
          f"(P < 0.02 or P > 0.98)")
    print(f"  criterion: agreement CI low >= 95%  -> {r['pass_agreement']}")
    print(f"             median |dP| CI high < 0.05 -> {r['pass_median_dP']}")
    print(f"  >>> {r['label']}: {r['verdict']}")


def main() -> None:
    print("=== Gate 1 / P1-1: paired pipeline test ===")
    print(f"device: {models.device()}  threads: {config.torch_threads()}")

    held_out = evaluate(data.cohort("confident", splits=("test",)), "HELD-OUT (primary)")
    show(held_out)

    # The training-side comparison cannot be computed from the files on disk. The
    # notebook named paired cutouts MB_<split>_<batch_index>.fits; batch_index counts
    # within a batch, so the 729 confident training sources collapse onto 107 filenames
    # and 8 download threads raced for each one. Those files cannot be attributed to a
    # source, so any training-side number would be comparing different galaxies. See
    # r1.data.paired_cutout_path and tests/test_diagnostics.py.
    train = data.cohort("confident", splits=("train",))
    resolvable = sum(1 for _, r in train.iterrows() if data.paired_cutout_path(r).exists())
    print(f"\n--- TRAINING (contaminated) ---")
    print(f"  DROPPED. {len(train)} training sources map onto "
          f"{len({f'MB_train_{r.batch_index}' for _, r in train.iterrows()})} legacy filenames; "
          f"{resolvable} resolve unambiguously.")
    print("  Re-running it needs 729 fresh downloads under the canonical names. The")
    print("  notebook's n = 833 T2 result is withdrawn: it was mis-paired, not merely")
    print("  contaminated. Only the 104 held-out sources above were ever paired correctly.")

    out = config.RESEARCH_DIR / "gate1_paired_pipeline.json"
    out.write_text(json.dumps(
        {"held_out": held_out,
         "training": {"status": "dropped",
                      "reason": "batch_index filename collision; see r1.data.paired_cutout_path",
                      "n_sources": int(len(train)),
                      "n_legacy_filenames": 107,
                      "n_resolvable": int(resolvable)}}, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
