# Known Issues — Normalizing Trial Inclusion/Exclusion Criteria

**Status:** living document · **Scope:** the free-text → structured normalization pipeline that turns ClinicalTrials.gov `eligibilityCriteria` blobs into matchable fields (diagnosis, biomarker, clinical criteria). **Audience:** future developers.

This is the honest retrospective. The core problem of this project is not the UI or the data source — it is that everything clinically interesting on the trial side lives in one unstructured `eligibilityCriteria` prose blob (median ~2,500 chars, max ~20,000), and turning that into reliable structured fields is where the accuracy risk, and every issue below, lives. Nothing here is a blocker for an MVP with a physician in the loop; all of it matters before anything approaches autonomous use.

Severities: **S1** = can produce a wrong match a physician might act on; **S2** = degrades recall/precision but visible on review; **S3** = cosmetic / efficiency.

---

## 1. Diagnosis normalization (CT.gov MeSH/conditions → OncoTree)

### 1.1 The two vocabularies don't share a key (S2)
CT.gov tags diagnosis with **MeSH** (e.g. `D002289` "Carcinoma, Non-Small-Cell Lung"); OncoTree keys on **UMLS/NCI** (NSCLC = UMLS `C0007131`). They do **not** join on a shared code, and — critically — they don't even string-match on the most important node: MeSH says "Carcinoma, Non-Small-Cell Lung," OncoTree says "Non-Small Cell Lung Cancer."
- **Current mitigation:** a hand-built MeSH-ID → OncoTree map for the lung branch + a condition-name token matcher. Reaches **98% coverage** on the NSCLC pull.
- **Residual risk:** the hand map is lung-specific. It does **not** generalize to other tumor types. Scaling past NSCLC needs the real bridge: MeSH → UMLS CUI via the **UMLS Metathesaurus** (free, but license/registration; end-users at the deploying institution must also be licensed).
- **Future work:** integrate UMLS as the diagnosis join key before expanding disease scope.

### 1.2 Free-text condition names are unnormalized (S2)
Raw `conditions` strings are wildly inconsistent — "nsclc", "non small cell lung cancer", "carcinoma, non-small-cell lung", "lung cancer (nsclc)" — so string-matching them directly is not viable; the derived MeSH layer is what makes diagnosis tractable.
- **Bug found & fixed during build:** the name fallback first used a *contiguous* regex (`non-small cell lung`) and silently missed word-order variants like "Lung Non-Small Cell Carcinoma." Switching to **token-presence** logic fixed it. Lesson: eligibility/condition text reorders freely; never assume token adjacency.

### 1.3 MeSH is too coarse to distinguish histology (S2)
MeSH has no term separating LUAD from LUSC — lung granularity effectively stops at "NSCLC" and "Lung Neoplasms." This is *acceptable* for the current design (patients walk UP the OncoTree hierarchy, so LUAD matches an NSCLC-tagged trial) and it aligns with the never-auto-exclude guardrail, but it means the tool cannot, from MeSH alone, tell that a LUSC patient shouldn't be on a LUAD-only trial. Histology-specific exclusion would need parsing the criteria text, not the MeSH tags.

### 1.4 Biomarker-defined "basket" trials have no lung diagnosis tag (S2, recall)
~1–2% of trials that would accept an NSCLC patient (e.g. condition = "C-Met Exon 14 Mutation", "Advanced Solid Tumor") carry **no lung MeSH term at all**, so a hard diagnosis pre-filter drops them. The tool currently excludes them.
- **Future work:** a secondary gene-only pool for pan-tumor baskets, surfaced as "diagnosis: basket/unspecified."

---

## 2. Biomarker / gene normalization

### 2.1 Gene symbols collide with English words (S1 if unhandled)
Case-insensitive matching of short symbols produces silent false positives: **"MET"** matches the verb "met" ("criteria are met"), **"neu"** (an ERBB2 alias) matches ordinary text.
- **Mitigation:** MET is matched **case-sensitively** ("MET"/"c-Met", never lowercase "met"), which took obviously-bad MET hits to 0; the "neu" alias was dropped (HER2 covers ERBB2). Any new short/ambiguous symbol (e.g. future additions like "KIT", "RET" already handled) must be audited the same way.

### 2.2 Gene named as therapy, not biomarker (S2)
"EGFR" appears inside **"EGFR-TKI" / "EGFR inhibitor"** — a *prior-therapy* reference, not a biomarker requirement. **21% of EGFR tokens** are therapy-phrase mentions; the same for ALK.
- **Mitigation:** a therapy-phrase filter deprioritizes `GENE-(TKI|inhibitor|targeted|mAb)` before classification. Not perfect; some therapy context still reaches the classifier and relies on it to return NOT_A_REQUIREMENT.

### 2.3 Meaning flips on the inclusion/exclusion section (S1 if unhandled)
A bare sentence loses whether it's inclusion or exclusion, which **inverts** it: "no EGFR mutation" means *wild-type required* under Inclusion but *alteration excluded* under Exclusion. Same words, opposite match.
- **Mitigation:** 97% of blobs carry both "Inclusion Criteria"/"Exclusion Criteria" headers; the extractor tags each snippet's section and feeds it to the classifier as strong evidence. **The 3% without headers are a genuine gap** — those snippets are classified with lower confidence and can be wrong.
- **Future work:** better section segmentation for header-less blobs (many use numbered lists or ad-hoc headers like "Key Exclusion").

### 2.4 Gene-level, not variant-level (S1 — the headline limitation)
Matching is at the **gene** level. A patient's EGFR **T790M** matches a trial requiring EGFR **L858R** — both resolve to "MET" — because the tool does not reason about which variant. This is deliberate MVP scope (no OncoKB/HGVS), and the mitigation is that every match **cites the trial's source sentence** so the physician catches the mismatch. It is nonetheless the single most likely way the tool over-surfaces, and the reason it must never be used as an autonomous filter.
- **Future work:** variant-level reasoning via OncoKB oncogenicity/effect annotations + HGVS normalization (note OncoKB's no-ML-training clause — call the API, don't distill it).

### 2.5 Per-cohort / compound logic (S2)
Basket trials with per-cohort biomarker rules ("Cohort B: EGFR exon 19/21") are classified at the sentence level and may miss cohort scoping — a requirement that applies to one arm gets read as trial-wide. 2 (trial,gene) conflicts of this kind were detected and flagged in the gene cache; more likely exist unflagged.

---

## 3. Clinical-criteria normalization (ECOG, labs, directional)

### 3.1 "Common (>20%)" is not the same as "useful to structure" (design note)
An early hypothesis was to structure any criterion appearing in >20% of trials. On measurement, **all 24 common categories cleared 20%** — standard oncology boilerplate is common by definition. Prevalence is the wrong selector; the right axes are **discriminating × extractable**. Informed consent (65%), contraception (68%), "adequate organ function" (41%), and measurable disease (57%) are common but non-discriminating — everyone passes, so structuring them narrows nothing. Documented so this isn't re-litigated.

### 3.2 ECOG: greedy digit extraction grabs the wrong number (S1 if unhandled, fixed)
Extracting the max allowed ECOG by "take the largest 0–4 digit near 'ECOG'" produced a clinically impossible distribution (95 trials at max ECOG 3, 77 at 4) because it captured the **next list-item number**: "...ECOG 0-1. **4.** Adequate organ function..." → parsed as 4. A subsequent clause-boundary fix over-corrected and cut ranges ("0-1" → 0). The working version uses explicit **range / comparator** patterns and yields a sane distribution (mostly max 1 and 2), **81% coverage**.
- **Residual:** 19% of trials have no parseable ECOG (KPS-only, unusual phrasing); an LLM fallback would raise coverage.

### 3.3 Labs: unit chaos makes thresholds unsafe as a hard filter (S1 — do not trust blindly)
This is the worst normalization problem in the criteria layer. The same analyte is reported in incompatible units across trials with no unit field:
- Hemoglobin as **`9.0` (g/dL)** in one trial vs **`90.0` (g/L)** in another — a 10× difference.
- Creatinine and bilirubin mix **mg/dL**, **µmol/L**, and **×ULN**.
- AST/ALT is almost always **×ULN**, not absolute.

A naive "patient value vs extracted threshold" comparison will therefore produce **false NOT-METs** (e.g. patient Hgb 11 g/dL vs a trial threshold stored as "90" g/L). 
- **Mitigation:** labs are treated as **annotation-grade, not filter-grade** — every lab result is stamped **"verify units,"** and lab fails never auto-hide a trial unless the user explicitly opts in. Coverage is also low (15–29% per analyte) because extraction only fires on an unambiguous comparator+number.
- **Future work:** unit normalization (detect g/L vs g/dL, µmol/L vs mg/dL, ×ULN vs absolute) before any lab value is used for filtering. Until then, labs should stay annotation-only.

### 3.4 Directional criteria are 3-valued and context-dependent (S2)
Brain/CNS mets, prior therapy, and prior immunotherapy each need an LLM classification pass because the direction isn't lexical:
- **Brain mets** is genuinely 3-valued: *active mets excluded* vs *treated/stable allowed* vs *unspecified* — "brain metastases" alone doesn't tell you which. Handled, distribution ~even.
- **Prior treatment is the least reliable field.** "Prior" also appears for radiation, surgery, and washout windows; "line of therapy" phrasing is inconsistent. `naive_required` / `pretreated_required` should be treated as a **hint**, not a hard gate.
- **Prior immunotherapy** has a subtle trap: a trial that *uses* immunotherapy as its intervention is not the same as one that *excludes prior* immunotherapy. The classifier is instructed on this distinction but it's an easy false-positive source.

---

## 4. Cross-cutting issues

### 4.1 Query-time LLM cost forced a caching architecture (resolved, but note it)
The original plan assumed the gene classifier would run on "a dozen trials" per query. Measured reality: an EGFR patient's shortlist is ~1,200 trials, ~510 with an EGFR gate → **~750 LLM calls per query**. Every LLM-derived field (gene directions, brain mets, prior therapy, prior IO) is therefore **classified once per (trial, field) and cached**; the shipped tool makes zero live LLM calls. Consequence for future devs: **the cache is only as fresh as the last classification run.** There is no incremental re-classification on trial updates yet.

### 4.2 Citations must be verified, not trusted (S2, handled)
The classifier occasionally returns a `cited_span` that isn't a verbatim substring (capitalization drift, paraphrase). Every cache-build step **verifies the span is an exact substring and falls back to the whole snippet if not**, so a citation never points to text that isn't in the trial. Keep this guard on any new extraction.

### 4.3 Data freshness / "recruiting" is unreliable (S2)
CT.gov's `overallStatus` cannot be trusted alone: of the "recruiting" pull, **17% are observational**, **20% have a primary completion date already in the past**, and **28% weren't updated in >12 months** (some >2 years). The tool filters to interventional / not-past-completion and flags "likely stale," but this is a **heuristic proxy** — a real system needs a scheduled refresh reading the record's verification date.

### 4.4 No independent accuracy benchmark (S1 — the meta-issue)
All extraction/classification was validated **LLM-against-LLM** during the build (a subagent classifies, the author reviews). That validates mechanism and prompts, **not accuracy**. The published ceiling for this task (NIH TrialGPT) is ~87% criterion-level, with **exclusion accuracy lower than inclusion** — i.e. the model is more likely to wrongly rule a patient *out*, the worst failure mode. The clinician review (build step 5) is the first real accuracy signal and has not yet been run at scale.

---

## 5. Priority for future development

| # | Issue | Sev | Recommended next step |
|---|---|---|---|
| 4.4 | No real accuracy benchmark | S1 | Run the clinician review; label a gold set; measure per-field precision/recall, especially wrong-exclusions. |
| 2.4 | Gene-level, not variant-level | S1 | Add OncoKB/HGVS variant reasoning behind the gene layer. |
| 3.3 | Lab unit chaos | S1 | Unit normalization before any lab filtering; keep annotation-only until then. |
| 1.1 | No shared diagnosis key (UMLS bridge) | S2 | Integrate UMLS before expanding beyond NSCLC. |
| 2.3 | Header-less section segmentation | S2 | Improve inclusion/exclusion detection for the ~3% without headers. |
| 3.4 | Prior-treatment reliability | S2 | Separate "prior systemic therapy" from radiation/surgery/washout; consider line-count extraction. |
| 1.4 | Basket trials dropped by dx filter | S2 | Secondary gene-only pool for pan-tumor baskets. |
| 4.1/4.3 | Cache freshness + stale status | S2 | Scheduled CT.gov refresh + incremental re-classification; read verification dates. |
| 2.5 | Per-cohort logic | S2 | Cohort-aware extraction (segment by arm/cohort before classifying). |
| 3.2 | ECOG coverage 81% | S3 | LLM fallback for the unparseable 19%. |

## 6. General lessons for anyone extending this
- **Free text reorders, negates, and section-scopes.** Never assume token adjacency; always carry the inclusion/exclusion section; a keyword ≠ a requirement (therapy mentions, testing logistics, background).
- **Isolate the uncertain step.** Let the LLM only *interpret*; keep the met/not-met logic deterministic and the citation verifiable. Every field here follows that split.
- **Prefer annotation over auto-exclusion** wherever extraction is shaky (labs, prior therapy). The guardrail — rank-and-surface, never auto-exclude, always cite — is what makes ~87%-accurate extraction safe to ship.
- **Audit every new short gene symbol** for English-word / substring collisions before trusting counts.
