# RESULTS

Every number that may appear in the paper lives here with its n, its uncertainty, the data
split it was computed on, and what produced it. A number without an uncertainty is not a
result. Status column: **verified** = recomputed this session; **stored** = taken from
outputs saved in `main.ipynb`, not yet reproduced; **contaminated** = computed wholly or
partly on training data; **superseded** = kept visible but replaced; **pending** = criterion
pre-registered, not yet run.

Last updated: 2026-11-24

**Device provenance.** As of 2026-11-24 every cached view-probability tensor is computed on
the GPU, so no comparison in this file mixes devices. The CPU set is preserved in
`research/_view_probs_cpu/` and the measured difference is in
`research/device_consistency.json`: largest per-source probability difference 4.1e-3, **one**
flip flag changed out of 7348 sources (in the `p99` sensitivity variant only), largest
cohort-level shift 0.05 pp, and every headline value unchanged to two decimals.

## Sample sizes

| Quantity | Value | 95% CI / spread | n | Data split | Produced by | Status |
|---|---|---|---|---|---|---|
| FIRST catalogue rows sampled | 10 000 | — | 946 432 total | 1-in-94 by `recno` | `data_extraction.ipynb` cell 4 | stored |
| Extended candidates after morphology cuts | 2 044 | — | of 10 000 | blind FIRST | `main.ipynb` cell 7 | stored |
| Clean candidates after quality gate | 1 996 | — | of 2 044 | blind FIRST | `main.ipynb` cell 10 | verified (CSV read) |
| — excluded, NaN pixels | 20 | — | — | — | `main.ipynb` cell 10 | stored |
| — excluded, within 30″ of MiraBest | 28 | — | — | — | `main.ipynb` cell 10 | stored |
| MiraBest confident, training | 729 | — | — | MiraBest train | `MBFRConfident` | stored |
| MiraBest confident, held-out | 104 | — | — | MiraBest test | `MBFRConfident` | stored |
| `MBFRUncertain` (never trained on) | 389 | — | — | MiraBest train+test | `main.ipynb` cell 31 | stored |
| `MBHybrid` (never trained on) | 34 | — | — | MiraBest train+test | `main.ipynb` cell 31 | stored |

## Classifier performance

| Quantity | Value | 95% CI / spread | n | Data split | Produced by | Status |
|---|---|---|---|---|---|---|
| Ensemble accuracy, final epoch | 88.7% | Wilson [80.9, 93.3]%; seed sd 1.3 pp | 104 | MiraBest test | `main.ipynb` cell 24; CI computed this session | verified (CI), stored (accuracy) |
| Ensemble accuracy, best epoch | 90.0% | seed sd 0.5 pp | 104 | MiraBest test | `main.ipynb` cell 24 | **superseded — selected on the test set, not quotable** |
| Single baseline accuracy, best epoch | 88.46% | — | 104 | MiraBest test | `main.ipynb` cell 22 | **superseded — selected on the test set, not quotable** |
| Per-seed final-epoch accuracies | 88.5, 86.5, 90.4, 89.4, 88.5 % | range 86.5–90.4% | 104 each | MiraBest test | `main.ipynb` cell 24 | stored |

## T1 — input-domain match

| Quantity | Value | 95% CI / spread | n | Data split | Produced by | Status |
|---|---|---|---|---|---|---|
| Median nonzero pixel, MiraBest | 0.1000 | [p10 0.0353, p90 0.2278] | 729 | MiraBest train | `main.ipynb` cell 12 | stored |
| Median nonzero pixel, candidates (linear) | 0.2089 | — | 1 996 | blind FIRST | `main.ipynb` cell 12 | stored |
| KS, candidates vs MiraBest (linear) | 0.380 | p = 2.3e-69 | 1 996 vs 729 | — | `main.ipynb` cell 12 | stored |
| KS, candidates vs MiraBest (asinh) | 0.965 | p ≈ 0 | 1 996 vs 729 | — | `main.ipynb` cell 12 | stored |
| Median nonzero pixels/image, MiraBest | 312 | — | 729 | MiraBest train | `main.ipynb` cell 12 | stored |
| Median nonzero pixels/image, candidates | 123 | — | 1 996 | blind FIRST | `main.ipynb` cell 12 | stored |
| "T1 verdict: PASS" | — | — | — | — | `main.ipynb` cell 12 | **withdrawn — criterion could not fail; see DECISIONS.md 2026-11-21** |

## T2 — paired pipeline validation

### Gate 1 / P1-1 — held-out result (primary)

Produced by `scripts/gate1_paired_pipeline.py`, 2026-11-23. Bootstrap 10 000, seed 0.

| Quantity | Value | 95% CI | n | Data split | Criterion | Status |
|---|---|---|---|---|---|---|
| **Native-vs-pipeline label agreement** | **99.0%** | bootstrap [97.1, 100.0] | 104 | MiraBest test | CI low ≥ 95% | **verified — met** |
| **Median \|P_native − P_pipeline\|** | **0.0037** | bootstrap [0.0013, 0.0073] | 104 | MiraBest test | CI high < 0.05 | **verified — met** |
| Spearman rho, native vs pipeline | 0.987 | bootstrap [0.973, 0.992] | 104 | MiraBest test | — | verified |
| Ensemble accuracy, native images | 88.5% | Wilson [80.9, 93.3] | 104 | MiraBest test | — | verified — reproduces the published 88.7% |
| Ensemble accuracy, pipeline images | 89.4% | Wilson [82.0, 94.0] | 104 | MiraBest test | — | verified |
| Fraction of P_native saturated (<0.02 or >0.98) | 55.8% | none | 104 | MiraBest test | — | verified |

**Gate 1 verdict: PASS.** `preprocess_cutout` applied to a SkyView cutout returns
essentially the same classification as MiraBest's own rendering of the same galaxy, on
sources never trained on. Candidate instability cannot be attributed to our preprocessing,
so the domain-shift question is answerable.

### Superseded: the notebook's n = 833 T2

| Quantity | Value | n | Data split | Produced by | Status |
|---|---|---|---|---|---|
| Native-vs-pipeline label agreement | 98.0% | 833 | 729 train + 104 test | `main.ipynb` cell 27 | **withdrawn — mis-paired** |
| Median \|P_native − P_pipeline\| | 0.024 | 833 | 729 train + 104 test | `main.ipynb` cell 27 | withdrawn — mis-paired |
| Spearman rho, native vs pipeline | 0.81 | 833 | 729 train + 104 test | `main.ipynb` cell 27 | withdrawn — mis-paired |
| Ensemble accuracy, native images | 98.1% | 833 | 729 train + 104 test | `main.ipynb` cell 27 | withdrawn — mis-paired |
| Ensemble accuracy, pipeline images | 97.2% | 833 | 729 train + 104 test | `main.ipynb` cell 27 | withdrawn — mis-paired |
| Training-side paired comparison | — | 729 | MiraBest train | — | **dropped, not recoverable** |

These are withdrawn rather than relabelled contaminated. The paired cutouts were saved as
`MB_<split>_<batch_index>.fits`, and `batch_index` counts within a batch, so the 729
confident training sources collapse onto 107 filenames: **625 of the 833 sources were
compared against a cutout of a different galaxy.** The 104 test sources come from a single
batch and were paired correctly, which is why the Gate 1 table above is valid. Full account
in DECISIONS.md, 2026-11-23.

The earlier note in this file attributing the low rho = 0.81 to saturated predictions on
memorised images was wrong: the correctly-paired held-out rho is 0.987, higher than 0.81,
so saturation was never the cause. Mis-pairing was.

## Candidate predictions and instability

| Quantity | Value | 95% CI / spread | n | Data split | Produced by | Status |
|---|---|---|---|---|---|---|
### Gate 5 / KF-1 — the primary held-out reference (n = 833)

Produced by `scripts/kfold_reference.py` on GPU, 2026-11-23. 5-fold stratified × 5 seeds ×
25 epochs = 25 trainings in 872 s; every one of the 833 confident sources scored by models
that never saw it. **This is the primary reference for all held-out comparisons.**

| Quantity | k-fold (n = 833) | Previous (n = 104) | Status |
|---|---|---|---|
| **Dihedral flip rate** | **11.4% [9.4, 13.6]** | 7.7% [2.9, 13.5] | **verified — primary reference** |
| Seed disagreement | 38.2% [34.9, 41.5] | 15.4% [8.7, 22.1] | verified |
| Frac P in (0.05, 0.95) | 60.0% [56.7, 63.4] | 42.3% [32.7, 51.9] | verified |
| Median \|P−0.5\| | 0.420 [0.409, 0.432] | 0.481 [0.445, 0.490] | verified |
| Held-out accuracy | 91.2% Wilson [89.1, 93.0] | 88.7% [80.9, 93.3] | verified — recipe reproduces |

CI width on the flip rate falls from 10.6 pp to 4.2 pp. The two flip-rate estimates are
**statistically consistent** (11.4% lies inside [2.9, 13.5]), so this sharpens rather than
contradicts; whether the point-estimate shift is due to fold models training on 666 sources
instead of 729, or to noise in an 8-flip estimate, cannot be separated from these data.

| Criterion | Candidate | Reference | Gap | CIs disjoint | Verdict |
|---|---|---|---|---|---|
| **KF-1a (P1-3 restated)** | 21.7% [19.9, 23.5] | 11.4% [9.4, 13.6] | **+10.3 pp** | yes | **PASS — marginal** |
| **KF-1b (P1-4 re-test)** | 41.8% [39.6, 44.0] | 38.2% [34.9, 41.5] | +3.7 pp | **no** | **FAIL** |
| KF-1c (recipe sanity) | — | 91.2% vs published 88.7% | — | — | PASS |

**KF-1a passes by 0.3 pp.** H2 survives on a well-powered reference, but the effect is a
factor of **1.9**, not the 2.8 the n=104 reference implied. Any text quoting "2.5×" or "~3×"
from the earlier references is wrong and must be corrected.

**KF-1b fails decisively, which vindicates not having moved the 15% ceiling.** The true
seed-disagreement baseline is 38.2%, not 15.4%: on 104 sources P1-4 failed its ceiling by
0.4 pp and looked like a near miss; properly powered it fails by 23 pp and the candidate gap
collapses from +26.4 pp to +3.7 pp with overlapping CIs. **Seed disagreement is not an OOD
score at any power level.** Had the ceiling been relaxed to accommodate 15.4%, the project
would be carrying a diagnostic that does not work.

Caveat that travels with every use of this reference: candidates are scored by the published
ensemble and the reference by matched-recipe fold ensembles, so this compares two model sets
trained identically, not identical weights. The 7.7% matched-weights reference is retained
above; the two together bound the comparison better than either alone.

### Gate 2 / P1-3, P1-4, H4 — all five cohorts with intervals

Produced by `scripts/gate2_instability.py`, 2026-11-23. Bootstrap 10 000, seed 0. All
intervals are bootstrap 95%. Definitions: a source **flips** if the 5-model ensemble-mean
label is not identical across all 8 dihedral views; seeds **disagree** if the 5 single-seed
identity-view labels are not unanimous.

| Cohort | n | Dihedral flip rate | Seed disagreement | Median \|P−0.5\| | Frac P in (0.05, 0.95) | Status |
|---|---|---|---|---|---|---|
| MiraBest confident **train** | 729 | 1.8% [0.8, 2.9] | 13.0% [10.7, 15.5] | 0.478 [0.473, 0.482] | 33.1% [29.8, 36.6] | verified — **contaminated** (memorised) |
| MiraBest confident **test** (reference) | 104 | **8.7% [3.8, 14.4]** | 15.4% [8.7, 22.1] | 0.481 [0.445, 0.490] | 42.3% [32.7, 51.9] | verified |
| **Blind FIRST candidates** | 1996 | **21.7% [19.9, 23.5]** | 41.8% [39.6, 44.0] | 0.326 [0.314, 0.337] | 79.1% [77.3, 80.9] | verified |
| MiraBest **uncertain** | 389 | 24.2% [20.1, 28.5] | 39.3% [34.7, 44.2] | 0.364 [0.339, 0.389] | 66.6% [62.0, 71.2] | verified — never trained on |
| MiraBest **hybrid** | 34 | 41.2% [23.5, 58.8] | 41.2% [23.5, 58.8] | 0.259 [0.178, 0.383] | 82.4% [67.6, 94.1] | verified — never trained on |

### Criterion verdicts

| Test | Candidate | Reference (MiraBest test) | Gap | CIs disjoint | Ref ≤ 15% | Verdict |
|---|---|---|---|---|---|---|
| **P1-3 dihedral flip rate** | 21.7% | 8.7% | +13.0 pp | yes | yes | **PASS** |
| P1-4 seed disagreement | 41.8% | 15.4% | +26.4 pp | yes | **no (15.4%)** | **FAIL** |
| Ambiguity band (exploratory) | 79.1% | 42.3% | +36.8 pp | yes | n/a | criterion misapplied — see note |

**P1-3 passes**, so the dihedral flip rate is a usable label-free OOD score and the
previously uninterpretable 21.7% is anchored at **2.5x the held-out reference of 8.7%**.
H2 is supported.

**P1-4 fails** on its third leg only; the 15% ceiling is not moved (CLAUDE.md §4). Seed
disagreement has a high floor — 13.0% even on memorised training data — so despite the wider
gap it discriminates less cleanly than the flip rate. The fail is underpowered: the reference
interval [8.7, 22.1] on n = 104 straddles the ceiling.

The ambiguity-band row's "FAIL" is an error in my own check, not evidence: the 15% ceiling
was designed for instability rates and is meaningless for a band-occupancy fraction, where
42.3% on confident held-out sources is ordinary. Its content is the +36.8 pp gap.

### H4 — ambiguity ranks MiraBest's own ambiguous classes correctly

| Comparison | Median \|P−0.5\| | vs confident test | Mann-Whitney p | Verdict |
|---|---|---|---|---|
| `MBFRUncertain` (n = 389) | 0.364 [0.339, 0.389] | 0.481 [0.445, 0.490] | 2.93e-10 | more ambiguous — **PASS** |
| `MBHybrid` (n = 34) | 0.259 [0.178, 0.383] | 0.481 [0.445, 0.490] | 7.17e-07 | more ambiguous — **PASS** |

`MBHybrid`'s n = 34 gives a wide interval that must be shown wherever this is quoted.

### Post-hoc observation (not pre-registered — see DECISIONS.md)

The flip rate is monotone in distance from the training manifold: memorised training 1.8% <
confident held-out 8.7% < blind candidates 21.7% ≈ MiraBest uncertain 24.2% < hybrids 41.2%.
On the flip rate the blind candidates [19.9, 23.5] are **statistically indistinguishable from
MiraBest's uncertain class** [20.1, 28.5] while decisively separated from the confident
held-out set. The ambiguity band agrees: candidates 79.1% sit between uncertain 66.6% and
hybrid 82.4%, far from confident-test 42.3%.

The cohort values are confirmatory (pre-specified in P1-3); this comparison and its reading
are post-hoc. Overlapping intervals are a weak test of equivalence, so a confirmatory test
with an equivalence margin stated in advance is required before this is quoted as a result.

Caveat for interpretation: the ensemble is nearly D4-invariant on memorised data (1.8%), so
the flip rate partly measures the generalisation gap, not domain shift alone. That is why it
works as an OOD score, but it means 8.7% is not an irreducible noise floor.

### Gate 3 — confound checks

Produced by `scripts/gate3_leg1a_leg2.py` and `scripts/gate3_leg3_components.py`, 2026-11-23.

**G3-1a — PASS. The preprocessing does not inflate the instability.** Flip rate on the same
104 held-out galaxies under two renderings:

| Rendering | Flip rate | n | Status |
|---|---|---|---|
| MiraBest's own images | 8.7% [3.8, 14.4] | 104 | verified |
| **Our `preprocess_cutout` from SkyView cutouts** | **7.7% [2.9, 13.5]** | 104 | **verified — now the primary P1-3 reference** |
| Blind candidates, our pipeline | 21.7% [19.9, 23.5] | 1996 | verified |

Paired per source: 7 flip under both renderings, 1 under ours only, 2 under MiraBest's only,
94 under neither. Candidate gap against the matched reference: **+14.0 pp**, CIs disjoint.
All later comparisons use 7.7% as the reference, as pre-registered.

**G3-1b — PASS, but by the confound being small rather than by surviving a severe test.**

| Candidate scaling | Flip rate | Gap vs 7.7% reference | CIs disjoint | Spearman vs `max` | median \|ΔP\| vs `max` |
|---|---|---|---|---|---|
| `max` (published) | 21.7% [19.9, 23.5] | +14.0 pp | yes | — | — |
| `p99` | 22.2% [20.4, 24.0] | +14.6 pp | yes | 0.998 | 0.0063 |
| `lcc_max` | 21.5% [19.7, 23.3] | +13.9 pp | yes | 0.982 | **0.0000** |

Both variants clear the criterion, so the flip-rate result is not an artefact of per-image-max
normalisation, and the default preprocessing is left unchanged. But `lcc_max`'s median |ΔP| of
exactly zero shows why: for most candidates the brightest pixel already lies inside the
largest connected component, so the hypothesised mechanism — a noise spike setting the
intensity scale — is **rare in this sample** rather than present and compensated. Removing it
moves the flip rate by 0.2 pp. The defensible claim is "this confound is not present at a
material level", not "the result is robust to large changes in normalisation", which is
untested: a severe test would change the intensity *distribution* (e.g. re-render candidates
with MiraBest's own stretch), not just its scale.

**G3-2 / P1-7 — PASS. Leakage is not driving the result.** The 2.25′ gate removes 18 further
candidates (1996 → 1978). Flip rate 21.7% → 21.6% (−0.11 pp); seed disagreement 41.8% →
41.6% (−0.23 pp); ambiguity band 79.1% → 79.0% (−0.09 pp). Largest shift 0.23 pp against a
5 pp criterion. The 30″ sample remains primary.

**G3-3 — the component problem is severe but is a second-order cause.**

| Quantity | Value | n | Status |
|---|---|---|---|
| Another FIRST component within 1′ | **53.6% [51.4, 55.8]** | 1996 | verified |
| Another FIRST component within 2.25′ | **68.6% [66.5, 70.6]** | 1996 | verified |
| Nearest other component (of the 1369 with one) | median 20.6″, p10 8.8″, p90 101.5″ | 1369 | verified |
| Neighbour count within 2.25′ | median 1, mean 1.54, max 19 | 1996 | verified |

Flip rate split by multiplicity:

| Radius | Multi-component | Single-component | CIs disjoint | Criterion |
|---|---|---|---|---|
| 1′ | 23.8% [21.3, 26.4] (n=1070) | 19.2% [16.7, 21.8] (n=926) | no | not established |
| 2.25′ | 23.8% [21.5, 26.1] (n=1369) | 17.1% [14.2, 20.1] (n=627) | yes | contributing cause |

Two thirds of the candidates are not isolated sources. The pre-registration named both radii
as reportable without saying which is decisive and they disagree — recorded in DECISIONS.md as
a defect rather than resolved by choosing the convenient one. Critically, **single-component
candidates still flip at 17.1–19.2%, i.e. 2.2–2.5× the 7.7% reference with no interval
overlap**, so component confusion is not the explanation.

Catalogue provenance: `first_14dec17.fits.gz` from `sundog.stsci.edu`, read back as exactly
946 432 rows — the same total the notebook obtained from VizieR, verified before matching.

### Gate 4 / H3 — restriction does not recover stability

Produced by `scripts/gate4_h3_restriction.py` and `scripts/gate4b_h3_pixel_size.py`. Every
subset indexes the cached Gate 2 tensor, so per-source predictions are identical to Gate 2's.
Reference 7.7% [2.9, 13.5]; unrestricted 21.7% [19.9, 23.5].

| Subset | n | Flip rate | vs unrestricted | Tier |
|---|---|---|---|---|
| `Maj` in MiraBest p10–p90 [12.5, 127.9]″ | 306 | 23.2% [18.6, 28.1] | −1.5 pp (worse) | no recovery |
| Single-component, 2.25′ | 627 | 17.1% [14.2, 20.1] | +4.6 pp | no recovery (marginal) |
| Single-component, 1′ | 926 | 19.2% [16.7, 21.8] | +2.5 pp | no recovery |
| `Maj`-size and single-component | 48 | 20.8% [10.4, 33.3] | +0.9 pp | no recovery |
| **Pixel extent in MiraBest p10–p90 [16, 39] px** | 465 | **22.8% [18.9, 26.7]** | −1.1 pp (worse) | no recovery |
| Pixel-size and single-component | 16 | 25.0% [6.2, 50.0] | −3.3 pp (worse) | no recovery |

**H3 verdict: NOT SUPPORTED, on both size definitions.** The single-component restriction
fails by 0.2 pp of interval overlap — a marginal failure, not a null. Everything else is flat
or slightly worse than the unrestricted sample.

Supporting measurement: the largest connected component's extent, measured identically on both
samples, is median 23 px (41.4″) for MiraBest held-out, p10–p90 [16, 39] px = [28.8, 70.4]″,
against a candidate median of 10 px (18.0″). 23.3% [21.5, 25.2] of candidates fall inside that
range, consistent with H1's 15.3% from `Maj`. The 41.4″ reproduces MiraBest's catalogued
median `size_arcsec` of 43.0″, which calibrates the proxy.

**Interpretation of the hypothesis set as a whole** (an interpretation, not a demonstrated
result — flagged as such per DECISIONS.md): H1 shows the inputs are decisively out of domain
in size; H2 shows the outputs are unstable at ~3× the matched reference; H3 shows that
selecting on size or multiplicity does not recover stability. So size is not the mechanism.
The reading consistent with all of it is that a blind FIRST component sample is a different
task rather than a harder one, most of its sources having no true FR label — but establishing
that needs labels or a third class this project does not have.

### Superseded candidate-side numbers

| Quantity | Value | n | Produced by | Status |
|---|---|---|---|---|
| Predicted FR-I / FR-II | 1 102 / 894 | 1 996 | `main.ipynb` cell 29 | stored |
| Dihedral flip rate, candidates | 21.7% (433) | 1 996 | `main.ipynb` cell 31 | superseded by the Gate 2 table (same value, now with CI and a control) |
| Per-seed bridge overlap (150 of 1 996) | median 19 | 1 996 | `main.ipynb` cell 31 | stored; chance 11 |
| "150 of 150 bridge sources flip" | — | 150 | `main.ipynb` cell 31 | **withdrawn — tautological; bridge is defined by P ≈ 0.5** |

## Candidate angular sizes (H1)

| Quantity | Value | 95% CI / spread | n | Data split | Produced by | Status |
|---|---|---|---|---|---|---|
| Candidate `Maj`, median | 8.46″ | p25 7.02″, p75 10.75″ | 1 996 | blind FIRST | computed this session from `FIRST_clean_candidates.csv` | verified |
| Candidate `Maj`, p10 / p90 | 6.42″ / 14.37″ | min 6.00″, max 66.48″ | 1 996 | blind FIRST | same | verified |
| Fraction with `Maj` ≤ 10″ | 69.2% | none | 1 996 | blind FIRST | same | verified |
| Fraction with `Maj` ≤ 2× FIRST beam (10.8″) | 75.5% | none | 1 996 | blind FIRST | same | verified |
| Median `Fint`/`Fpeak` | 2.164 | — | 1 996 | blind FIRST | same | verified |
| Median SNR (`Fpeak`/`Rms`) | 11.6 | — | 1 996 | blind FIRST | same | verified |
| MiraBest confident `size_arcsec`, median | 43.0″ | p10 12.5″, p90 127.9″; range 6.3–269.4″ | 833 | MiraBest train+test | P1-5, this session | verified |
| MiraBest confident `size_arcsec`, test only | 37.8″ | p10 12.3″, p90 133.3″ | 104 | MiraBest test | P1-5, this session | verified |
| MiraBest confident redshift, median | z = 0.196 | p10 0.086, p90 0.376 | 833 | MiraBest train+test | P1-5, this session | verified |
| **Fraction of candidates inside MiraBest's p10–p90 size range** | **15.3%** | **bootstrap [13.8, 16.9]%** | 1 996 | blind FIRST vs MiraBest confident | P1-5, this session | **verified — criterion was < 50%, H1 leg (a) supported** |
| Fraction of candidates inside MiraBest's full size range | 93.2% | bootstrap [92.1, 94.3]% | 1 996 | vs full confident (range 6.3–269.4″) | P1-5, this session | verified — range is so wide it is uninformative |
| Fraction inside the test-only full range (10.0–269.4″) | 30.9% | bootstrap [28.9, 33.0]% | 1 996 | blind FIRST | P1-5, this session | verified |

### H1 leg (b): structure measured identically on both sides

Same `preprocess_cutout(mode="linear")` output on both sides; candidates n = 1 996, MiraBest
confident test n = 104. Medians with bootstrap 95% CIs.

| Statistic | Candidates | MiraBest test | KS (p) | Status |
|---|---|---|---|---|
| **Nonzero pixels per image** | **123 [117, 129]** | **294.5 [265.5, 340.0]** | **0.683 (5.9e-46)** | **verified — criterion KS > 0.30, H1 leg (b) supported** |
| Largest connected component (px) | 53 [50, 56] | 202.5 [181, 227.5] | 0.748 (4.8e-57) | exploratory — see DECISIONS.md 2026-11-23 |
| Extent of largest component | 10 px [10, 11] = 18.0″ | 23 px [21, 26] = 41.4″ | 0.693 (1.5e-47) | exploratory; 41.4″ agrees with MiraBest's catalogued 43.0″, which calibrates the proxy |
| Fraction of nonzero px in largest component | 0.42 [0.41, 0.43] | 0.76 [0.68, 0.81] | 0.499 (3.3e-23) | exploratory |
| Connected components per mask | 25 [25, 25] | 20 [19, 21.5] | 0.323 (1.1e-09) | exploratory |
| Maximum extent of whole 3-sigma mask | 143 px | 128 px | 0.569 (1.1e-30) | **withdrawn — measures the noise floor, wrong sign; see DECISIONS.md** |

H1 verdict: **supported**, on the catalogue sizes and on the pixel data independently. The
blind FIRST candidates carry roughly a quarter of MiraBest's resolved structure (123 vs 294
nonzero pixels; largest component 53 vs 202 px), and MiraBest's size p10 (12.5″) is above
the candidate p75 (10.8″). The candidate sample is not a harder version of MiraBest; it is a
different population of barely-resolved components.

## Out of scope

The SDSS environmental-density results in `main.ipynb` cells 34–35 (Bridge/FR-I/FR-II
neighbour counts, Mann-Whitney p-values) are **dropped** per CLAUDE.md §2 and are not
recorded here as results. The cohorts differ by a factor ~4 in median `Fint` (3.98, 9.28,
2.19 mJy), 27–32% of queries failed, and there are no redshifts, so the measurement is a
confound rather than a result.
