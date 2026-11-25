# Scripts — what to run, in what order

Each script tests one question whose pass/fail criterion was written down **before** it ran
(see `research/DECISIONS.md`). Each writes a JSON into `research/`, so every number in
`research/RESULTS.md` traces back to the code that produced it.

The filenames use "gate" numbering from the project's working vocabulary. A gate is a
question that could have stopped the project if answered badly. The table below translates.

## Run order

| # | Script | Question it answers | Writes | Needs |
|---|---|---|---|---|
| 1 | `gate1_paired_pipeline.py` | Is our own image pipeline faithful, or does it distort what the model sees? | `gate1_paired_pipeline.json` | cached cutouts |
| 2 | `gate2_instability.py` | How unstable are predictions on each cohort? Produces the core result. | `gate2_instability.json` | ~25 min CPU, or minutes on GPU |
| 3a | `gate3_leg1a_leg2.py` | Does *our preprocessing* inflate the instability? Does the leakage cut matter? | `gate3_leg1a_leg2.json` | cached tensors |
| 3b | `gate3_leg1b_scaling.py` | Is the result an artefact of per-image-max normalisation? | `gate3_leg1b_scaling.json` | ~25 min CPU |
| 3c | `gate3_leg3_components.py` | How many candidates are blended with a neighbouring component? | `gate3_leg3_components.json`, `candidate_component_flags.csv` | 69 MB catalogue download |
| 4a | `gate4_h3_restriction.py` | Does restricting to MiraBest-like sizes restore stability? | `gate4_h3_restriction.json` | cached tensors |
| 4b | `gate4b_h3_pixel_size.py` | Same question, using pixel-measured size instead of the catalogue's. | `gate4b_h3_pixel_size.json` | cached tensors |
| 5 | `kfold_reference.py` | What is a properly powered baseline? Trains 25 models. | `kfold_reference.json`, `research/_kfold/` | **GPU strongly preferred** |
| 6 | `make_figure.py` | Builds the paper figure from the JSONs above. | `research/figures/` | — |

Utility, not part of the sequence:

| Script | Purpose |
|---|---|
| `recompute_view_probs_gpu.py` | Regenerates every cached prediction tensor on one device, so no comparison mixes CPU and GPU arithmetic. Run after switching hardware. |

## Which results come from which script

| If you want to check... | Read | Produced by |
|---|---|---|
| The headline instability numbers | `research/RESULTS.md`, "Gate 2" | script 2 |
| The well-powered reference (11.4%) | `research/RESULTS.md`, "Gate 5 / KF-1" | script 5 |
| Whether the result is a preprocessing artefact | `research/RESULTS.md`, "Gate 3" | scripts 3a, 3b |
| Why size restriction does not help | `research/RESULTS.md`, "Gate 4 / H3" | scripts 4a, 4b |
| The pre-registered criterion for any of these | `research/DECISIONS.md` | — |

## Notes

- Scripts 3a, 4a, 4b and 6 reuse cached prediction tensors and take seconds. Scripts 2, 3b
  and 5 do real inference or training.
- Script 5 reuses a saved tensor if present; pass `--retrain` to force the 25 trainings.
- Nothing here depends on the MiraBest loader; see `third_party/README.md`.
