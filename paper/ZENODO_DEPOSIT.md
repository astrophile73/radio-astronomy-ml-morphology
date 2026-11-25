# Zenodo deposit — checklist and field content

Working notes for preparing the single Zenodo record. Not part of the deposit itself.

## Before uploading

- [ ] Delete the stray `~/.claude/settings.json` directory at the repo root
- [ ] Add your ORCID to `CITATION.cff` and `.zenodo.json`
- [ ] Reserve the DOI on Zenodo, then paste it into `CITATION.cff`, `README.md` and the
      draft's data-availability line **before** tagging
- [ ] Tag the repo `v1.0.0` and record the commit SHA in the Zenodo description
- [ ] Confirm `pytest` passes from a clean clone

## Files to include

```
r1/                     the analysis package
scripts/                one entry point per pre-registered test
tests/                  40 tests
research/               DECISIONS.md, RESULTS.md, STATE.md, all *.json,
                        figures/, candidate_component_flags.csv, env_freeze.txt
research/_kfold/        5-fold held-out reference (272 KB)
research/_view_probs/   cached prediction tensors (2.3 MB)
paper/                  draft and figure
third_party/README.md   why the MiraBest loader is absent
notebooks/legacy/       superseded notebooks, clearly marked
README.md  LICENSE  CITATION.cff  pyproject.toml  requirements.txt
*.pth                   six model checkpoints (268 MB)
```

Including `_kfold/` and `_view_probs/` is deliberate: together they let a reader reproduce
every reported number **without a GPU**, which is the difference between a reproducible
deposit and an aspirational one.

## Files deliberately excluded

| Excluded | Why | Where to get it |
|---|---|---|
| `MiraBest_F.py`, `MiraBest.py` | No licence could be established; redistribution not permitted | See `third_party/README.md` |
| FIRST FITS cutouts (~1.8 GB) | Regenerable | `r1.extract.download_cutouts()` |
| `first_14dec17.fits.gz` (69 MB) | Third-party | `sundog.stsci.edu/first/catalogs/` |
| `mirabest_data/` | Third-party | Jodrell Bank MiraBest page |
| `research/_view_probs_cpu/` | Superseded by the GPU set | Regenerable |

## Form fields

**Resource type:** Software

**Licence:** MIT. State the split in the description — code MIT, text/figures/result files
CC-BY-4.0. Do not select two licences; it leaves a user unable to tell which covers what.

**Publisher:** Zenodo

**Keywords and subjects** (one combined field; Zenodo supports only EuroSciVoc, MeSH and
GEMET as controlled vocabularies — no astronomy vocabulary, and UAT is not supported, so
most of these go in as custom keywords):

```
Fanaroff-Riley classification
radio galaxies
FIRST survey
MiraBest
domain shift
out-of-distribution detection
convolutional neural networks
galaxy morphology
radio astronomy
model reliability
deep learning
active galactic nuclei
VLA
reproducibility
pre-registration
```

Also search the field for `astronomy`, `astrophysics`, `machine learning` and take any
EuroSciVoc term the dropdown actually offers.

**Related works:**
- the GitHub repository — *is supplement to*
- the RNAAS DOI — *is supplement to*, once the note is published

**Software fields:**
- Repository URL: `https://github.com/astrophile73/radio-astronomy-ml-morphology`
- Programming language: Python
- Development status: Active

## Description (paste-ready)

> Code, pre-registered analysis record and results for a study of how a MiraBest-trained
> FR-I/FR-II classifier behaves when applied to a blind sample of FIRST catalogue
> components.
>
> A five-seed ResNet-18 ensemble was applied to 1996 extended FIRST components. Only 15.3
> per cent of the sample falls inside MiraBest's angular-size range. Predicted class changes
> under a rotation or mirror for 21.7 per cent (19.9-23.5) of candidates, against 11.4 per
> cent (9.4-13.6) for MiraBest sources held out under five-fold cross-validation.
> Restricting candidates to MiraBest's angular-size range, or to isolated components, does
> not recover stability, so selection cannot repair the transfer. Ensemble seed disagreement
> fails as a diagnostic once referenced against a properly powered baseline.
>
> research/DECISIONS.md records the pass/fail criterion fixed before each test ran,
> including criteria that failed and thresholds that were deliberately not moved.
> research/RESULTS.md gives every reported number with its uncertainty, sample size, data
> split and the script that produced it, including three results from an earlier version of
> this work that were withdrawn rather than deleted.
>
> This archive corresponds to tag v1.0.0 of
> https://github.com/astrophile73/radio-astronomy-ml-morphology
>
> Not included, and documented in the README: the FIRST cutouts and catalogue (obtainable
> through r1.extract and from STScI), and the MiraBest_F dataset and its loader (obtainable
> from the Jodrell Bank MiraBest release; no licence could be established for the loader, so
> it is not redistributed here).
>
> Licence: code MIT; text, figures and result files CC-BY-4.0.
