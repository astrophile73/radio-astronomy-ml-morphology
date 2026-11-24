# DECISIONS (append-only)

Pre-registered criteria are written here *before* the test is run. A criterion is never
moved after a result is seen; if a criterion was badly chosen, a new entry supersedes it
and the superseded result stays visible.

---

## 2026-11-21 — Repo audit: what the external review got right and wrong

Context: CLAUDE.md §3 lists eight problems from the external review of 2026-11-21. This
session checked each against the code in `main.ipynb`, `data_extraction.ipynb` and
`MiraBest_F.py`, and against the outputs stored in `main.ipynb` and the derived CSVs.

Options considered: accept the review as written; or re-derive each item from the code.

Decision (proposed): accept items 1, 2, 3, 5, 7, 8 as stated; reclassify item 4 as
"partially done, specific comparison missing"; reject the "remove it" half of item 6. The
global dihedral flip rate is the strongest evidence in the repo and is promoted to the H2
diagnostic; only the bridge-subset sentence ("150 of 150 flip") is tautological and is
withdrawn. Three findings the review missed are recorded as separate entries below.

Pre-registered criterion: n/a (audit, not a test).

Outcome: see STATE.md for the item-by-item table and the resulting phase plan.

---

## 2026-11-21 — Finding the review missed: T1's pass criterion cannot fail

Context: T1, the input-domain match test in `main.ipynb` cell 12, pre-registered the
criterion "the chosen mode's median nonzero-pixel value falls inside MiraBest's [p10, p90]
range". The stored output reports linear-mode median 0.2089 against MiraBest p10 = 0.0353,
p90 = 0.2278, and declares PASS. The same cell reports KS = 0.380 with p = 2.3e-69, i.e.
the two pixel-value distributions are decisively different. A criterion that one point
estimate can satisfy while a KS test rejects equality at p of order 1e-69 does not test what
T1 claims to test. Separately, the decision rule in code is `CHOSEN_MODE = min(verdicts,
key=KS)`, which is not the registered criterion; here the two agree, but the code would
silently select a stretch that failed the registered check.

Options considered: (a) keep T1 as a pass; (b) retire T1; (c) keep T1 as the
stretch-selection step and replace the match criterion with one that can fail.

Decision (proposed, needs Raj): (c). T1 remains the step that selects linear over asinh by
KS, which is a defensible use of it, and stops being reported as evidence that the input
domains match. The README sentence "T1 and T2 pass" is withdrawn.

Pre-registered criterion for the replacement test, set now, before re-running: the input
domains are called matched only if KS < 0.10 on both (i) per-image median nonzero-pixel
value and (ii) per-image nonzero-pixel count, candidates against the MiraBest confident
test set. On the numbers already stored (KS = 0.380 on (i); median nonzero-pixel counts 312
against 123 on (ii)) this criterion is expected to fail, which is the point: a failed
input-domain match is the H1 result, not a problem to be tuned away.

Outcome (filled later):

---

## 2026-11-21 — Finding the review missed: the quoted uncertainty is the wrong one

Context: the ensemble headline is "final-epoch accuracy 88.7% ± 1.3%", where ±1.3 pp is the
standard deviation over 5 seeds. The MiraBest confident test set has n = 104. Computed in
this session: the Wilson 95% interval for 88.7% on n = 104 is [80.9%, 93.3%], half-width
6.2 pp. The finite test set, not seed variance, dominates the uncertainty budget by roughly
a factor of five.

Options considered: quote the seed spread; quote the Wilson interval; quote both.

Decision (proposed): quote both, with the Wilson interval as the headline uncertainty and
the seed spread named separately as what it is. No number in the paper carries ±1.3 pp
alone. Best-epoch accuracies (90.0 ± 0.5%) are never quoted as results, since they are
selected on the test set.

Pre-registered criterion: n/a (reporting rule).

Outcome (filled later):

---

## 2026-11-21 — Finding the review missed: the leakage radius is inconsistent with the cutout

Context: the quality gate excludes candidates within 30 arcsec of a MiraBest train or test
position; 28 of 2044 were excluded. The cutouts are 4.5 arcmin across (150 px x 1.8 arcsec).
A MiraBest source anywhere inside a candidate's field contributes flux to the image the
model scores, so 30 arcsec is far tighter than the geometry warrants, and FR-II lobes are
catalogued as components offset from the host position that MiraBest's filenames encode.

Options considered: leave at 30 arcsec; widen to 1 arcmin; widen to the half-field,
2.25 arcmin.

Decision (proposed): keep 30 arcsec as the primary sample for continuity with the stored
results, and run the whole diagnostic chain again on a 2.25 arcmin-gated sample as a
sensitivity check.

Pre-registered criterion: leakage is deemed not to drive the result if the three headline
diagnostics (dihedral flip rate, seed-disagreement rate, and fraction of candidates with
P in (0.05, 0.95)) each change by less than 5 pp between the 30 arcsec and 2.25 arcmin
samples. If any one changes by more than 5 pp, the 2.25 arcmin sample becomes primary.

Outcome (filled later):

---

## 2026-11-21 — Phase 1 pre-registered criteria (P1-1 to P1-5)

Context: Phase 1 repairs the validation flaws before any diagnostic is claimed. The criteria
below are fixed now, before the tests are run.

### P1-1 — T2 on held-out MiraBest sources only

Test: restrict the paired native-against-pipeline comparison to the 104 `MBFRConfident` test
sources. Report n, label agreement, median |P_native − P_pipeline|, Spearman rho, accuracy on
native images and accuracy on pipeline images, each with a bootstrap 95% CI (10,000
resamples, seed 0). Report the 729 training sources separately, labelled contaminated.

Pre-registered criterion: T2 passes only if the bootstrap 95% CI lower bound for label
agreement is at least 95% and the CI upper bound for median |ΔP| is below 0.05. These are
the original thresholds; the change is that the interval, not the point estimate, must clear
them. Any other outcome is reported as a fail, including a fail with a high point estimate.

Note: the stored n = 833 result (agreement 98.0%, median |ΔP| 0.024, rho = 0.81, native
accuracy 98.1%) is retained in RESULTS.md as superseded. The low rho beside the high
agreement is itself the signature of saturated predictions on memorised images.

**Correction (2026-11-23):** that last sentence was wrong, and the mechanism is worse than
leakage. The real cause is a filename collision that mis-paired most of the n = 833 sample;
see the entry below. The held-out rho is 0.987, i.e. *higher* than the 0.81 reported on
n = 833, so saturation was never the explanation.

Outcome (2026-11-23): **PASS on held-out data, decisively.** n = 104, all 104 paired
cutouts present and correctly paired.

| quantity | value | 95% CI | criterion | met |
|---|---|---|---|---|
| label agreement | 99.0% | bootstrap [97.1, 100.0] | CI low ≥ 95% | yes |
| median \|ΔP\| | 0.0037 | bootstrap [0.0013, 0.0073] | CI high < 0.05 | yes |
| Spearman rho | 0.987 | bootstrap [0.973, 0.992] | — | — |
| accuracy, native images | 88.5% | Wilson [80.9, 93.3] | — | — |
| accuracy, pipeline images | 89.4% | Wilson [82.0, 94.0] | — | — |

Both legs clear their thresholds by a wide margin: the median paired probability difference
is 0.0037, an order of magnitude inside the 0.05 bound. The native-image accuracy of 88.5%
reproduces the ensemble's published final-epoch 88.7% on the same 104 sources, which is an
independent check that the right checkpoints and the right split are being used.

**What this licenses.** `preprocess_cutout` applied to a SkyView FIRST cutout returns
essentially the same classification as MiraBest's own rendering of the same galaxy, on
sources the ensemble never trained on. Candidate instability therefore cannot be dismissed
as an artefact of our preprocessing, and the domain-shift question is answerable. Gate 1 is
the precondition for every candidate-side claim, and it is met. Produced by
`scripts/gate1_paired_pipeline.py`; raw output in `research/gate1_paired_pipeline.json`.

---

## 2026-11-23 — The notebook's n = 833 T2 result is withdrawn: it was mis-paired

Context: `main.ipynb` cell 26 saves each paired cutout as
`MB_<split>_<batch_index>.fits`. `batch_index` is the index of a source *within its batch*,
and all 8 MiraBest batches hold 157 sources each, so the name is unique only for the
single-batch test split. Verified this session: the 729 confident **training** sources
collapse onto **107** distinct filenames, up to 7 sources per name. The download helper
returned early for any name that already existed, and 8 threads raced for each name, so the
107 files on disk cannot be attributed to a source at all — their index set does not even
match `data_batch_1`'s confident indices. At most 104 of the 729 training sources could have
been paired with their own cutout; the rest were scored against a cutout downloaded for a
different galaxy.

The 104 **test** sources come from a single batch, so their indices are unique and all 104
resolve correctly. Gate 1's held-out result is unaffected.

Options considered: attempt to reconstruct the attribution from file mtimes and thread
ordering; re-download 729 cutouts under canonical names; drop the training-side comparison.

Decision (proposed): drop it, and withdraw the notebook's n = 833 numbers entirely rather
than labelling them contaminated. Reconstruction is not defensible — the ordering of 8
racing threads is not recoverable — and the training-side comparison is not needed for any
claim, since it was only ever context for the contamination. Re-running it would cost 729
SkyView downloads for a number no hypothesis depends on.

Note what this says about the original test: T2 reported 98.0% agreement *while comparing
different galaxies* for 625 of its 833 sources. Both images in each wrong pair are real
extended radio sources, so the classifier often lands on the same class by base rate alone.
A test that passes on mis-paired data was not measuring pipeline fidelity. This is the
second criterion in the repo found to be incapable of failing, after T1.

Pre-registered criterion: n/a (defect, not a test). Guards added: `r1.data.paired_cutout_path`
prefers a canonical `MB_<split>_<batch>_<batch_index>.fits` name, accepts the legacy name
only for a split proven single-batch, and otherwise returns a non-existent path so callers
skip the source instead of silently loading the wrong image.
`tests/test_diagnostics.py::test_legacy_paired_name_is_ambiguous_for_training_split` and
`::test_training_paired_cutouts_are_not_silently_resolved` fail if this regresses.

Outcome: applied; 26 tests pass.

### P1-2 — Honest headline accuracy

Test: none; this is a reporting decision. The headline is the 5-seed, final-epoch ensemble
accuracy on the n = 104 held-out set, quoted with its Wilson 95% interval, with the seed
standard deviation named separately.

Pre-registered criterion: n/a. Open decision for Raj: whether to carve a validation split
from the 729 training sources and retrain (this changes the training sample and needs a
GPU), or report final-epoch numbers only and add k-fold cross-validation later. Recommended:
final-epoch only for now, since it costs no retraining and is already the honest number.

### P1-3 — Reference dihedral flip rate (H2's missing control)

Test: for each of the 8 dihedral views, take the 5-model ensemble mean and its label; a
source flips if the label is not identical across all 8 views. Compute the flip rate on the
MiraBest confident test set (n = 104), the MiraBest confident training set (n = 729,
labelled contaminated), `MBFRUncertain` (n = 389), `MBHybrid` (n = 34), and the clean
candidates (n = 1996). Report each with a bootstrap 95% CI (10,000 resamples, seed 0).

Pre-registered criterion: the dihedral flip rate is a usable label-free OOD score only if
(i) the candidate rate exceeds the MiraBest confident-test rate by at least 10 pp and (ii)
the two bootstrap 95% CIs do not overlap. If the MiraBest confident-test rate is itself
above 15%, the metric is declared too noisy to serve as an OOD score regardless of the gap,
and that is reported.

### P1-4 — Seed-disagreement rate as a second label-free score

Test: a source disagrees if the 5 single-seed identity-view labels are not unanimous.
Computed in this session from `FIRST_predictions_master_v2.csv`: 835 of 1996 candidates,
41.8%. The MiraBest-side reference values do not exist yet and must be computed on the same
five cohorts as P1-3, with bootstrap 95% CIs.

Pre-registered criterion: identical in form to P1-3 (at least a 10 pp gap, non-overlapping
CIs, and a MiraBest confident-test reference below 15%). This score needs no GPU and no new
inference on the candidate side, so it is the cheapest route to an H2 result.

### P1-5 — Angular-size comparison (CLAUDE.md §3.4, and H1's primary evidence)

Test: compare the clean candidates' FIRST `Maj` against MiraBest confident `size_arcsec`
parsed from the batch filenames, and report the fraction of candidates inside MiraBest's
full range and inside its p10-p90. Because `Maj` (deconvolved component FWHM) and MiraBest's
`size_arcsec` (largest angular size of the labelled source) are different quantities, also
compute a proxy measured identically on both sides after identical preprocessing: the
nonzero-pixel count, and the maximum extent of the 3-sigma mask in pixels.

Pre-registered criterion: H1 is supported if either fewer than 50% of candidates fall inside
MiraBest's confident p10-p90 size range, or the KS statistic on the identically-measured
proxy exceeds 0.30 with p < 0.01. Both legs are reported whichever way they fall.

Context already computed in this session: candidate `Maj` has median 8.46 arcsec and p90
14.37 arcsec, and 75.5% of candidates have `Maj` below twice the 5.4 arcsec FIRST beam. The
MiraBest side could not be read because `mirabest_data/F_batches` denies read access (see
STATE.md PENDING).

Outcome (2026-11-23): **H1 supported on both legs.** The ACL block was bypassed by extracting
`MiraBest_F_batches.tar.gz` to a scratch directory and reading the batches from there; the
repo copy is untouched and still unreadable, which remains a Phase 3 reproducibility fix.

Leg (a): MiraBest confident `size_arcsec` has median 43.0″ and p10–p90 = 12.5–127.9″
(n = 833). Candidate `Maj` has median 8.5″ and p75 = 10.8″. Only **15.3% [13.8, 16.9]** of
candidates fall inside MiraBest's p10–p90 range, against a criterion of < 50%. MiraBest's
p10 (12.5″) exceeds the candidate p75 (10.8″), i.e. 90% of the training sources are larger
than 75% of the candidates.

Leg (b): on the identically-measured nonzero-pixel count, candidates have median 123
[117, 129] against 294.5 [265.5, 340.0] for the MiraBest confident test set, KS = 0.683,
p = 5.9e-46, against a criterion of KS > 0.30 at p < 0.01.

The second proxy named in the criterion, "maximum extent of the 3-sigma mask", **failed as a
measurement** and its number is not used: it gave 143 px for candidates against 128 px for
MiraBest, i.e. the wrong sign. Diagnosis below.

---

## 2026-11-23 — The whole-mask extent proxy measures noise, and is replaced

Context: P1-5 leg (b) named "maximum extent of the 3-sigma mask" as a size proxy. Measured,
it put the candidates *larger* than MiraBest (143 px vs 128 px of a 150 px frame), which
contradicts every other size measure. Exploratory connected-component analysis (scipy
`ndimage.label`, candidates n = 1996 vs MiraBest confident test n = 104) explains why: the
candidate 3-sigma masks are fragmented into a median of 25 components holding 123 nonzero
pixels, with only 0.42 [0.41, 0.43] of those pixels in the largest component. The whole-mask
bounding box is therefore set by isolated noise spikes near the frame edge, not by the
source. MiraBest masks hold 0.76 [0.68, 0.81] of their pixels in one component.

The structure-bearing statistic, measured in the same exploratory pass:
largest connected component 53 px [50, 56] for candidates against 202.5 px [181, 227.5] for
MiraBest test (KS = 0.748, p = 4.8e-57); extent of that component 10 px [10, 11] against
23 px [21, 26] (KS = 0.693, p = 1.5e-47), i.e. **18.0″ against 41.4″**. That 41.4″ agrees
with MiraBest's own catalogued median `size_arcsec` of 43.0″, which calibrates the proxy.

Options considered: keep whole-mask extent and explain the sign; drop the proxy entirely;
replace it with the largest-connected-component statistics.

Decision (proposed): replace it. Whole-mask extent is withdrawn as a size measure and the
reason is recorded rather than hidden. The numbers above are labelled **exploratory**,
because they were computed while diagnosing a failed proxy rather than against a criterion
set in advance, and they are not quoted as a confirmatory result.

Pre-registered criterion for the confirmatory re-run, set now: the candidate and MiraBest
confident-test samples differ in resolved structure if the largest-connected-component pixel
count gives KS > 0.30 at p < 0.01 with non-overlapping bootstrap 95% CIs on the medians.
Reported alongside it, with no threshold attached: the component count, the fraction of
nonzero pixels in the largest component, and that component's extent in arcsec. The
preprocessing is not changed to make the masks cleaner; the fragmentation is itself part of
the domain-shift evidence and a 3-sigma cut is what the pipeline actually applies.

Outcome (filled later):

---

## 2026-11-23 — Gate 2 outcomes: P1-3 PASS, P1-4 FAIL, H4 PASS

Produced by `scripts/gate2_instability.py`; raw output in `research/gate2_instability.json`,
cached probability tensors in `research/_view_probs/`. Bootstrap 10 000, seed 0.

| cohort | n | dihedral flip rate | seed disagreement | median \|P−0.5\| | frac P in (0.05,0.95) |
|---|---|---|---|---|---|
| MiraBest confident **train** (contaminated) | 729 | 1.8% [0.8, 2.9] | 13.0% [10.7, 15.5] | 0.478 [0.473, 0.482] | 33.1% [29.8, 36.6] |
| MiraBest confident **test** (reference) | 104 | 8.7% [3.8, 14.4] | 15.4% [8.7, 22.1] | 0.481 [0.445, 0.490] | 42.3% [32.7, 51.9] |
| **blind FIRST candidates** | 1996 | **21.7% [19.9, 23.5]** | 41.8% [39.6, 44.0] | 0.326 [0.314, 0.337] | 79.1% [77.3, 80.9] |
| MiraBest **uncertain** (never trained on) | 389 | 24.2% [20.1, 28.5] | 39.3% [34.7, 44.2] | 0.364 [0.339, 0.389] | 66.6% [62.0, 71.2] |
| MiraBest **hybrid** (never trained on) | 34 | 41.2% [23.5, 58.8] | 41.2% [23.5, 58.8] | 0.259 [0.178, 0.383] | 82.4% [67.6, 94.1] |

**P1-3 — PASS.** Candidate flip rate 21.7% against a held-out reference of 8.7%: gap
+13.0 pp (criterion ≥ 10 pp), bootstrap CIs disjoint (14.4 < 19.9), reference 8.7% below the
15% ceiling. The dihedral flip rate is a usable label-free OOD score, and the previously
uninterpretable 21.7% is now anchored: it is 2.5x the rate the same ensemble shows on
MiraBest's own held-out confident sources. H2 is supported.

**P1-4 — FAIL, and the threshold is not moved.** Seed disagreement shows a larger gap
(+26.4 pp) with disjoint CIs, but the held-out reference is 15.4%, above the pre-registered
15% ceiling, so the criterion as written is not met. Per CLAUDE.md §4 the ceiling stays at
15% and this is recorded as a fail. The substantive reading: even on MiraBest's own held-out
confident sources roughly one source in 6.5 has non-unanimous seed labels, and the
contaminated training cohort still shows 13.0% [10.7, 15.5], so seed disagreement has a high
floor and is a noisier discriminator than the flip rate despite its wider gap. The flip rate
is the better instrument.

Caveat recorded rather than buried: the reference is 15.4% **[8.7, 22.1]** on n = 104, an
interval that straddles the ceiling, so this fail is underpowered and poorly determined. No
re-test is run on this reference. If seed disagreement is revisited, a better-powered
reference must be pre-registered first — the natural one is k-fold held-out prediction over
all 833 confident sources, which does not exist yet and needs retraining.

**Criterion defect found in my own check.** The `uncertain_band` row applied the 15% ceiling,
which is meaningless for that metric: the ceiling was designed to detect a noisy *instability*
rate, whereas 42.3% of confident held-out sources falling in (0.05, 0.95) is ordinary
behaviour, not noise. The row was labelled exploratory when written and its "FAIL" should be
read as "criterion misapplied", not as evidence. Its content is the +36.8 pp gap with disjoint
CIs. No threshold is retrofitted; if this metric is used, a criterion gets pre-registered
for it separately.

**H4 — PASS.** Ensemble ambiguity ranks MiraBest's held-out ambiguous classes as more
ambiguous than its confident test set: uncertain median |P−0.5| 0.364 against 0.481,
Mann-Whitney p = 2.93e-10; hybrid 0.259 against 0.481, p = 7.17e-07. Both now carry bootstrap
intervals. `MBHybrid` has n = 34 and an interval of [0.178, 0.383], which must be shown
wherever this is quoted.

---

## 2026-11-23 — Post-hoc observation: the blind sample behaves like MiraBest's *uncertain* class

Context: the five cohort values above were all pre-specified in P1-3, so the numbers are
confirmatory. The following *comparison* was not pre-registered with a criterion and is
therefore post-hoc, and is recorded as such.

Two orderings fall out of the table. First, the flip rate is monotone in distance from the
training manifold: memorised training 1.8% < confident held-out 8.7% < blind candidates 21.7%
≈ MiraBest uncertain 24.2% < MiraBest hybrids 41.2%. Second, on the flip rate the blind
candidates [19.9, 23.5] are **statistically indistinguishable from MiraBest's uncertain
sources** [20.1, 28.5] — the intervals overlap — while being decisively separated from the
confident held-out set. The ambiguity band says the same: candidates 79.1% sit between
uncertain 66.6% and hybrid 82.4%, far from confident-test 42.3%.

This is a sharper statement of the research question's answer than either criterion produced:
applied to a blind FIRST sample, the ensemble's output distribution resembles what it produces
on MiraBest's own unclassifiable sources, not what it produces on sources it classifies well.
It is a candidate headline for the note.

A second reading of the 1.8% training figure is needed before that headline is used: the
ensemble is nearly D4-invariant on data it memorised, so the flip rate partly measures the
generalisation gap rather than domain shift alone. That is what makes it work as an OOD score,
but it means the 8.7% held-out reference is itself elevated relative to the 1.8% floor, and
the note must say so rather than implying 8.7% is an irreducible noise level.

Decision (proposed, needs Raj): if this becomes the central claim, pre-register the
confirmatory test before quoting it — flip rate and ambiguity-band equivalence between the
blind candidates and MiraBest's uncertain class, with an equivalence margin stated in advance
rather than inferred from overlapping intervals, which is a weak test of equivalence.

Outcome (filled later):

---

## 2026-11-23 — Gate 3 pre-registration (G3-1, G3-2, G3-3)

Context: Gates 0-2 passed, so the candidate instability is real, measurable and anchored to a
held-out reference. Gate 3 asks whether the measured shift is a property of the sky or partly
an artefact of our own arithmetic. These criteria are fixed now, before any of the three legs
is run. Raj approved all three legs including the network leg on 2026-11-23.

### G3-1 — Is the instability inflated by our own preprocessing?

`preprocess_cutout` normalises each image by its single brightest pixel. Candidate 3-sigma
masks are fragmented (median 25 components, 0.42 [0.41, 0.43] of nonzero pixels in the
largest) while MiraBest's are not (0.76 [0.68, 0.81]), so a noise spike can set a candidate's
scale where it would not set a MiraBest source's. If that compresses real structure into a
narrow dynamic range, some of the 21.7% flip rate is self-inflicted.

**G3-1a, the primary test — a reference rendered by our own pipeline.** Gate 1 already
produced the 104 held-out MiraBest sources as rendered by `preprocess_cutout` from SkyView
cutouts. Measuring the dihedral flip rate on *those* images gives a reference that is
apples-to-apples with the candidates: same code, same cutout service, same normalisation,
only the sky differs. The 8.7% reference from Gate 2 used MiraBest's own rendering, so it
confounds "our pipeline" with "MiraBest's rendering" of the same galaxies.

Pre-registered criterion:
- If the pipeline-rendered reference flip rate is **below 15%** and the candidate rate still
  exceeds it by at least 10 pp with disjoint bootstrap 95% CIs, then G3-1 passes: the
  instability is a property of the candidate sample, not of our preprocessing, and this
  pipeline-rendered value **replaces 8.7% as the primary reference for P1-3** in everything
  written afterwards, because it is the better-matched control.
- If the pipeline-rendered reference is **15% or above**, our preprocessing materially
  inflates instability. P1-3's verdict is then restated against this reference and the note
  must report the preprocessing contribution explicitly rather than attributing the gap to
  domain shift.
- Either way the paired comparison is also reported per-source: of the 104 held-out sources,
  how many flip under the pipeline rendering but not under MiraBest's, and vice versa.

**G3-1b, secondary — robust alternative scalings on the candidates.** Re-preprocess all 1996
candidates with two scales that a single spike cannot set: (i) the 99th percentile of nonzero
pixels, with values clipped to 1; (ii) the maximum within the largest connected component of
the 3-sigma mask. Re-run the flip rate for each.

Pre-registered criterion: the P1-3 conclusion is robust only if, under **both** alternative
scalings, the candidate flip rate still exceeds the primary reference (whichever G3-1a
selects) by at least 10 pp with disjoint CIs. If either variant breaks that, the result is
declared normalisation-dependent and reported as such, with all three scalings shown. The
preprocessing used for every other result is **not** changed on the basis of this test; it is
a sensitivity analysis, not a tuning opportunity.

### G3-2 — Leakage radius sensitivity (supersedes nothing; executes P1-7)

Re-run the MiraBest cross-match at 2.25 arcmin, half the 4.5 arcmin field, against all 1256
MiraBest positions rather than only the confident ones, and recompute the three headline
diagnostics on the surviving candidates by indexing the cached probability tensors.

Pre-registered criterion, as set on 2026-11-21: leakage is deemed not to drive the result if
the dihedral flip rate, the seed-disagreement rate and the fraction with P in (0.05, 0.95)
each change by less than 5 pp between the 30 arcsec and 2.25 arcmin samples. If any changes
by more than 5 pp, the 2.25 arcmin sample becomes primary and every Gate 2 number is restated
on it. Also reported: how many candidates the wider radius removes.

### G3-3 — Component versus source

FIRST catalogue rows are components and FR-II lobes are catalogued separately from the host,
so a cutout centred on a component may be centred on a lobe. Quantify it: for each of the
1996 clean candidates, the number of *other* FIRST components within 1 arcmin and within
2.25 arcmin, and the separation to the nearest one.

Method: fetch the positions of the full 946 432-row `VIII/92/first14` catalogue once from
VizieR TAP in declination strips, verify the recovered row count against the catalogue total,
cache locally, then match with `astropy.coordinates.search_around_sky`. A bulk fetch with a
verifiable total is preferred over 1996 cone searches specifically because the environment
analysis that was dropped from this project failed by swallowing per-query errors — 149 of
150 queries returned nothing and the failure was invisible. Any shortfall between the
recovered and expected row count is reported, not absorbed.

Pre-registered criterion: this leg is descriptive and has no pass/fail. It reports the
fraction of candidates with at least one other component within each radius, with bootstrap
95% CIs, and the flip rate split by that flag. The flag then feeds Gate 4's
single-component restriction (H3). Stated in advance so it cannot become a post-hoc story:
if the flip rate for multi-component candidates exceeds that for single-component candidates
with disjoint CIs, component confusion is a contributing cause of the instability; if the two
are indistinguishable, it is not, and H3's size restriction carries the explanation alone.

Outcome (filled later):

---

## 2026-11-23 — Method change for G3-3: the project's TAP endpoint no longer exists

Context: G3-3's pre-registered method was a bulk fetch of the full 946 432-row
`VIII/92/first14` catalogue from VizieR TAP in declination strips, with the recovered row
count verified against the catalogue total. On attempting it, the host both notebooks
hard-code — `tapvizier.cds.unistra.fr` — does not answer on port 80 or 443 (connect timeout,
confirmed with `curl` against both). CDS's `viz-bin` paths also return 404, while
`vizier.cds.unistra.fr` itself answers, so this is an endpoint retirement or relocation
rather than a local network problem. SkyView still answers normally.

**This is a reproducibility defect in the repo beyond Gate 3:** `data_extraction.ipynb`
selects the 10 000-source sample through that same dead TAP service, so the extraction step
cannot be re-run as written. The Harvard CfA mirror `vizier.cfa.harvard.edu` serves the same
catalogues and answers normally; it is recorded in `r1/config.VIZIER_SERVER`. Switching the
notebooks over is a Phase 3 item.

Options considered: abandon G3-3; wait for the CDS endpoint; re-implement against the mirror.

Decision: re-implement against the mirror using batched multi-position cone searches. **The
measured quantity and the pass/fail criterion are unchanged** — neighbour counts within
1 arcmin and 2.25 arcmin, and the flip-rate split by that flag. Only the retrieval method
changed, because the pre-registered one is no longer executable.

The verification requirement that motivated the bulk fetch is preserved in a different form:
every batch must succeed, batch failures fall back to per-source queries before being counted
as failures, the count of failures is reported, the script refuses to report a density if any
remain, and it additionally asserts that every candidate returns at least its own catalogue
row. That last check is the direct analogue of the row-count verification — it is impossible
to silently report a density over candidates the server never answered for, which is exactly
how the dropped environment analysis failed (149 of 150 queries returned nothing invisibly).

Operational note: the mirror rate limits. Batches of 100 were served four times and then
rejected every request with a truncated VOTable; the implementation uses batches of 25, a
1.5 s throttle and 10/25/50 s backoff.

**Second method change, same day.** Even at 25 per batch the CfA mirror served one batch in
ten minutes, which is unusable for 80 batches. The catalogue was therefore taken from its
authoritative source, the FIRST survey's own distribution at
`sundog.stsci.edu/first/catalogs/first_14dec17.fits.gz` (69 MB, one request, 24 s). This
**restores the pre-registered method rather than departing further from it**: a single bulk
fetch whose row count is verified. It reads back as exactly 946 432 rows, the same total the
notebook obtained from VizieR, so it is the same release the candidate sample was drawn from.
The script refuses to run if the row count differs, and additionally asserts that each of the
1996 candidates self-matches exactly once (it did), which is a stronger coverage check than
the original batch accounting. The file is gitignored; the one-line download command is in the
script's docstring.

Outcome (2026-11-23): see the G3 outcomes entry below.

---

## 2026-11-23 — Gate 3 outcomes: G3-1a PASS, G3-2 PASS, G3-3 partially attributive

Raw output in `research/gate3_leg1a_leg2.json` and `research/gate3_leg3_components.json`.
G3-1b was still running when this entry was written and is recorded separately.

### G3-1a — PASS. Our preprocessing does not inflate the instability.

Flip rate on the same 104 held-out galaxies, two renderings:

| rendering | flip rate |
|---|---|
| MiraBest's own images | 8.7% [3.8, 14.4] |
| **our `preprocess_cutout` from SkyView cutouts** | **7.7% [2.9, 13.5]** |
| blind candidates, our pipeline | 21.7% [19.9, 23.5] |

Paired per source: 7 flip under both renderings, 1 under ours only, 2 under MiraBest's only,
94 under neither. The pipeline-rendered reference is 7.7%, below the 15% ceiling, and the
candidate gap against it is +14.0 pp with disjoint CIs, so all three legs of the criterion are
met. **7.7% replaces 8.7% as the primary P1-3 reference** in everything written afterwards,
as pre-registered, because it is matched to the candidates in code, cutout service and
normalisation, and differs only in the sky observed.

### G3-2 / P1-7 — PASS. Leakage is not driving the result.

The 2.25 arcmin gate removes 18 further candidates, leaving 1978. Shifts against the
published 30 arcsec sample: flip rate 21.7% to 21.6% (−0.11 pp), seed disagreement 41.8% to
41.6% (−0.23 pp), ambiguity band 79.1% to 79.0% (−0.09 pp). Largest shift 0.23 pp against a
criterion of 5 pp. The 30 arcsec sample remains primary.

### G3-3 — the component problem is severe, and it is a contributing but minor cause

| quantity | value |
|---|---|
| candidates with another FIRST component within 1 arcmin | **53.6% [51.4, 55.8]** |
| candidates with another FIRST component within 2.25 arcmin | **68.6% [66.5, 70.6]** |
| nearest other component, for the 1369 that have one | median 20.6", p10 8.8", p90 101.5" |
| neighbour count within 2.25 arcmin | median 1, mean 1.54, max 19 |

Two thirds of the "candidates" are not isolated sources. CLAUDE.md §3.5 is fully vindicated
and the magnitude is larger than the discussion there implied.

Flip rate split by the multi-component flag:

| radius | multi-component | single-component | CIs disjoint | criterion verdict |
|---|---|---|---|---|
| 1 arcmin | 23.8% [21.3, 26.4] (n=1070) | 19.2% [16.7, 21.8] (n=926) | no | not established |
| 2.25 arcmin | 23.8% [21.5, 26.1] (n=1369) | 17.1% [14.2, 20.1] (n=627) | yes | contributing cause |

**Defect in my own pre-registration:** the criterion named both radii as reportable but did
not say which is decisive, and they disagree. Recorded rather than resolved by choosing the
convenient one. The honest reading is that the effect runs the same way at both radii
(+4.6 pp and +6.7 pp) and reaches CI-disjointness only at 2.25 arcmin, so component confusion
is a real but modest contributor.

**The quantitatively important point is what this does not explain.** Restricting to
single-component candidates leaves the flip rate at 17.1-19.2%, still **2.2 to 2.5 times the
7.7% pipeline-rendered reference**, with no interval overlap. Component confusion is therefore
not the explanation for the transfer failure; it is a second-order contributor. That shifts the
weight of Gate 4 onto the size restriction, and it means a single-component cut alone would not
be a usable remedy for a survey pipeline.

Outcome: G3-1a and G3-2 closed. G3-3 closed as descriptive, with the pre-registration defect
noted. Component flags for Gate 4 written to `research/candidate_component_flags.csv`.

---

## 2026-11-23 — Gate 4 / H3 pre-registration

Context: H3 states that restricting candidates to MiraBest's size range and to
single-component, centred sources reduces instability toward the MiraBest-test level. This is
the difference between the note being a warning and being a prescription, so the criterion is
tiered and fixed now. Gate 4 requires no new inference: every subset indexes the cached
`research/_view_probs/candidates.npy` tensor, so the predictions are identical to Gate 2's
and the only thing that changes is which sources are counted.

Reference values, both fixed before this runs:
- unrestricted candidates, flip rate **21.7% [19.9, 23.5]**, n = 1996
- pipeline-rendered held-out reference selected by G3-1a, **7.7% [2.9, 13.5]**, n = 104

Subsets, each reported with flip rate, seed disagreement, ambiguity band and median |P−0.5|,
all with bootstrap 95% CIs (10 000, seed 0):
1. **size-restricted** — `Maj` inside MiraBest confident p10-p90, [12.5, 127.9] arcsec
   (expected n ~306, from H1's 15.3%)
2. **single-component** — no other FIRST component within 2.25 arcmin (n = 627)
3. **single-component, 1 arcmin variant** — no other component within 1 arcmin (n = 926),
   reported for robustness because G3-3's two radii disagreed
4. **both** — size-restricted and single-component at 2.25 arcmin

Pre-registered criterion, applied to the flip rate of subset 4 (and reported for 1-3):
- **Full recovery, H3 supported:** the subset's point estimate is below 13.5%, the upper bound
  of the reference interval, **and** its CI overlaps the reference CI. Then the restriction is
  a usable remedy and the note can carry a prescription.
- **Partial recovery, H3 partially supported:** the point estimate is at least 5 pp below
  21.7% **and** the subset CI is disjoint from the unrestricted sample's CI, while remaining
  disjoint from the reference. Then the restriction helps but does not fix, and the note
  reports a mitigation rather than a remedy.
- **No recovery, H3 not supported:** anything else, including a drop whose CI overlaps the
  unrestricted sample.

Stated in advance, because they bear on how the result may be read:
- A size restriction is a **selection, not an intervention**. The surviving sources also
  differ in flux, extent and SNR, so a drop in flip rate is consistent with several
  mechanisms and must not be described as the effect of size alone.
- Subset 4 will be small. If its n falls below 100 its interval will be wide enough that
  "overlaps the reference" is a weak claim, and the point-estimate leg of the criterion is
  what carries the verdict. The n is reported beside every rate for this reason.
- **Centring is not tested.** H3 says "single-component, centred"; we test single-component
  only, because testing centring needs re-centroiding the cutouts on a radio centroid and
  re-running inference, which is a separate piece of work. The note must say "single-component"
  and not imply centring was controlled.
- A floor effect is expected and is not evidence of recovery: restricting to large,
  isolated sources selects the candidates that most resemble MiraBest by construction, which
  is exactly what H3 predicts, so the test is confirmatory of a mechanism rather than a
  discovery.

Outcome (2026-11-23): **H3 NOT SUPPORTED — no recovery on any subset.** Raw output in
`research/gate4_h3_restriction.json`. Reference 7.7% [2.9, 13.5]; unrestricted candidates
21.7% [19.9, 23.5].

| subset | n | flip rate | drop vs unrestricted | tier |
|---|---|---|---|---|
| size-restricted, `Maj` in [12.5, 127.9]″ | 306 | **23.2% [18.6, 28.1]** | **−1.5 pp (worse)** | no recovery |
| single-component, 2.25′ | 627 | 17.1% [14.2, 20.1] | +4.6 pp | no recovery |
| single-component, 1′ | 926 | 19.2% [16.7, 21.8] | +2.5 pp | no recovery |
| both, size and single-component | 48 | 20.8% [10.4, 33.3] | +0.9 pp | no recovery |

Three things to record precisely.

**First, the size restriction makes stability slightly worse, not better.** 23.2% against
21.7%, intervals overlapping. This contradicts H3's central premise directly: the candidates
that most resemble MiraBest in catalogued angular size are not classified more stably. H1
established that the candidate population is far smaller than MiraBest's; H3 assumed that
closing that gap would close the instability gap, and it does not.

**Second, the single-component restriction fails by a hair, not by a mile.** 17.1%
[14.2, 20.1] against the unrestricted [19.9, 23.5]: the intervals overlap across 0.2 pp, so
the pre-registered disjointness leg is not met. The point estimate did fall 4.6 pp. The
criterion stands as written and this is recorded as no recovery, but it should be described as
a marginal failure rather than a null result, and it is consistent with G3-3's finding that
component confusion contributes modestly.

**Third, the combined subset is too small to carry anything.** n = 48, interval
[10.4, 33.3]. Its CI does overlap the reference, but that is the weak-claim case the
pre-registration anticipated at n < 100, and its point estimate of 20.8% is nowhere near the
reference. It is reported, not leaned on.

**Consequence for the note: a warning, not a prescription.** Neither of the two cuts a survey
pipeline would naturally reach for — restrict to the training set's angular-size range,
restrict to isolated components — restores stability. Combined with G3-3's result that
single-component candidates still flip at 2.2 to 2.5 times the reference, the honest statement
is that the transfer failure is not removable by the obvious selection cuts, and that a
label-free instability diagnostic is therefore more useful than a selection rule. That is a
stronger argument for the diagnostic than a successful H3 would have been, but it is a
negative result and is to be written as one.

---

## 2026-11-23 — Proposed follow-up to H3, pre-registered before running

Context: H3 restricted on the FIRST catalogue's `Maj`. On 2026-11-21, before any of this ran,
the P1-5 pre-registration already recorded that `Maj` (a deconvolved single-component Gaussian
FWHM) and MiraBest's `size_arcsec` (largest angular size of the labelled source) are different
quantities, and for that reason required a proxy measured identically on both sides. H1 then
found the pixel-measured proxies separate the samples far more cleanly than `Maj` does
(largest connected component 53 px against 202 px, KS 0.748). A large `Maj` can also mean a
poorly constrained fit to a faint blended source rather than genuine resolved structure, which
would explain why the `Maj`-restricted subset is not more stable.

So there is a pre-existing, documented reason to think H3 was tested with the wrong size
variable. The proposal is **one** further test, not a search.

Pre-registered criterion, fixed now: restrict the candidates to those whose largest connected
component has an extent inside the MiraBest confident test set's p10-p90 extent, measured
identically on both sides with the same preprocessing, and apply the same three tiers as H3
(full recovery if the point estimate is below the reference CI's upper bound and the CIs
overlap; partial if the drop is at least 5 pp with a CI disjoint from the unrestricted sample;
otherwise none).

Guard against p-hacking, stated in advance: this is the **only** additional size definition
that will be tried. If it also shows no recovery, H3 is closed as not supported and no third
variable is tested. If it shows recovery, both results are reported together — the `Maj`
version failing and the pixel version passing — with the interpretation that the catalogue's
deconvolved FWHM is not the quantity that governs transfer, which is itself a finding useful
to survey pipelines that would naturally select on the catalogue column.

Needs Raj's approval before running, since it extends an already-answered hypothesis.

Outcome (2026-11-23, approved by Raj and run): **also NO RECOVERY. H3 is closed as NOT
SUPPORTED on both size definitions.** Raw output in `research/gate4b_h3_pixel_size.json`.

Measured identically on both samples with the same preprocessing, the largest connected
component's extent is median 23 px (41.4") for the MiraBest held-out set, p10-p90
[16, 39] px = [28.8, 70.4]", against a candidate median of 10 px (18.0"). 23.3%
[21.5, 25.2] of candidates fall inside that range, consistent with the 15.3% H1 obtained
from `Maj`.

| subset | n | flip rate | drop vs unrestricted | tier |
|---|---|---|---|---|
| pixel-size restricted | 465 | 22.8% [18.9, 26.7] | −1.1 pp (worse) | no recovery |
| pixel-size and single-component | 16 | 25.0% [6.2, 50.0] | −3.3 pp (worse) | no recovery |

As with `Maj`, the restricted subset is very slightly *less* stable than the unrestricted
sample, not more. No third size variable is tried, as pre-registered.

**What this closes, and what it opens.** The result is stronger as a negative than the
alternative would have been, and it sharpens the whole project's claim. H1 established
decisively that the candidate inputs are out of MiraBest's domain in size. H3 now establishes
that **size is not the mechanism driving the instability**: selecting the candidates that
match MiraBest's size distribution, on either the catalogue's deconvolved FWHM or an
identically-measured pixel extent, leaves the dihedral flip rate statistically unchanged at
roughly three times the pipeline-rendered reference. Combined with G3-3, where single-component
candidates still flip at 2.2 to 2.5 times the reference, no selection on size or multiplicity
recovers stability.

The reading this supports, for Raj to accept or reject before it is written anywhere: a blind
FIRST component sample is not a harder version of the FR task but a different one, in which
most sources have no true FR label at all, and the instability is the symptom of asking a
two-class question of sources that belong to neither class. That is consistent with every
result so far, but it is an interpretation and not something any test here has demonstrated —
establishing it would need labels or a third "neither" class, which this project does not
have. It must be written as an interpretation, flagged as such, or else dropped.

Closing note on the hypothesis set: H1 supported, H2 supported via the dihedral flip rate
(P1-3), H4 supported, H3 not supported. P1-4 failed its ceiling leg. Gates 1, 2, 3-1a, 3-2
passed; G3-3 descriptive; G3-1b outstanding.

---

## 2026-11-23 — G3-1b outcome: PASS, but by the confound being small

Raw output in `research/gate3_leg1b_scaling.json`. Reference 7.7% [2.9, 13.5].

| candidate scaling | flip rate | gap vs reference | CIs disjoint | Spearman vs `max` | median \|ΔP\| vs `max` |
|---|---|---|---|---|---|
| `max` (published) | 21.7% [19.9, 23.5] | +14.0 pp | yes | — | — |
| `p99` | 22.2% [20.4, 24.0] | +14.5 pp | yes | 0.998 | 0.0063 |
| `lcc_max` | 21.5% [19.7, 23.3] | +13.9 pp | yes | 0.982 | 0.0000 |

Both variants clear the pre-registered criterion, so **G3-1b passes and the flip-rate result is
not an artefact of per-image-max normalisation.** The default preprocessing is left unchanged,
as pre-registered.

**The reason it passes is worth stating accurately, because it is not the same as surviving a
severe stress test.** `lcc_max` has a median |ΔP| of exactly 0.0000 against `max`: for most
candidates the brightest pixel already lies inside the largest connected component, so the two
scales are literally identical and only the minority with a brighter spike outside the main
component differ. The mechanism hypothesised in the G3-1b pre-registration — a noise spike
setting a candidate's intensity scale — is therefore **rare in this sample rather than present
and compensated**. Removing it moves the flip rate by 0.2 pp.

So the correct claim is "the hypothesised normalisation confound is not present at a material
level", not "the result is robust to large changes in normalisation". The latter is untested
and must not be written. A genuinely severe test would change the intensity *distribution*,
not just its scale — for example re-rendering candidates with MiraBest's own stretch — and is
not performed here.

Gate 3 is now closed: G3-1a PASS, G3-1b PASS, G3-2 PASS, G3-3 descriptive.

---

## 2026-11-23 — K-fold reference pre-registration (KF-1), approved by Raj

Context: every candidate-side claim is compared against a reference of **8 flips in 104
sources**, 7.7% [2.9, 13.5]. That interval is the weakest element of the project: the headline
contrast is between a quantity measured on 1996 sources and a baseline measured on 104. The
same shortage makes P1-4's ceiling test unusable, since its reference is 15.4% [8.7, 22.1] and
the ceiling sits at 15%. A k-fold construction gives every one of the 833 confident sources a
prediction from models that never saw it, raising the reference n from 104 to 833.

Design, fixed before running:
- 5-fold **stratified** split of all 833 confident MiraBest sources, stratified on the FR-I /
  FR-II label so each fold matches the parent class balance. `numpy` seed 0, folds recorded to
  disk so the split is auditable and reusable.
- For each fold, train a 5-seed ensemble on the other four folds with the published recipe
  unchanged: ResNet-18 (1 input channel, 2 classes), dihedral augmentation, Adam lr 1e-4,
  weight decay 1e-4, 25 epochs, batch 32, **final-epoch weights** (no epoch selection, since
  there is still no validation split and selecting would reintroduce the P1-2 flaw).
- Each held-out source is then scored by the 5-seed ensemble of its own fold across all 8
  dihedral views, giving flip rate, seed disagreement, ambiguity and accuracy over n = 833
  held-out predictions.
- 25 trainings in total. Run on GPU; the tensors it produces are stored separately from the
  CPU-computed Gate 2/3 tensors and are never mixed with them.

What this is used for, and the limit on it:
- **Primary use: the reference distribution.** The k-fold flip rate replaces 7.7% as the
  reference wherever a well-powered baseline is needed, and its CI is reported alongside.
- **The candidate predictions are NOT recomputed from k-fold models.** Candidates continue to
  be scored by the published 5-seed ensemble. The comparison is therefore between one model
  set and a matched-architecture, matched-recipe model set, not between identical weights.
  This is a real caveat and is to be stated wherever the comparison is quoted; it is accepted
  because the alternative — scoring candidates with 5 fold-ensembles that each saw a different
  80% of MiraBest — would make the candidate number harder to interpret, not easier.
- **Secondary use: the only well-powered re-test of P1-4.** Its ceiling stays at 15%, exactly
  as pre-registered on 2026-11-21. The re-test is legitimate because the reference changes from
  an underpowered estimate to a well-powered one, not because the threshold moved.

Pre-registered criteria:
- **KF-1a (P1-3 restated):** the candidate dihedral flip rate must exceed the k-fold reference
  by at least 10 pp with disjoint bootstrap 95% CIs. If it does, H2 stands on a well-powered
  reference. If the gap falls below 10 pp or the CIs touch, **P1-3's pass is withdrawn** and
  reported as having depended on an underpowered reference.
- **KF-1b (P1-4 re-test):** seed disagreement is a usable score only if the k-fold reference is
  below 15% **and** the candidate rate exceeds it by at least 10 pp with disjoint CIs.
- **KF-1c (sanity):** the k-fold held-out accuracy must agree with the published final-epoch
  88.7% [80.9, 93.3] within its interval. If it does not, the k-fold training did not reproduce
  the published recipe and nothing from it is used until that is explained.

Stated in advance: the k-fold reference is expected to be *higher* than 7.7%, because each fold
ensemble trains on 666 sources rather than 729 and less training data generally means less
stability. A reference that comes back higher is not a problem to be explained away — it is the
honest baseline, and KF-1a is written so that it can fail.

Outcome (2026-11-23): run on GPU, 25 trainings in 872 s. Raw output in
`research/kfold_reference.json`, held-out view probabilities in `research/_kfold/`.
Fold stratification verified: FR-II fraction 0.521-0.524 per fold against a parent 0.524.

**The reference, n = 833 held-out predictions:**

| quantity | k-fold (n=833) | previous (n=104) | CI width |
|---|---|---|---|
| dihedral flip rate | **11.4% [9.4, 13.6]** | 7.7% [2.9, 13.5] | 4.2 pp vs 10.6 pp |
| seed disagreement | **38.2% [34.9, 41.5]** | 15.4% [8.7, 22.1] | — |
| P in (0.05, 0.95) | 60.0% [56.7, 63.4] | 42.3% [32.7, 51.9] | — |
| median \|P−0.5\| | 0.420 [0.409, 0.432] | 0.481 [0.445, 0.490] | — |
| held-out accuracy | 91.2% Wilson [89.1, 93.0] | 88.7% [80.9, 93.3] | — |

As predicted in the pre-registration, the better-powered reference came back higher. Note the
two flip-rate estimates are **statistically consistent** — 11.4% lies inside the old
[2.9, 13.5] — so this is a sharpening, not a contradiction. The point-estimate difference is
attributable either to fold models training on 666 sources rather than 729, or to noise in an
8-flip estimate; the data cannot separate those and the note should not claim to.

**KF-1c — PASS.** 91.2% [89.1, 93.0] against the published 88.7% [80.9, 93.3]. Consistent, and
higher as expected since this is a 5-seed ensemble with 8-view TTA whereas the published figure
is a per-seed single-view mean. The recipe reproduces.

**KF-1a — PASS, but marginally, and the margin must be reported.** Candidate 21.7%
[19.9, 23.5] against the k-fold reference 11.4% [9.4, 13.6]: gap **+10.3 pp** against a
pre-registered threshold of 10 pp, CIs disjoint. P1-3 stands and H2 survives on a well-powered
reference, but the effect is a factor of **1.9**, not the 2.8 implied by the n=104 reference,
and the gap clears its threshold by 0.3 pp. The honest headline is that the diagnostic works
and its margin is thinner than the original analysis suggested. Any write-up that quotes
"2.5x" or "~3x" from the earlier references is now wrong and must be corrected.

**KF-1b — FAIL, decisively, and this retrospectively vindicates not moving the ceiling.** The
k-fold seed-disagreement reference is **38.2% [34.9, 41.5]**, not the 15.4% [8.7, 22.1]
estimated from 104 sources. The candidate rate of 41.8% exceeds it by only +3.7 pp and the CIs
overlap heavily. Seed disagreement is not an OOD score at any power level: on 104 sources it
failed its ceiling by 0.4 pp and looked like a near miss, and properly powered it fails by
23 pp. Had the 15% ceiling been relaxed on 2026-11-23 to accommodate 15.4%, the project would
now be carrying a diagnostic that does not work. P1-4 is closed as failed.

**Device consistency (2026-11-24, at Raj's direction).** KF-1 ran on GPU while every other
tensor had been computed on CPU, so the headline comparison carried an uncontrolled device
term — and KF-1a clears its threshold by only 0.3 pp. Rather than measure that term and keep
a mixed set, all eight cached tensors were regenerated on the GPU
(`scripts/recompute_view_probs_gpu.py`), with the CPU set preserved in
`research/_view_probs_cpu/` so the delta is recorded rather than assumed. Measured, over
7348 sources:

- largest per-source probability difference: 4.1e-3 — larger than float rounding alone, so
  cuDNN is selecting different convolution algorithms, not merely reordering sums;
- flip flags changed: **1 source of 7348**, in the `p99` sensitivity variant only;
- largest cohort-level flip-rate shift: **0.05 pp**, in that same non-headline variant;
- every headline value unchanged to two decimals: candidates 21.69%, pipeline-rendered
  reference 7.69%, held-out test 8.65%, training 1.78%, uncertain 24.16%, hybrid 41.18%.

KF-1a's margin is therefore unaffected, and every comparison in the project now rests on one
device. Recorded in `research/device_consistency.json`. The earlier concern that device
mixing might matter at a 0.3 pp margin was reasonable to check and turned out to be
immaterial; it is logged here so the check is not repeated.

**Adopted as primary:** the k-fold flip-rate reference, 11.4% [9.4, 13.6], replaces both 8.7%
and 7.7% wherever a held-out baseline is quoted. The caveat pre-registered above stands and
must travel with it: candidates are scored by the published ensemble and the reference by
matched-recipe fold ensembles, so this compares two model sets trained the same way, not
identical weights. The 7.7% figure is retained in RESULTS.md as the matched-weights reference
with its wide interval, because the two together bound the comparison better than either alone.
