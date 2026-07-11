# Step 3 — Diagnosis crosswalk + hierarchical matcher + structured filters

Modules: `crosswalk.py` (CT.gov→OncoTree), `matcher.py` (hierarchical dx + age/sex/status).

Bottom line: the deterministic diagnosis matcher works and is auditable. String/MeSH crosswalk reaches **98% coverage (1,267/1,287)** with a tiny curated map — no UMLS bridge needed for the lung branch.

## Crosswalk: 98% coverage
- **MeSH map alone: 86%.** MeSH lung granularity is coarse — two terms carry everything: `D002289` → NSCLC, `D008175` → LUNG. No MeSH term distinguishes LUAD from LUSC, so trials key at the NSCLC/LUNG level (fine — patients walk up).
- **+ condition-name fallback: 98%.** Token-presence name mapper handles word-order variants ("Lung Non-Small Cell Carcinoma"). One bug found & fixed: a contiguous-regex draft missed those; token presence fixed it.
- **Unmatched floor: 20 trials (1.6%)** — genuine pan-tumor baskets and data-quality junk ("Advanced Solid Tumor", "C-Met Exon 14 Mutation", "PROMs").

### Basket-trial recall risk
Biomarker-defined baskets ("C-Met Exon 14 Mutation") carry no lung diagnosis tag and get dropped by a hard diagnosis filter. Recommend a secondary gene-only pool, surfaced as "diagnosis: basket/unspecified". ~1–2% of the corpus.

## Hierarchical matcher — walk-up verified
`diagnosis_relation` classifies each trial exact / broader / narrower / none:
- LUAD patient: mostly broader (trials tagged NSCLC/LUNG) + a few exact.
- NSCLC-NOS patient: narrower matches (LUAD/LUSC-specific trials) are **surfaced with a flag**, not silently matched or dropped.
- Wrong tissue (BREAST): 0 matches — confirms the crosswalk+hierarchy excludes off-tissue trials.

## Structured filters
Age monotonic and correct; absent `maximumAge` treated as **no cap**. Sex a near non-filter but implemented. Status general.

## Honest caveat
Diagnosis+age barely shrinks an all-NSCLC pull; the real narrowing to a reviewable list comes from the **biomarker layer (step 4)**.
