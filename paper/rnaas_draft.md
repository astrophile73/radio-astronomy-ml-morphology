# A Label-Free Reliability Test for FR-I/FR-II Classification in Blind Radio Surveys

*Draft. RNAAS limit is 1,500 words inclusive of title, headers, captions and references, with 150 reserved for the abstract — see research/DECISIONS.md, 2026-11-24. Budget: abstract 150, body ~1,100, caption ~70, references ~130.*

**Status: all sections drafted as prose. Section headers below are scaffolding for review
and should NOT appear in the submitted note — RNAAS runs as continuous prose and headers
count against the word limit.**

---

## Abstract (target 150)

Morphological classifiers trained on curated radio-galaxy samples are increasingly applied to blind survey catalogues, where no labels exist to check them. We apply a five-seed ResNet-18 ensemble trained on MiraBest to 1996 extended components from the FIRST catalogue,
and ask which label-free diagnostics detect a failed transfer. The candidate inputs are far outside the training domain, with only 15% falling inside MiraBest's angular-size range. The predicted class changes under a rotation or mirror for 21.7% (19.9–23.5%) of candidates, compared with 11.4% (9.4–13.6%) for MiraBest sources held out under five-fold cross-validation. Restricting the candidates to MiraBest's size range, or to isolated components, does not recover stability, so selection cannot repair the transfer. Ensemble
seed disagreement fails as a diagnostic once it is referenced against a properly powered baseline. We recommend dihedral instability as a per-source reliability score for survey pipelines.

---

## §1 — The problem (target ~200)

The Evolutionary Map of the Universe is expected to catalogue about 70 million radio galaxies (Norris et al. 2011), far more than can be inspected by eye, and convolutional neural networks are now a standard tool for classifying them (Aniyan & Thorat 2017). Fanaroff–Riley type separates sources by whether their emission peaks near the core or the 
edges, a division that correlates with radio luminosity (Fanaroff & Riley 1974), so FR
demographics at survey scale bear on jet power and environment. That use depends on the
classifications being meaningful for the sources the classifier is actually given.

Training sets do not look like survey catalogues. Labelled sets such as MiraBest (Porter &
Scaife 2023) are curated: the sources are extended, centred on their host, and were chosen
because a human could classify them confidently. A blind catalogue is none of these things.
Its rows are components rather than whole sources, most are barely resolved, and many are
not FR galaxies at all. A classifier still returns a confident-looking probability for
every row.

Standard validation does not reveal this. Held-out accuracy is measured on sources from the
same curated distribution, so it says nothing about behaviour on sources unlike them, and
blind samples have no labels at all. A survey pipeline instead needs a diagnostic that can
be computed without labels, for each source, and that flags when an output should not be
trusted. We test two such diagnostics, and whether simple selection cuts can fix the problem
instead.

---

## §2 — Data and method (target ~280)

We selected 1996 extended components from the FIRST catalogue (Becker et al. 1995; Helfand
et al. 2015), taking every 94th of the 946,432 entries and keeping those with an
integrated-to-peak flux ratio above 1.25, a deconvolved major axis above 6″, and a
signal-to-noise ratio above 7. We discarded cutouts with missing pixels and components
within 30″ of a MiraBest position. The images are 4.5′ SkyView cutouts (McGlynn et al. 1998)
at the native 1.8″ pixel scale, giving 150 × 150 pixels, matching MiraBest's format. Each is
background-subtracted, thresholded at 3σ, and scaled to unit maximum.

The classifier is an ensemble of five ResNet-18 networks (He et al. 2016) trained on
MiraBest's 729 confident sources with full eight-fold dihedral augmentation, keeping
final-epoch weights so no model was selected on the data it is evaluated against.

The diagnostic itself is simple. A radio galaxy has no preferred orientation, so a
classifier's answer should not depend on how the image is rotated or mirrored, and
group-equivariant networks build this invariance in by design (Scaife & Porter 2021). We
call a source unstable if the ensemble-mean predicted class is not the same across all eight
symmetries of the square. The measurement needs no label and costs eight forward passes.

An instability rate means little without a baseline, and one taken from a small held-out set
is too noisy to serve. We therefore ran five-fold cross-validation over all 833 confident
MiraBest sources, giving every source a prediction from models that never saw it. This
raises the reference from 104 sources to 833, with a held-out accuracy of 91.2%
(89.1–93.0%).

One check underpins the comparison. Passing the 104 held-out galaxies through our own cutout
and preprocessing path, rather than their native images, changed little: 99.0% label
agreement and a median probability difference of 0.004. The instability below is therefore a
property of the candidate sample, not of our pipeline.

---

## §3 — Results (target ~400; owns the figure)

The candidate sample lies well outside the training domain. Only 15.3% (13.8–16.9%) fall
inside MiraBest's 10th-to-90th-percentile angular-size range, and MiraBest's 10th percentile
exceeds the candidates' 75th. Measured on the pixels with identical preprocessing, the
median candidate spans 18.0″ against MiraBest's 41.4″, with 123 pixels above threshold
against 294.5.

Instability follows that distance. The predicted class changes under a rotation or mirror
for 21.7% (19.9–23.5%) of candidates, compared with 11.4% (9.4–13.6%) for the
cross-validated MiraBest reference. The gap is 10.3 percentage points, the intervals do not
overlap, and the candidate rate is 1.9 times the reference. We had set a threshold of 10
points in advance, so the result clears it by only 0.3 points. The effect is real, but the
margin is narrow, and a larger candidate sample would test it more strongly.

The ordering across cohorts is the clearest form of the result (Figure 1). The flip rate
rises steadily with distance from the training set: 1.8% on the training sources, 11.4% on
held-out MiraBest sources, 21.7% on blind FIRST candidates, 24.2% on MiraBest's uncertain
class, and 41.2% on its hybrids. The blind sample sits next to the sources MiraBest itself
could not classify, rather than next to the sources the classifier handles well.

Selection does not repair the problem. Restricting the candidates to MiraBest's angular-size
range leaves the flip rate at 23.2% using the catalogue's deconvolved axis, or 22.8% using
the pixel extent, both slightly worse than the unrestricted sample. Two thirds (68.6%) have
another catalogued component within 2.25′, and keeping only the isolated ones gives 17.1%,
still 1.5 times the reference. None of the cuts a survey pipeline would naturally apply
returns the sample to baseline.

Not every diagnostic works. Seed disagreement separates the samples by only 3.7 points,
41.8% against 38.2%, with overlapping intervals. Against a 104-source reference it had
seemed to miss our threshold by 0.4 points; properly powered, the baseline is 38.2%, not
15.4%. It is not a usable reliability score.

---

## §4 — What to do about it (target ~220)

Because no selection cut restores stability, reliability must be assessed per source rather
than per sample. We suggest that pipelines applying morphology classifiers to blind
catalogues report each source’s dihedral instability alongside its class, and treat unstable
sources as unclassified rather than as low-confidence members of a class.

We offer one interpretation of the ordering, which no test here demonstrates. It is
consistent with a blind sample posing a different problem rather than a harder version of
the same one: many rows may have no true FR class, and a two-class classifier asked about
such a source can only answer unstably. Testing this needs labels for a blind subsample, or
a third class.

Three limits apply. The candidates are scored by the published ensemble while the reference
comes from the cross-validation models, so the comparison is between two model sets trained
the same way rather than identical weights. The diagnostic has been tested on one survey,
one architecture and one training set. It also assumes a classifier that is not equivariant
by construction: a group-equivariant network would show almost no flips by design, removing
the symptom rather than the domain shift, and with it a free reliability signal.

Code, pre-registered criteria and all reported numbers are at
github.com/astrophile73/radio-astronomy-ml-morphology; weights and cached predictions are
deposited at doi.org/10.5281/zenodo.24497097.

---

## References — verified via Crossref, 2026-11-24

All records below were confirmed against the Crossref API (authors, title, journal, volume,
pages, DOI). None is cited from memory.

| # | Reference | DOI | Supports |
|---|---|---|---|
| 1 | Fanaroff, B. L. & Riley, J. M. 1974, MNRAS, 167, 31P–36P, *The Morphology of Extragalactic Radio Sources of High and Low Luminosity* | 10.1093/mnras/167.1.31p | the FR classes themselves |
| 3 | Porter, F. A. M. & Scaife, A. M. M. 2023, RASTI, 2, 293–306, *MiraBest: a data set of morphologically classified radio galaxies for machine learning* | 10.1093/rasti/rzad017 | the training set |
| 4 | Scaife, A. M. M. & Porter, F. 2021, MNRAS, 503, 2369–2379, *Fanaroff–Riley classification of radio galaxies using group-equivariant convolutional neural networks* | 10.1093/mnras/stab530 | **the symmetry argument** |
| 5 | Aniyan, A. K. & Thorat, K. 2017, ApJS, 230, 20, *Classifying Radio Galaxies with the Convolutional Neural Network* | 10.3847/1538-4365/aa7333 | CNNs as standard practice for FR |
| 6 | Becker, R. H., White, R. L. & Helfand, D. J. 1995, ApJ, 450, 559, *The FIRST Survey* | 10.1086/176166 | the survey |
| 7 | Helfand, D. J., White, R. L. & Becker, R. H. 2015, ApJ, 801, 26, *The Last of FIRST: The Final Catalog and Source Identifications* | 10.1088/0004-637X/801/1/26 | the catalogue used |
| 8 | Norris, R. P., Hopkins, A. M., et al. 2011, PASA, 28, 215–248, *EMU: Evolutionary Map of the Universe* | 10.1071/as11021 | the ~70 million source projection in §1 |
| 9 | He, K., Zhang, X., Ren, S. & Sun, J. 2016, CVPR, 770–778, *Deep Residual Learning for Image Recognition* | 10.1109/cvpr.2016.90 | ResNet-18 |
| 10 | McGlynn, T., Scollick, K. & White, N. 1998, IAU Symp. 179, 465–466, *SkyView: The Multi-Wavelength Sky on the Internet* | 10.1017/s0074180900129316 | cutout service |

### Two errors this check caught

- **Miraghaei & Best DOI.** I had constructed `10.1093/mnras/stw3317`. It is wrong. The
  correct DOI is **10.1093/mnras/stx007**. Corrected in `.zenodo.json`.
- **Aniyan & Thorat page number.** I had written ApJS 230, **2**. It is ApJS 230, **20**.

### One claim that was reworded (resolved)

Fanaroff & Riley (1974) is titled *The Morphology of Extragalactic Radio Sources of High and
Low Luminosity*. It establishes the morphological dichotomy and its correlation with
luminosity — it does **not** say that FR type encodes "where a jet deposits its energy",
which is a later physical interpretation. §1 originally made that claim and cited it; it now
states the morphology/luminosity relation the paper actually supports.

### EMU — now verified from the PDF Raj supplied

`literatures/1106.3219v1.pdf` is Norris et al. (2011), and its abstract states that EMU "is
expected to detect and catalogue about **70 million galaxies**". §1 now quotes that figure
and cites the paper. The published record is PASA, 28, 215–248, DOI 10.1071/as11021,
confirmed via Crossref.

`literatures/2108.00569v1.pdf` is Norris et al. (2021), *The EMU Pilot Survey*. Its
introduction notes that about 2.5 million radio sources were known beforehand and that the
figure is "about to increase by about two orders of magnitude". Not cited: the 2011 figure
is more specific and directly supports the claim §1 makes. Worth using if §1 is ever
rewritten around what EMU has already delivered rather than what it projects.

### Optional, found during the check

Lines, N. E. P., Font-Quer Roset, J. & Scaife, A. M. M. 2024, RASTI, 3, 347–361,
*E(2)-equivariant features in machine learning for morphological classification of radio
galaxies*, 10.1093/rasti/rzae022. Directly on the equivariance thread, but largely redundant
with reference 4 in a 1,500-word note. Include only if §2's symmetry argument is expanded.

### Dropped during the word-budget pass

- **Shimwell et al. (2017), LoTSS.** Norris et al. (2011) now carries the survey-scale claim
  in §1 with a specific figure, so a second survey example was redundant.
- **Miraghaei & Best (2017).** It is the source of the MiraBest labels, but after §1 was
  rewritten it is cited nowhere in the body, and AAS style requires every reference to be
  cited in the text. Porter & Scaife (2023) covers the dataset. Reinstate it only if §2 is
  expanded to describe how the labels were assigned.

### Relevance note

Nine references at roughly 13 words each cost ~117 words. If the budget tightens further,
#5 (Aniyan & Thorat) goes first, since #4 can carry "CNNs are standard for FR" on its own.
References 1, 3, 4, 7 and 9 are load-bearing and should not be cut.

---

## Figure 1 caption (target ~70)

**Figure 1.** Dihedral instability, the fraction of sources whose predicted class changes
under at least one of the eight rotations and mirrors of the square, for five cohorts
ordered by distance from the training set. Error bars are bootstrap 95% intervals and the
shaded band is the five-fold held-out MiraBest reference. Open squares show candidates
restricted to MiraBest's angular-size range or to isolated components; none returns to
baseline.

---

## UAT keywords — verified 2026-11-25

Parsed locally from the official vocabulary file
(raw.githubusercontent.com/astrothesaurus/UAT/master/UAT_list.json, release 6.0.0, 2406
concepts), not taken from a search page. Chosen set:

| Concept | ID |
|---|---|
| **Fanaroff-Riley radio galaxies** | 526 |
| **Convolutional neural networks** | 1938 |
| **Astronomy data analysis** | 1858 |
| **Extragalactic radio sources** | 508 |

Also available and verified, if a different emphasis is wanted: Radio galaxies (1343), Radio
astronomy (1338), Radio continuum emission (1340), Astroinformatics (78), Classification
(1907), Galaxy classification systems (582), Computational astronomy (293).

## Still to do

- Add the affiliation in `paper/rnaas_note.tex`.
- Verify the `\uat{}{}` macro and the `[RNAAS]` class option against the AASTeX **v7**
  documentation. The macros used follow AASTeX 6.3 conventions and have not been checked
  against v7.
- Build the LaTeX and confirm the rendered length against the 1,500-word limit.
