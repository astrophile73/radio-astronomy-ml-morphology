# radio-astronomy-ml-morphology

FR-I/FR-II radio galaxy classification pipeline (FIRST survey + MiraBest, ResNet-18 ensemble) with built-in domain-shift and reproducibility validation.

## What this is

This project builds and rigorously validates a machine-learning pipeline for classifying Fanaroff-Riley (FR-I vs FR-II) radio galaxy morphology. It extracts ~10,000 3-arcmin cutouts from the FIRST survey (VizieR catalogue VIII/92/first14) via NASA SkyView, trains a ResNet-18 ensemble on the labelled MiraBest_F dataset, and applies three explicit validation tests before trusting any result:

1. **T1 -- input-domain match**: does the FITS preprocessing actually match the pixel statistics the model was trained on?
2. **T2 -- paired pipeline validation**: does the whole extraction-to-inference chain reproduce known labels, end to end?
3. **T3 -- bridge stability**: does an uncertainty-based "transition-bridge" candidate list survive re-training with different seeds and basic image symmetries (rotation/mirror)?

Candidates are also cross-matched against SDSS to explore whether morphological ambiguity correlates with galaxy environment.

**Honest result:** T1 and T2 pass; T3 currently does not -- the specific set of "ambiguous" galaxies is not stable across model seeds, even though the model's uncertainty score does correctly track MiraBest's own known-hybrid sources in isolation. This is documented directly in `main.ipynb` rather than hidden.

## Contents

- `data_extraction.ipynb` -- queries the FIRST catalogue (VizieR TAP) and downloads FITS cutouts via SkyView.
- `main.ipynb` -- quality gating, preprocessing, MiraBest-based training (single model + 5-seed ensemble), the three validation tests, four diagnostic plots, and the SDSS environment analysis.
- `MiraBest_F.py` -- the MiraBest_F PyTorch `Dataset` loader (third-party; confirm its license before further redistribution).
- `best_mirabest_resnet18.pth`, `ensemble_seed0.pth` .. `ensemble_seed4.pth` -- trained model checkpoints, provided so the later cells can be re-run without retraining (roughly 10-15 minutes on a single GPU otherwise).

## Setup

```
pip install astropy pyvo numpy pandas scipy torch torchvision requests matplotlib pillow
```

Run `data_extraction.ipynb` first to populate `FIRST_FITS_CUTOUTS/` (not tracked in this repo -- see `.gitignore`), then `main.ipynb`. The MiraBest_F dataset downloads itself automatically on first use.

## Status

Research/methods notebook, not a packaged library. See the markdown cells in `main.ipynb` for the full validation methodology and results.
