# radio-astronomy-ml-morphology

Diagnosing domain shift when a MiraBest-trained CNN ensemble is applied to a blind sample of
FIRST catalogue components.

**This repository is the supporting material for** the archived Zenodo deposit [doi:10.5281/zenodo.24497097](https://doi.org/10.5281/zenodo.24497097).

Arriving from the note and want to check a number?
**[`paper/NOTE_TO_DATA.md`](paper/NOTE_TO_DATA.md)** maps every claim in it to the file that
produced it. `scripts/verify_note_numbers.py` checks the headline figures automatically and
fails if any has drifted.

## What this is

FR-I/FR-II classification on MiraBest has been done many times, and another accuracy number
would not be new. This repository asks a different question: when a ResNet-18 ensemble trained
on MiraBest — curated, extended, host-centred radio galaxies — is pointed at an unlabelled
sample of FIRST catalogue components, how much of its output is meaningful, and which cheap
label-free diagnostics detect the failure?

The sample is 1996 extended FIRST components drawn from the full 946 432-row catalogue, with
4.5 arcmin cutouts from NASA SkyView at the native 1.8 arcsec pixel scale (150 x 150 px, which
matches MiraBest's own image format).

## Where to find things

| I want to... | Go to |
|---|---|
| **See the results** | [`research/RESULTS.md`](research/RESULTS.md) — every number with its uncertainty, sample size, data split, and the script that produced it |
| **See what was decided, and when** | [`research/DECISIONS.md`](research/DECISIONS.md) — the pass/fail criterion fixed *before* each test ran, including the ones that failed |
| **Run the analysis** | [`scripts/README.md`](scripts/README.md) — run order, what each script answers, what it writes |
| **Read the code** | [`r1/`](r1/) — `config`, `data`, `preprocess`, `models`, `diagnostics`, `extract` |
| **Check the code is right** | [`tests/`](tests/) — 40 tests, including a regression proving the preprocessing reproduces the stored arrays |
| **See the figure** | [`research/figures/`](research/figures/) — regenerates from the JSON outputs, so it cannot drift from the numbers |
| **Check a number from the note** | [`paper/NOTE_TO_DATA.md`](paper/NOTE_TO_DATA.md) — every claim mapped to its source file |
| **Read the paper** | [`paper/`](paper/) — the note, its LaTeX source, and the Zenodo checklist |
| **Know why the MiraBest loader is missing** | [`third_party/README.md`](third_party/README.md) |

### Start here

If you only read one file, read [`research/RESULTS.md`](research/RESULTS.md). It is the
authoritative record; anything quoted in the legacy notebooks predates the corrections
documented there.

## Layout

```
r1/                 analysis package: config, data access, preprocessing, models,
                    diagnostics, catalogue extraction
scripts/            one script per pre-registered test; see scripts/README.md for run order
tests/              40 tests
weights/            the five ensemble checkpoints plus the superseded single-model baseline
research/           the record:
  RESULTS.md          every reported number, with provenance
  DECISIONS.md        pre-registered criteria, including failures and withdrawn results
  STATE.md            where the project stands
  figures/            the paper figure
  *.json              machine-readable output, one per script
paper/              manuscript and submission material:
  rnaas_note.tex      AASTeX v7 source for the Research Note
  NOTE_TO_DATA.md     every number in the note mapped to its source file
  ZENODO_DEPOSIT.md   deposit checklist and paste-ready metadata
  rnaas_draft.md      working draft, with the reference-verification record
notebooks/legacy/   superseded notebooks, kept for provenance; not runnable
third_party/        why the MiraBest loader is not redistributed here
```

## Results

Each hypothesis had a pass/fail criterion written down before it was tested; the criteria and
their outcomes are in [`research/DECISIONS.md`](research/DECISIONS.md), and every number with
its uncertainty and provenance is in [`research/RESULTS.md`](research/RESULTS.md).

| | Question | Outcome |
|---|---|---|
| **H1** | Are the candidate inputs out of MiraBest's domain? | **Supported.** Only 15.3% [13.8, 16.9] of candidates fall inside MiraBest's p10–p90 angular-size range; identically-measured nonzero-pixel counts give KS = 0.68, p = 6e-46. |
| **H2** | Is dihedral prediction instability a usable label-free OOD score? | **Supported.** Candidates flip class under a rotation or mirror at 21.7% [19.9, 23.5] against a 5-fold held-out reference of 11.4% [9.4, 13.6] — a factor of 1.9, gap +10.3 pp with disjoint intervals. |
| **H3** | Does restricting to MiraBest-like sources restore stability? | **Not supported.** Neither an angular-size restriction (on the catalogue FWHM or an identically-measured pixel extent) nor a single-component restriction recovers; size-restricted subsets are marginally *worse*. |
| **H4** | Does ensemble ambiguity rank MiraBest's own hybrid/uncertain sources correctly? | **Supported.** p = 2.9e-10 and 7.2e-07 against the confident held-out set. |

Two further results are worth stating plainly because they are negative:

- **Seed disagreement is not an OOD score.** On a 104-source reference it appeared to miss its
  pre-registered ceiling by 0.4 pp and looked like bad luck. Against a properly powered 833-source
  reference the baseline is 38.2%, not 15.4%, and the candidate gap collapses from +26.4 pp to
  +3.7 pp with overlapping intervals.
- **The transfer failure is not removable by the obvious selection cuts.** Single-component
  candidates still flip at 2.2–2.5 times the reference, and 68.6% [66.5, 70.6] of candidates have
  another FIRST component within 2.25 arcmin, so a survey pipeline cannot filter its way out. That
  is the argument for a per-source instability score rather than a selection rule.

### Withdrawn results

Three results from the first version of this work do not survive and are retained, marked, in
`research/RESULTS.md` rather than deleted:

- **T1's "input-domain match: PASS"** — the criterion could not fail. It was satisfied by a single
  point estimate while the same cell's KS test rejected distributional equality at p = 2e-69.
- **T2's n = 833 paired test** — mis-paired, not merely contaminated. Paired cutouts were named
  `MB_<split>_<batch_index>.fits`, but `batch_index` counts within a batch, so 729 training sources
  collapsed onto 107 filenames and 625 of the 833 were compared against a cutout of a different
  galaxy. The 104 held-out sources were paired correctly and are the basis of the result that
  replaces it (99.0% label agreement, median |ΔP| 0.0037).
- **"150 of 150 bridge sources flip"** — tautological, since the bridge is defined as the sources
  nearest P = 0.5.

The SDSS environmental-density analysis has been dropped: the cohorts differ by a factor ~4 in
median flux, 27–32% of queries failed, and there are no redshifts, so it measured a confound.

## Setup

```bash
pip install --index-url https://download.pytorch.org/whl/cu126 \
    torch==2.14.1+cu126 torchvision==0.29.1+cu126
pip install -e .
pytest
```

The MiraBest_F dataset is not bundled. Download it once into `mirabest_data/`:

```bash
curl -L -o mirabest_data/MiraBest_F_batches.tar.gz \
    https://www.jb.man.ac.uk/research/MiraBest/MiraBest_F/MiraBest_F_batches.tar.gz
```

`r1.data.batch_dir()` extracts it on first use. See `third_party/README.md` for why the
loader itself is not redistributed here.

A CPU-only PyTorch build reproduces every result except the k-fold reference training, which is
impractically slow without a GPU. All cached inference tensors were computed on one device; the
measured CPU/GPU difference is in `research/device_consistency.json`.

Reproducing from scratch:

```python
from r1 import extract
extract.download_catalogue()                    # 69 MB, one request
cat = extract.load_catalogue()                  # row count verified against 946 432
cand = extract.select_extended_candidates(extract.select_sample(cat))
extract.download_cutouts(cand, out_dir)         # SkyView
```

Then run the scripts in `scripts/` in the order they are numbered in
`research/STATE.md`.

## Known issues

- **`data_extraction.ipynb` cannot run.** It selects its sample through
  `tapvizier.cds.unistra.fr`, which stopped answering on both port 80 and 443 in November 2026;
  CDS's `viz-bin` paths also return 404. `r1/extract.py` replaces it, reading the catalogue from
  the FIRST survey's own distribution at STScI. Reproducing the published sample needs
  `vizier_rounding=True`: VizieR served rounded columns, and five candidates sit at exactly
  SNR 7.000 on those values but below the threshold at full precision.
- **`main.ipynb` is superseded.** It still contains hard-coded absolute paths and the three
  withdrawn results above. `r1/` and `scripts/` reproduce everything in it.
- **The MiraBest loader is not distributed here.** No licence could be established for it, so
  redistribution is not permitted; see `third_party/README.md` for what was checked and how to
  obtain the dataset. Nothing in `r1/` depends on it — the batch reader, label mapping and cohort
  definitions are reimplemented and tested against the published cohort sizes.
- **Model weights are tracked in git**, which is why the repository is large. They will move to a
  Zenodo deposit with a DOI and be fetched on demand.
- `mirabest_data/F_batches` may be unreadable depending on how it was extracted; `r1/data.py`
  falls back to re-extracting the distributed tarball into a cache directory.

## Status

Research code supporting a short paper in preparation. The analysis is complete; the repository
is being prepared for release. Results in `research/RESULTS.md` are the authoritative numbers —
anything quoted in the notebooks predates the corrections above.

## Licence and attribution

The code in this repository is MIT licensed (see `LICENSE`). Text, figures and result files in
`research/` and `paper/` are CC-BY-4.0. No third-party code is redistributed here. The MiraBest_F dataset is the work of its original
authors and must be cited accordingly; FIRST catalogue and image data are from the VLA FIRST
survey, distributed by STScI, and cutouts are served by NASA SkyView.
