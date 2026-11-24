"""The single RNAAS figure: the dihedral flip rate as a function of distance from training.

One panel carries H1, H2 and H3 together:
  - the cohort ladder, from memorised training data out to MiraBest's own hybrids, with the
    blind FIRST candidates landing beside MiraBest's *uncertain* class rather than its
    confident held-out set (H2, and the post-hoc equivalence observation);
  - the restricted candidate subsets overlaid, showing that selecting on size or multiplicity
    does not move them back toward the reference (H3, not supported);
  - the reference marked as a band so the reader sees what the comparison is against.

All values are read from the research/*.json outputs; nothing is recomputed or hard-coded,
so the figure cannot drift from RESULTS.md.

Run:  python -u scripts/make_figure.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config  # noqa: E402

RES = config.RESEARCH_DIR
OUT = RES / "figures"


def load(name: str) -> dict | None:
    p = RES / name
    if not p.exists():
        return None
    return json.loads(p.read_text())


def main() -> None:
    g2 = load("gate2_instability.json")
    g3a = load("gate3_leg1a_leg2.json")
    g4 = load("gate4_h3_restriction.json")
    g4b = load("gate4b_h3_pixel_size.json")
    kf = load("kfold_reference.json")
    if g2 is None or g3a is None:
        raise RuntimeError("run Gate 2 and Gate 3 first")

    s = g2["summaries"]

    def rate(d):
        return 100 * d["rate"], 100 * d["ci_lo"], 100 * d["ci_hi"], d["n"]

    # The primary reference is the k-fold one (n=833) when it exists; the n=104
    # matched-weights reference is plotted beside it so the model-set caveat is visible
    # rather than hidden. See DECISIONS.md 2026-11-23.
    ref_104 = rate(g3a["G3_1a"]["reference_pipeline_rendered"])
    ref_kf = rate(kf["reference"]["flip"]) if kf else None
    primary = ref_kf if ref_kf else ref_104
    ref_label = ("MiraBest held-out\n(5-fold reference)" if ref_kf
                 else "MiraBest held-out\n(reference)")

    # The ladder, ordered by distance from the training manifold.
    ladder = [
        ("MiraBest train\n(memorised)", rate(s["mirabest_confident_train"]["flip"]), "0.6"),
        (ref_label, primary, "tab:green"),
        ("blind FIRST\ncandidates", rate(s["candidates"]["flip"]), "tab:red"),
        ("MiraBest\nuncertain", rate(s["mirabest_uncertain"]["flip"]), "tab:orange"),
        ("MiraBest\nhybrid", rate(s["mirabest_hybrid"]["flip"]), "tab:purple"),
    ]

    # H3's restricted subsets, plotted against the candidate position.
    restricted = []
    if g4:
        for key, label in [
            ("size_restricted", "size-restricted\n(catalogue Maj)"),
            ("single_component_2.25arcmin", "single-component\n(2.25')"),
        ]:
            if key in g4["subsets"]:
                restricted.append((label, rate(g4["subsets"][key]["flip"])))
    if g4b and "pixel_size_restricted" in g4b["subsets"]:
        restricted.append(("size-restricted\n(pixel extent)",
                           rate(g4b["subsets"]["pixel_size_restricted"]["flip"])))

    fig, ax = plt.subplots(figsize=(7.2, 4.4))

    # Reference band.
    _, rlo, rhi, rn = primary
    ax.axhspan(rlo, rhi, color="tab:green", alpha=0.12, zorder=0)
    ax.axhline(primary[0], color="tab:green", lw=1, ls="--", zorder=1)

    # The n=104 matched-weights reference, offset beside the primary one.
    if ref_kf:
        v4, lo4, hi4, n4 = ref_104
        ax.errorbar(1 + 0.30, v4, yerr=[[v4 - lo4], [hi4 - v4]], fmt="D", ms=5, capsize=3,
                    lw=1.1, color="tab:green", alpha=0.45, markerfacecolor="white",
                    markeredgecolor="tab:green", zorder=3)
        ax.annotate(f"n={n4}, same weights\nas the candidates", (1 + 0.30, lo4),
                    textcoords="offset points", xytext=(6, -2), fontsize=6.3,
                    color="tab:green", alpha=0.95, ha="left", va="top")

    x = np.arange(len(ladder))
    # The candidate column carries the restricted squares to its right, so its label goes left.
    label_side = {2: -1}
    for i, (label, (v, lo, hi, n), colour) in enumerate(ladder):
        ax.errorbar(i, v, yerr=[[v - lo], [hi - v]], fmt="o", ms=8, capsize=4, lw=1.6,
                    color=colour, zorder=4)
        side = label_side.get(i, 1)
        dx = 13 * side
        ha = "left" if side > 0 else "right"
        ax.annotate(f"{v:.1f}%", (i, v), textcoords="offset points", xytext=(dx, 4),
                    fontsize=9, color=colour, fontweight="bold", ha=ha)
        ax.annotate(f"n={n}", (i, v), textcoords="offset points", xytext=(dx, -11),
                    fontsize=7.5, color="0.35", ha=ha)

    # Restricted subsets, offset to the right of the candidate column, each labelled.
    if restricted:
        xc = 2
        offs = np.linspace(0.20, 0.20 + 0.20 * (len(restricted) - 1), len(restricted))
        for (label, (v, lo, hi, n)), dx in zip(restricted, offs):
            ax.errorbar(xc + dx, v, yerr=[[v - lo], [hi - v]], fmt="s", ms=5.5, capsize=3,
                        lw=1.1, color="tab:red", alpha=0.5, zorder=3,
                        markerfacecolor="white", markeredgecolor="tab:red")
            ax.annotate(label.replace("\n", " "), (xc + dx, hi), textcoords="offset points",
                        xytext=(0, 7), fontsize=6.3, color="tab:red", alpha=0.95,
                        ha="center", va="bottom", rotation=90)

    ax.set_xticks(x)
    ax.set_xticklabels([l for l, _, _ in ladder], fontsize=8.5)
    ax.set_ylabel("sources changing predicted class under a\nrotation or mirror  (%)",
                  fontsize=9.5)
    ax.set_ylim(bottom=-3.2, top=max(hi for _, (_, _, hi, _), _ in ladder) * 1.22)
    ax.tick_params(axis="y", labelsize=8.5)
    ax.grid(axis="y", alpha=0.25, lw=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    ax.annotate(f"held-out reference  {ladder[1][1][0]:.1f}% [{rlo:.1f}, {rhi:.1f}]",
                xy=(0.013, rhi), xycoords=("axes fraction", "data"),
                xytext=(0, 5), textcoords="offset points",
                fontsize=7.5, color="tab:green")

    if restricted:
        handles = [
            plt.Line2D([], [], marker="o", ls="none", color="0.35", ms=7,
                       label="cohort (whole sample)"),
            plt.Line2D([], [], marker="s", ls="none", mfc="white", mec="tab:red", ms=6,
                       label="candidates restricted to MiraBest's size\n"
                             "range or to single components (H3: no recovery)"),
        ]
        ax.legend(handles=handles, loc="upper left", fontsize=7.4, frameon=False,
                  handletextpad=0.8, borderaxespad=0.2, labelspacing=0.9)

    ax.set_title("Dihedral prediction instability rises with distance from the training set",
                 fontsize=10.5, pad=10)
    fig.tight_layout()

    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        p = OUT / f"fig1_flip_rate_ladder.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print(f"wrote {p}")

    print("\nvalues plotted (all read from research/*.json):")
    for label, (v, lo, hi, n), _ in ladder:
        print(f"  {label.replace(chr(10), ' '):34s} {v:5.1f}% [{lo:4.1f}, {hi:5.1f}]  n={n}")
    for label, (v, lo, hi, n) in restricted:
        print(f"  {label.replace(chr(10), ' '):34s} {v:5.1f}% [{lo:4.1f}, {hi:5.1f}]  n={n}")
    if kf:
        k = kf["reference"]["flip"]
        c = s["candidates"]["flip"]
        print(f"\n  band = k-fold reference, n={k['n']} (primary). The n=104 matched-weights "
              "reference is the open diamond beside it.")
        print(f"  candidate gap vs the k-fold reference: "
              f"{100*(c['rate']-k['rate']):+.1f} pp, factor {c['rate']/k['rate']:.2f}")


if __name__ == "__main__":
    main()
