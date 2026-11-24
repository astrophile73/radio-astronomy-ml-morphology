# STATE (overwrite each update)

Last updated: 2026-11-23
Phase: 1 — fix validation flaws. H1 (P1-5) is done and supported. Gates 1 and 2 below are
unblocked and runnable on CPU from data already on disk; awaiting Raj's go-ahead to create
`r1/` and execute them.

## The critical path, in dependency order

The four phases are the *order of work*, not the order of decisions. What determines whether
there is a defensible result is a chain of four gates, each of which can kill or reshape the
claim. The ordering principle is: run the cheapest experiment that can kill the paper first.

| Gate | Question | Test | Cost | Outcome |
|---|---|---|---|---|
| 0 ✅ | Is the candidate sample actually out of MiraBest's domain? | P1-5 / H1 | done | **H1 supported** — 15.3% [13.8, 16.9] inside MiraBest's p10–p90 size range; nonzero-pixel KS 0.683 |
| 1 ✅ | Is our own pipeline faithful, or lossy? | P1-1, T2 on the 104 held-out sources | done | **PASS** — agreement 99.0% [97.1, 100.0], median \|ΔP\| 0.0037 [0.0013, 0.0073]. Candidate instability is not a preprocessing artefact. |
| 2 ✅ | Is the instability a *signal*, or noise the model always has? | P1-3 + P1-4 + H4 on 5 cohorts | done, 21 min | **P1-3 PASS** (21.7% vs 8.7%, disjoint CIs), **P1-4 FAIL** (ceiling leg), **H4 PASS**. H2 supported via the flip rate. |
| 3 ✅ | Is the failure astronomy, or our arithmetic? | G3-1a pipeline-rendered reference; G3-1b normalisation scalings; G3-2 leakage radius; G3-3 components | done | **All PASS.** Pipeline-rendered reference 7.7% [2.9, 13.5] vs MiraBest's own 8.7% — preprocessing does not inflate instability. Leakage shifts < 0.25 pp. 68.6% of candidates have another component within 2.25′, a modest contributor only. |
| 4 ✅ | Can we name the cause and give a prescription? | H3, size-restricted and single-component, on two size definitions | done | **H3 NOT SUPPORTED.** No subset recovers; size-restricted subsets are marginally *worse*. A warning, not a prescription. |
| 5 ✅ | Is the reference well enough powered to carry the claim? | KF-1, 5-fold x 5-seed over all 833 confident sources | 25 trainings, 872 s on GPU | **KF-1a PASS by 0.3 pp** (21.7% vs 11.4% [9.4, 13.6], gap +10.3 pp). **KF-1b FAIL decisively** — the true seed-disagreement baseline is 38.2%, not 15.4%. KF-1c PASS. |

**The hypothesis set is closed.** H1 supported, H2 supported via the dihedral flip rate, H3
not supported, H4 supported; P1-4 failed at every power level. The headline effect is a
factor of **1.9**, not the 2.8 the n=104 reference implied, and KF-1a clears its
pre-registered threshold by 0.3 pp. Every text quoting "2.5x" or "~3x" from the earlier
references is wrong and must be corrected.

The single best argument for this project's pre-registration discipline is KF-1b: on 104
sources, P1-4 missed its 15% ceiling by 0.4 pp and looked like bad luck; properly powered it
misses by 23 pp with the candidate gap collapsing from +26.4 pp to +3.7 pp. Relaxing that
ceiling when it was convenient would have left the project carrying a diagnostic that does
not work. Worth a sentence in the paper.

---

## Done (with evidence)

- `research/` created with STATE.md, DECISIONS.md, RESULTS.md (CLAUDE.md §9 templates).
- Full read-only audit of `main.ipynb` (36 cells), `data_extraction.ipynb` (5 cells),
  `MiraBest_F.py`, `README.md`, `.gitignore`, git history (2 commits), and the derived CSVs.
  Item-by-item verdicts in the table below; new findings logged in DECISIONS.md.
- Numbers recomputed this session from files on disk (not taken from the notebook):
  candidate `Maj` percentiles (median 8.46″; 75.5% below 2× the 5.4″ FIRST beam);
  seed-disagreement rate 835/1996 = 41.8%; fraction of candidates with P in (0.05, 0.95)
  = 79.1%; median |P − 0.5| = 0.326; Wilson 95% CI for 88.7% on n = 104 = [80.9, 93.3]%.
  All logged in RESULTS.md with provenance.
- Environment checked: the 5 ensemble checkpoints load cleanly on CPU
  (`load_state_dict` → all keys matched) and a batch of 32 forwards in 0.37 s, so the whole
  Phase 1 diagnostic set is runnable without a GPU.
- Confirmed all 104 held-out paired cutouts (`MB_test_*.fits`) are present in
  `FIRST_FITS_CUTOUTS/FIRST/MIRABEST_PAIRED_TEST/`, so the T2 re-run needs no new downloads.
- **2026-11-23: the `F_batches` ACL block is routed around.** `MiraBest_F_batches.tar.gz` is
  readable and extracts cleanly to a scratch directory (1256 sources across 8 batches,
  matching the notebook). Every MiraBest-side number is therefore unblocked without waiting
  on Raj. The repo copy of `mirabest_data/F_batches` is still unreadable and untouched; fixing
  it properly is a Phase 3 reproducibility item, not a blocker.
- **2026-11-23: P1-5 run, H1 supported on both legs.** Only 15.3% [13.8, 16.9] of candidates
  fall inside MiraBest's confident p10–p90 size range (criterion: < 50%); nonzero-pixel count
  123 [117, 129] against MiraBest test 294.5 [265.5, 340.0], KS = 0.683, p = 5.9e-46
  (criterion: KS > 0.30 at p < 0.01). MiraBest's size p10 of 12.5″ sits above the candidate
  p75 of 10.8″. Full numbers in RESULTS.md; the failed whole-mask-extent proxy and its
  replacement are logged in DECISIONS.md.

## Audit verdicts on CLAUDE.md §3

| # | Review item | Verdict | Evidence |
|---|---|---|---|
| 1 | T2 evaluated on training data | **Confirmed** | `main.ipynb` cell 26 selects all confident classes across `splits=("train","test")` → n = 833 = 729 train + 104 test. Native accuracy 98.1% vs 88.7% held-out. The contamination inflates the *pipeline-fidelity* metric, not only accuracy: on memorised images P saturates near 0/1, so label agreement is easy (98.0%) while rank correlation stays mediocre (rho = 0.81) — that gap is the tell. |
| 2 | Test set used for model selection | **Confirmed, with a correction** | True for the single baseline (cell 22 saves on best "Val Accuracy", which is `mirabest_test`; best epoch 13, 88.46%). Not true for the ensemble: `train_one_seed` returns and saves the final-epoch model, so 88.7 ± 1.3% is selection-clean. But there is no validation split anywhere, the test set is read 25× per seed, and the best-epoch figures (90.0 ± 0.5%) must never be quoted. |
| 3 | No reference for the 21.7% flip rate | **Confirmed** | Cell 31 computes `flip_changes` on `X_clean` only. No MiraBest-side flip rate exists anywhere in the repo, so 21.7% is uninterpretable as written. |
| 4 | Candidates vs training size distribution | **Partially done — overstated as absent** | Cell 12 already reports median nonzero pixels 312 (MiraBest) vs 123 (candidates), a 2.5× deficit. Genuinely missing: the `Maj` vs `size_arcsec` comparison, any distributional test on size, and the fraction inside MiraBest's range. |
| 5 | Component vs source problem | **Confirmed, and worse than stated** | Sampling is by catalogue `recno`, i.e. components, and cutouts are centred on the component. Candidate `Maj` median is 8.46″ against a 5.4″ beam: 75.5% are barely resolved. The test cannot be done from `FIRST_10000_catalog.csv`, which is a 1-in-94 sample — a nearest-neighbour search on it measures the sampling step, not source density. It needs a per-candidate TAP cone search against the full 946 432-row catalogue. |
| 6 | T3(b) is tautological | **Half right — the "remove it" half is rejected** | The bridge is defined as the 150 smallest \|P − 0.5\|, so "150 of 150 flip" is indeed circular and is withdrawn. But `flip_changes` is computed over all 1996 candidates, and that 21.7% global rate is not tautological — it is the single strongest piece of evidence in the repo and becomes the H2 diagnostic. Reframe, do not remove. |
| 7 | Repo hygiene | **Confirmed, and partly worse** | Hard-coded `I:\...` paths in both notebooks while the repo now sits on `E:\` — the notebooks cannot run as committed. Six `.pth` files, ~268 MB, are tracked in git. No `requirements.txt` exists at all (the README has a bare `pip install` line). The 3′ vs 4.5′ error is in `main.ipynb` cell 0 as well as the README; the **code is right** (4.5′ ÷ 1.8″ = 150 px, matching MiraBest's 150 × 150 format) and both prose statements are wrong. The README also still presents the SDSS environment analysis as a component and claims "T1 and T2 pass". |
| 8 | `MiraBest_F.py` licence | **Confirmed** | No copyright, licence, author or citation string anywhere in `MiraBest_F.py` or `MiraBest.py` (grep for copyright/licen/author/cite returns nothing). The repo's MIT LICENSE, © Raj Kondekar, currently appears to cover a third-party file. |

### Findings the review missed (all logged in DECISIONS.md)

1. **T1's pass criterion cannot fail.** Linear mode is declared PASS because its median
   nonzero pixel (0.2089) sits just inside MiraBest's p10–p90 (0.0353–0.2278), while the
   same cell reports KS = 0.380, p = 2.3e-69. The notebook's own data say the input domains
   do **not** match. "T1 and T2 pass" in the README is not defensible. Also, the code picks
   the stretch by smallest KS, which is not the registered criterion.
2. **The quoted uncertainty is the wrong one.** ±1.3 pp is the seed spread; the Wilson
   interval on n = 104 is [80.9, 93.3]%, half-width 6.2 pp. The finite test set dominates by
   ~5×, so ±1.3 pp understates the uncertainty.
3. **The 30″ leakage radius is inconsistent with a 4.5′ cutout** and with off-centre lobes;
   only 28 of 2044 were excluded. Needs a sensitivity run at the 2.25′ half-field.
4. **Two cheap results are already sitting in the data, uncomputed.** Seed disagreement is
   41.8% of candidates, and 79.1% of candidates have P in (0.05, 0.95) against 42.3% for
   MiraBest's confident held-out sources and 82.4% for its hybrids — the blind sample looks
   *more* ambiguous than MiraBest's hybrids. Both come straight out of
   `FIRST_predictions_master_v2.csv` with no inference at all.
5. **Determinism is not met** (CLAUDE.md §4): no `cudnn.deterministic`, no
   `use_deterministic_algorithms`, no DataLoader worker seeding, so retraining will not
   reproduce 88.7 ± 1.3%. `MBRandom` in `MiraBest_F.py` also calls `np.random.choice`
   unseeded — a landmine if that class is ever used.
6. **Silent `except: pass`** in cell 12's preprocessing loop drops failed reads without
   tracking names, so the arrays could misalign with `df_clean`. Zero failures were recorded,
   so no current number is affected, but cell 14 does it properly and cell 12 does not.
7. **Per-image max normalisation** in `preprocess_cutout` sets the intensity scale from a
   single brightest pixel. This is a plausible *cause* of part of the measured domain shift
   and is an alternative explanation that H2 must rule out, not a detail.

## In progress (2026-11-23)

- **`r1/` package built and tested.** `config.py` (relative paths, no `I:\`), `data.py`,
  `preprocess.py`, `models.py`, `diagnostics.py`, plus `tests/` and `pytest.ini`.
  **24 tests pass.** Notebooks untouched.
- **The preprocessing reproduction contract is established** (`tests/test_preprocess.py`).
  `r1.preprocess` reproduces the stored `FIRST_clean_X_final.npy` to within float32
  threshold noise: across all 1996 candidates, 4 images and **6 pixels of 44.9 million**
  differ, every one of them a pixel sitting exactly on the 3-sigma cut where a last-bit
  difference in `std_bg` between astropy versions decides inclusion. The ratio of retained
  pixel values is exactly 1.0 and no aggregate statistic moves (median nonzero count 123
  against 123; median of per-image median nonzero pixel identical to 6 decimal places).
  Bitwise equality is deliberately not asserted, since it is not stable across astropy
  versions and nothing downstream depends on it. **The stored arrays, and every number
  derived from them, are therefore safe to reuse.**
- The test suite also pins the cohort construction against the published sample sizes
  (confident 833 = 729 + 104, uncertain 389, hybrid 34), confirms the label-index-to-class-code
  mapping from `batches.meta`, and asserts all 104 held-out paired cutouts exist.
- **Gate 1 PASSED** (`scripts/gate1_paired_pipeline.py`, output in
  `research/gate1_paired_pipeline.json`). On the 104 held-out sources: label agreement 99.0%
  [97.1, 100.0] against a criterion of CI low ≥ 95%; median |ΔP| 0.0037 [0.0013, 0.0073]
  against a criterion of CI high < 0.05; Spearman rho 0.987 [0.973, 0.992]; native-image
  accuracy 88.5% [80.9, 93.3] Wilson, which reproduces the published final-epoch 88.7% on
  the same split and independently confirms the right checkpoints and split are in use.
  **The pipeline is faithful, so candidate instability is not a preprocessing artefact and
  the domain-shift question is answerable.**
- **The notebook's n = 833 T2 is withdrawn as mis-paired, not merely contaminated.** Paired
  cutouts were named `MB_<split>_<batch_index>.fits`; `batch_index` counts within a batch and
  every MiraBest batch holds 157 sources, so the 729 confident training sources collapse onto
  107 filenames (up to 7 each). 625 of the 833 sources were compared against a cutout of a
  different galaxy. The 104 test sources are from a single batch, so they paired correctly and
  Gate 1 stands. The training-side comparison is dropped as unrecoverable: 8 download threads
  raced for each name, so the files cannot be attributed to sources. Guards and two regression
  tests added. Full account in DECISIONS.md.
- **Gate 2 COMPLETE** (`scripts/gate2_instability.py`, 21 min wall on 16 CPU cores; output
  in `research/gate2_instability.json`, raw `(8, 5, n)` probability tensors cached in
  `research/_view_probs/` so all later re-analysis is free).
  - **P1-3 PASS.** Candidate dihedral flip rate 21.7% [19.9, 23.5] against a held-out
    reference of 8.7% [3.8, 14.4]: gap +13.0 pp, CIs disjoint, reference under the 15%
    ceiling. **H2 is supported** and the 21.7% is anchored at 2.5x the held-out rate.
  - **P1-4 FAIL** on its ceiling leg only (reference 15.4% > 15%). Threshold not moved. Seed
    disagreement has a high floor — 13.0% even on memorised training data — so it
    discriminates less cleanly than the flip rate despite a wider gap. The fail is
    underpowered: [8.7, 22.1] on n = 104 straddles the ceiling.
  - **H4 PASS.** Uncertain 0.364 and hybrid 0.259 median |P−0.5| against confident-test
    0.481; Mann-Whitney p = 2.9e-10 and 7.2e-07.
  - **Post-hoc, not pre-registered:** the flip rate is monotone in distance from the training
    manifold (train 1.8% < test 8.7% < candidates 21.7% ≈ uncertain 24.2% < hybrid 41.2%),
    and the blind candidates are statistically indistinguishable from MiraBest's *uncertain*
    class while decisively separated from its confident held-out set. Candidate headline for
    the note; needs a confirmatory equivalence test with a pre-stated margin.

### Upstream bug found in `MiraBest_F.py`

`MBHybrid`'s docstring states its classes are `[110, 112]` and `[210]`, copied from
`MBFRUncertain`. Its code uses label indices `[8]` and `[9]`, i.e. class codes 300 and 310,
which is what the published n = 34 corresponds to. The code is correct and the docstring is
wrong; `r1/config.py` replicates the code and records the discrepancy. Worth reporting
upstream when the provenance question (§3.8) is settled.

## Phased plan (awaiting approval)

**Phase 1 — validation flaws.** Criteria for P1-1…P1-5 are already pre-registered in
DECISIONS.md. Work goes into a new `r1/` package (`r1/config.py`, `r1/data.py`,
`r1/preprocess.py`, `r1/models.py`, `r1/diagnostics.py`) with `pytest` tests for
preprocessing, the leakage cross-match and the flip metric; notebooks are left untouched
until the package reproduces the numbers.
- P1-1 T2 on the 104 held-out sources only, with bootstrap CIs. Runnable now, no GPU, no
  network (cutouts verified present).
- P1-2 Reporting fix: Wilson interval as the headline uncertainty.
- P1-3 Reference dihedral flip rate on five cohorts with CIs — the control that makes 21.7%
  mean something. ~15 min CPU for the candidates, ~10 min for the MiraBest cohorts.
- P1-4 Seed-disagreement rate on the same cohorts with CIs.
- P1-5 Angular-size comparison, `Maj` vs `size_arcsec` plus an identically-measured proxy.
- P1-6 Withdraw the T1 "PASS" and the "150 of 150" sentence; keep both visible as superseded.
- P1-7 Leakage sensitivity at 30″ vs 2.25′.

**Phase 2 — diagnostics H1–H4.** H1 from P1-5 plus the pixel-domain evidence. H2 from P1-3
and P1-4, with the per-image-max normalisation ruled in or out as a confound. H3 the
size-matched and single-component-restricted subsample, which needs the component-density
TAP query first. H4 the ambiguity ranking of MiraBest hybrid/uncertain sources with
bootstrap CIs — note `MBHybrid` has only n = 34, so the interval will be wide and must be
shown. Each gets its criterion pre-registered before it runs.

**Phase 3 — repo and release.** `config.py` and relative paths; `.pth` files out of git
history into a Zenodo record or GitHub Release with a download helper; pinned
`requirements.txt`; README rewritten (fix 3′ → 4.5′, drop the environment section, drop "T1
and T2 pass", add MiraBest attribution); notebook prose stripped of "peer review", "retired
first attempt" and "v2"; `MiraBest_F.py` provenance and licence settled.

**Phase 4 — RNAAS draft** in `paper/`, ≤1000 words and ≤1 figure, limits to be verified on
the AAS site at the time of writing, plus the Zenodo code/weights release.

## PENDING (Raj to run)

Nothing is blocking Gate 1 or Gate 2. The items below are needed for Phase 3
reproducibility, not for the science, and can wait.

1. **Fix read access to the MiraBest batches** (downgraded from blocking to Phase 3). The
   analysis now reads the tarball into a scratch directory, but a clean clone must be able to
   read `mirabest_data/F_batches` directly:
   ```powershell
   icacls "e:\Radio and Gamma-ray observational astronomy Data analysis projects\R1\mirabest_data\F_batches" /grant "$($env:USERNAME):(OI)(CI)RX" /T
   python -c "import pickle; e=pickle.load(open(r'mirabest_data\F_batches\data_batch_1','rb'),encoding='latin1'); print(len(e['labels']))"
   ```
   Paste back the printed count; it should be 157.

2. **Confirm whether a CUDA PyTorch environment still exists.** The notebook recorded
   `cuda:0`, but the interpreter on this machine is `torch 2.14.1+cpu`,
   `cuda.is_available() == False`. Phase 1 does not need a GPU; retraining (the P1-2
   validation-split option) does.
   ```powershell
   python -c "import torch,sys; print(sys.executable); print(torch.__version__, torch.cuda.is_available())"
   conda env list
   ```
   Paste back both outputs.

3. **Confirm the library versions to pin.** This interpreter reports numpy 2.5.3,
   pandas 3.0.6, scipy 1.18.1, astropy 8.0.1, torch 2.14.1+cpu — all newer than whatever ran
   the September notebook, which matters for reproducing stored numbers.
   ```powershell
   python -m pip freeze > research\env_freeze.txt
   ```
   Paste back the file or just the lines for numpy/pandas/scipy/astropy/torch/torchvision.

Not blocking, for later: the component-density query in Phase 2 needs ~1996 VizieR TAP cone
searches against `VIII/92/first14` (network, no GPU, ~20–40 min). The 729 contaminated
paired cutouts are mostly absent (107 of 729 present) — not needed, since P1-1 uses the 104.

## Open questions for Raj

1. **Which claim is the note's headline?** Now decidable, because Gate 2 passed. Options:
   (a) *methodological* — the dihedral flip rate is a cheap label-free OOD score, 21.7%
   against a held-out 8.7%, validated against MiraBest's own uncertain and hybrid classes;
   (b) *descriptive* — a blind FIRST sample scored by a MiraBest-trained ensemble behaves
   like MiraBest's unclassifiable sources. (b) is the sharper sentence and (a) is the more
   useful tool for EMU/LoTSS. Recommended: lead on (a) and use (b) as the supporting result,
   since (a) is pre-registered and passed while (b) is currently post-hoc.
2. **Scope of Gate 3.** Legs 1 and 2 need nothing from you. Leg 3 needs ~1996 VizieR TAP
   queries over 20–40 min. Run it now, or defer until Gate 4 needs the component flags?
3. **P1-2: retrain with a proper validation split, or report final-epoch only?** Still open,
   still not on the critical path. Recommendation unchanged: final-epoch only. Note Gate 2
   added a reason to care — a k-fold held-out reference over all 833 confident sources is the
   only well-powered way to re-test P1-4's ceiling, and that needs retraining.
4. **Is `main.ipynb` to be rewritten or superseded?** Its prose is written as a reply to a
   review ("retired first attempt", "peer review", "v2"), and three of its stored results are
   now withdrawn (T1's pass, the n = 833 T2, "150 of 150"). I would rebuild the analysis in
   `r1/` and leave the notebook as a thin caller, but that is a larger change to your document
   than a prose edit.
5. **MiraBest provenance.** The `url` field in `MiraBest_F.py` points at
   `jb.man.ac.uk/research/MiraBest/MiraBest_F/`, consistent with the Manchester MiraBest-F
   release of Porter & Scaife, but I have not verified the upstream repository, its licence or
   the correct citation and will not guess them. Want me to look them up and bring you the
   exact licence text and BibTeX to check before anything goes in the README?

## Next action

The science is finished; what remains is one robustness check, two decisions from Raj, and
then writing. In order:

**1. Device consistency — DONE 2026-11-24.** At Raj's direction, rather than measuring a
device delta and keeping a mixed set, all eight cached tensors were regenerated on the GPU so
every comparison in the project rests on one device. Measured over 7348 sources: largest
per-source probability difference 4.1e-3 (cuDNN algorithm selection, not just float
reordering), **one** flip flag changed, largest cohort shift 0.05 pp, all headline values
identical to two decimals. KF-1a re-ran at exactly +10.3 pp, PASS. All six downstream
analyses and the figure were regenerated from the GPU set; the only changed number anywhere
is the `p99` sensitivity gap, +14.5 -> +14.6 pp, which does not affect any verdict. 30 tests
pass. CPU set preserved in `research/_view_probs_cpu/`, delta in
`research/device_consistency.json`.

**2. Decisions owed by Raj** (both have been open for several sessions, and Phase 4 cannot
start without them):
   - **Headline framing.** Methodological (the flip rate as a validated label-free diagnostic)
     or descriptive (a blind sample behaves like MiraBest's unclassifiable sources)?
     Recommended: methodological, because it is the leg that was pre-registered and passed,
     and H3's failure means a pipeline cannot filter its way out, so a per-source score is the
     actionable contribution. If the descriptive framing is chosen instead, the post-hoc
     candidates-vs-uncertain equivalence must first be confirmed with a margin stated in
     advance (pre-registration already drafted in DECISIONS.md, 2026-11-23).
   - **The "different task, not a harder task" interpretation.** Consistent with every result,
     demonstrated by none. Write it explicitly as interpretation, or drop it.

**3. Phase 3 — repo and release.** Now substantial, not cosmetic:
   - `data_extraction.ipynb` **cannot run at all**: its TAP host is dead. Migrate to
     `r1.config.VIZIER_SERVER` or to the STScI bulk catalogue.
   - Notebooks still carry hard-coded `I:\` paths and three withdrawn results (T1's pass, the
     n = 833 T2, "150 of 150").
   - ~268 MB of `.pth` in git history → Zenodo or a GitHub Release with a download helper.
   - No `requirements.txt`; pin the versions in `research/env_freeze.txt` once generated.
   - README asserts "T1 and T2 pass", says 3 arcmin where the code uses 4.5, and still
     presents the dropped SDSS environment analysis as a component.
   - `MiraBest_F.py` licence, attribution and citation unresolved (§3.8), plus the `MBHybrid`
     docstring bug to report upstream.
   - `mirabest_data/F_batches` ACL fix so a clean clone works without the tarball fallback.

**4. Phase 4 — the RNAAS draft**, ≤1000 words and the one figure, which already exists at
`research/figures/fig1_flip_rate_ladder.pdf` and regenerates from the JSON outputs.
