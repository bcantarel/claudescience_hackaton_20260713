# Step 1 — CT.gov v2 pull + honest data read

**Query:** `query.cond="non-small cell lung cancer"` + `overallStatus=RECRUITING` · **Result:** 1,287 trials, full protocol + derived sections cached. No API key, token pagination, whole corpus pulled in 2 pages.

Bottom line: structured fields and MeSH diagnosis tagging are good enough to build on; biomarker phrasing is exactly as messy as predicted — which confirms the plan to do a dictionary-scan → LLM-classify gene layer.

## Structured fields (age / sex / status) — trivial
- **Sex:** 1,283/1,287 `ALL`. Effectively a non-filter for NSCLC.
- **minimumAge:** present on 98%; 1,200 trials are `18 Years`.
- **maximumAge:** present on only 26% — **most trials have no upper age limit** (absent = no cap, not missing). A real correctness trap: do not treat absent maximumAge as unknown/exclude.
- **stdAges:** every trial `OLDER_ADULT`, 1,276 `ADULT`, 36 `CHILD`.

## Diagnosis / MeSH tagging — usable, coarser than ideal
Free-text `conditions` names are inconsistent ("nsclc", "non small cell lung cancer", "carcinoma, non-small-cell lung"), so string-matching raw names is not viable — the derived MeSH layer matters.
- **89%** have ≥1 condition MeSH term; **81%** carry "Carcinoma, Non-Small-Cell Lung".
- **14% (177) have no lung MeSH term at all** — basket/tissue-agnostic trials. This is the diagnosis-recall risk to measure in step 3.

## Biomarker phrasing — messy, LLM step justified
- eligibilityCriteria never empty; median 2,547 chars, max 20,203.
- **62%** mention a tracked biomarker; **56%** an actionable driver gene.
- Top gene mentions: EGFR 548, ALK 377, PD-L1 314, ROS1 205, MET 180, ERBB2/HER2 127, KRAS 127, BRAF 116, RET 110, NTRK 81. A handful of genes cover almost everything.

Three distinct directions the classifier must separate, all present in real text: alteration required, wild-type required, alteration excluded. Pure string matching cannot tell these apart.

### Therapy-name false positives
"EGFR" often appears inside "EGFR-TKI"/"EGFR inhibitor" — a prior-therapy reference, not a biomarker gate. **21% of EGFR tokens** are therapy-phrase mentions. Mitigation: deprioritize `GENE-(TKI|inhibitor|targeted|mAb)` phrases before classification.
