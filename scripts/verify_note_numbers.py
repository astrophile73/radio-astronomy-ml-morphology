"""Check that every headline number in the Research Note matches the recorded outputs.

The note, the Zenodo deposit and this repository have to agree. This script reads the
numbers out of the JSON files the analysis scripts wrote and compares them against what
paper/rnaas_note.tex claims, so a transcription error cannot survive into the submission.

Run:  python -u scripts/verify_note_numbers.py
Exit code 1 if any claim does not match.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r1 import config  # noqa: E402

RES = config.RESEARCH_DIR
NOTE = config.REPO_ROOT / "paper" / "rnaas_note.tex"


def load(name):
    p = RES / name
    return json.loads(p.read_text()) if p.exists() else None


def pc(x):
    """Fraction -> percentage, rounded the way the note writes it."""
    return round(100 * x, 1)


def main() -> None:
    note = NOTE.read_text(encoding="utf-8")
    g2, g3a, g3b = load("gate2_instability.json"), load("gate3_leg1a_leg2.json"), load("gate3_leg1b_scaling.json")
    g3c, g4, g4b = load("gate3_leg3_components.json"), load("gate4_h3_restriction.json"), load("gate4b_h3_pixel_size.json")
    kf, g1 = load("kfold_reference.json"), load("gate1_paired_pipeline.json")
    missing = [n for n, v in [("gate2", g2), ("gate3a", g3a), ("gate3b", g3b), ("gate3c", g3c),
                              ("gate4", g4), ("gate4b", g4b), ("kfold", kf), ("gate1", g1)] if v is None]
    if missing:
        print("MISSING outputs: %s - run the scripts first" % ", ".join(missing))
        sys.exit(1)

    s = g2["summaries"]
    checks = []

    def claim(label, value, source):
        """Assert the note contains `value` as written, and record where it came from."""
        txt = str(value)
        checks.append((label, txt, source, txt in note))

    # --- the core comparison
    claim("candidate flip rate", pc(s["candidates"]["flip"]["rate"]), "gate2_instability.json")
    claim("candidate flip CI low", pc(s["candidates"]["flip"]["ci_lo"]), "gate2_instability.json")
    claim("candidate flip CI high", pc(s["candidates"]["flip"]["ci_hi"]), "gate2_instability.json")
    claim("k-fold reference", pc(kf["reference"]["flip"]["rate"]), "kfold_reference.json")
    claim("k-fold CI low", pc(kf["reference"]["flip"]["ci_lo"]), "kfold_reference.json")
    claim("k-fold CI high", pc(kf["reference"]["flip"]["ci_hi"]), "kfold_reference.json")
    claim("k-fold held-out accuracy", pc(kf["reference"]["accuracy"]["rate"]), "kfold_reference.json")

    # --- the cohort ladder
    for key, lbl in [("mirabest_confident_train", "training"), ("mirabest_uncertain", "uncertain"),
                     ("mirabest_hybrid", "hybrid")]:
        claim("ladder: %s" % lbl, pc(s[key]["flip"]["rate"]), "gate2_instability.json")

    # --- seed disagreement
    claim("seed disagree, candidates", pc(s["candidates"]["seed_disagree"]["rate"]), "gate2_instability.json")
    claim("seed disagree, k-fold ref", pc(kf["reference"]["seed_disagree"]["rate"]), "kfold_reference.json")

    # --- pipeline fidelity (gate 1)
    claim("paired label agreement", pc(g1["held_out"]["agreement"]), "gate1_paired_pipeline.json")

    # --- H3 restrictions
    claim("size-restricted (catalogue)", pc(g4["subsets"]["size_restricted"]["flip"]["rate"]), "gate4_h3_restriction.json")
    claim("single-component", pc(g4["subsets"]["single_component_2.25arcmin"]["flip"]["rate"]), "gate4_h3_restriction.json")
    claim("size-restricted (pixel)", pc(g4b["subsets"]["pixel_size_restricted"]["flip"]["rate"]), "gate4b_h3_pixel_size.json")

    # --- component density
    claim("neighbour fraction 2.25'", pc(g3c["frac_with_neighbour_2.25arcmin"]["rate"]), "gate3_leg3_components.json")

    ok = [c for c in checks if c[3]]
    bad = [c for c in checks if not c[3]]

    print("Checking paper/rnaas_note.tex against research/*.json\n")
    print("%-30s %9s  %-34s %s" % ("claim", "value", "source", ""))
    print("-" * 86)
    for label, val, src, good in checks:
        print("%-30s %9s  %-34s %s" % (label, val, src, "ok" if good else "NOT IN NOTE"))
    print("\n%d of %d numbers found verbatim in the note." % (len(ok), len(checks)))

    if bad:
        print("\nThe following were not found as written. Either the note is out of date,")
        print("or it rounds differently, or the analysis has been re-run:")
        for label, val, src, _ in bad:
            print("  %-30s expected %s from %s" % (label, val, src))
        sys.exit(1)
    print("Every headline number in the note matches the recorded output.")


if __name__ == "__main__":
    main()
