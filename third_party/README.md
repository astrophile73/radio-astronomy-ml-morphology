# Third-party code — intentionally not included

This project uses the **MiraBest_F** dataset. Its PyTorch loader (`MiraBest_F.py`) was
previously vendored into this repository and has been **removed**, because no licence
could be established for it.

## What was checked (2026-11-24)

- `github.com/as595/MiraBest` — does not exist (HTTP 404).
- `github.com/fmporter/MiraBest`, `fmporter/MiraBest-full`, `inigoval/mirabest` — all
  public, **none carries a LICENSE file**.
- The Jodrell Bank MiraBest project page refuses automated requests (HTTP 403), so its
  terms could not be read.
- The specific upstream of the `_F` variant was not located; the public Porter
  repositories contain `MiraBest.py` and `MiraBest_full.py`, not `MiraBest_F.py`.

With no licence stated anywhere in the chain, default copyright applies and redistribution
is not permitted. The file is therefore not distributed here or in the Zenodo deposit.

A further complication, unresolved: the loader carries the structure of torchvision's
CIFAR10 dataset class (BSD-3-Clause) and its own docstring says it is "inspired by" the
HTRU1 loader, whose repository is GPL-3.0. Which licence governs the derivative is unclear,
which is a second reason not to redistribute it.

## This does not affect reproducing the analysis

Nothing in `r1/` imports `MiraBest_F.py`. The pieces this project needs — the batch reader,
the label-code mapping and the cohort definitions — are reimplemented in `r1/data.py` and
`r1/config.py`, and `tests/test_diagnostics.py` verifies them against the published cohort
sizes (confident 833 = 729 train + 104 test, uncertain 389, hybrid 34).

Only the legacy notebooks in `notebooks/legacy/` import the original loader, and they are
superseded by `r1/` and `scripts/`.

## Getting the data

The dataset tarball is served from Jodrell Bank and was reachable on 2026-11-24:

    https://www.jb.man.ac.uk/research/MiraBest/MiraBest_F/MiraBest_F_batches.tar.gz

Download it to `mirabest_data/` and extract, or let `r1.data.batch_dir()` extract it from
the tarball automatically. Using the data is ordinary scientific use; only redistributing
the loader was in question.

## Citation

The labels derive from Miraghaei & Best (2017), MNRAS 466, 4346. The correct citation for
the MiraBest_F dataset release itself has **not been verified** and should be confirmed
with the dataset authors before use.
