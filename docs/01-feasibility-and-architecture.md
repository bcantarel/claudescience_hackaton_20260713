# ClinicalTrialFinder — Feasibility & Architecture Assessment

**Scope:** iOS app to help physicians find oncology clinical trials by extracting and matching structured inclusion/exclusion criteria (age, sex, diagnosis via ICD-10 / SNOMED CT / OncoKB, and genetic profile).
**Context:** Academic/institutional tool. Hybrid extraction (LLM + ontology normalization).
**Date:** July 2026

---

## 1. Bottom line up front

The iOS app is the *easy* 20% of this project. The hard, risky, and expensive 80% is turning free-text eligibility criteria into reliable structured fields and then matching them to a real patient. This is achievable at a useful-but-imperfect quality level, and the state of the art proves it: NIH's TrialGPT hit **87.3% criterion-level accuracy** — close to human experts (87.9–90.0%) — but that also means roughly **1 in 8 criterion judgments is wrong**. For an academic decision-support tool with a physician in the loop, that is workable. As an autonomous filter, it is not.

The verdict: **feasible and worth building**, provided you (a) keep the physician in the loop and never auto-exclude patients, (b) treat extraction accuracy as the core engineering problem, not the UI, and (c) resolve three licensing/regulatory constraints early (SNOMED end-user licensing, OncoKB's no-ML-training clause, and the FDA CDS line between "finding" and "matching").

The single most common way this class of project fails is underestimating extraction and overbuilding the app.

---

## 2. Data source reality: ClinicalTrials.gov API v2

The corpus is a solved problem. ClinicalTrials.gov's v2 API is genuinely good and is the correct primary source.

- **Endpoint:** `https://clinicaltrials.gov/api/v2/studies`. No API key, no auth, no signup. Rate limits exist but are generous for reasonable batch use.
- **Pagination:** token-based (`nextPageToken`), page size up to 1000.
- **Public domain data.** No licensing obstacle to the trial records themselves.

**Critical structural fact that defines your entire architecture:** the `EligibilityModule` splits into two very different kinds of data:

| Field | Type | Extraction difficulty |
|---|---|---|
| `minimumAge`, `maximumAge`, `stdAges` | **Structured** | Trivial — parse directly |
| `sex`, `healthyVolunteers` | **Structured** | Trivial — parse directly |
| `eligibilityCriteria` | **Free-text prose blob** | **This is the entire hard problem** |

Age and sex you get for free. Everything clinically interesting — the diagnosis, histology, stage, biomarkers, prior lines of therapy, ECOG, comorbidities, washout periods, the actual genetic variants — lives inside one unstructured `eligibilityCriteria` string.

Parsing that reliably into ICD-10 / SNOMED / OncoKB codes and HGVS variant strings is the project. Do not let anyone tell you the API "already has structured criteria" — it does not, beyond age and sex.

---

## 3. The extraction problem — what's realistic

### What the evidence says
NIH's TrialGPT (Nature Communications, 2024) is the most rigorous public benchmark and your realistic ceiling for an off-the-shelf-ish approach:

- Criterion-level eligibility accuracy: **87.3%** (inclusion 89.9%, exclusion 85.9%).
- Sentence-location F1 for *why* a criterion matched: **88.6%**.
- Trial ranking NDCG@10: 0.73; excluding ineligible trials AUROC: 0.80.
- Measured benefit: **~42.6% reduction in screening time** in a human study.

~87% is genuinely useful for *shortlisting* and *time-saving*, and genuinely dangerous for *automated exclusion*. Exclusion accuracy is lower than inclusion — meaning the model is more likely to wrongly rule a patient out, which is the worst failure mode in trial finding (a missed trial can be a missed treatment option).

### Why "hybrid" is the correct call
- **LLM does span extraction and interpretation** — reading the prose, identifying "EGFR L858R" as a required biomarker, recognizing negation, handling the messy logic ("or", "at least one of", nested conditions).
- **Ontologies do normalization and grounding** — mapping the extracted spans to stable codes so you can match deterministically and auditably.

Pure rules alone have poor coverage; pure LLM-to-freetext gives no stable, auditable match key. Hybrid is the only one that produces something a physician can trust and verify.

### The genetic-profile piece is the hardest sub-problem
- Variants are written a dozen ways: "EGFR L858R", "EGFR p.Leu858Arg", "exon 19 del", "EGFR-mutant", "EGFR activating mutation". You need HGVS normalization and variant-class reasoning.
- Matching requires *biological* logic, not string equality: "EGFR exon 19 deletion" must satisfy "EGFR activating mutation". That's what OncoKB's annotations are for.
- Fusions, copy-number, TMB, MSI, expression each have their own representation.

> The MVP deliberately scopes to **gene-level** matching (is the gene named as a requirement, and in which direction) and defers variant-class reasoning. See the step docs.

---

## 4. Ontology & licensing constraints (resolve these before building)

**ICD-10-CM** — Public domain in the US. No obstacle.

**SNOMED CT** — Free in the US via NLM, but gated behind a **UMLS Metathesaurus license** (free, requires registration). The catch: a vendor license does **not** cover your end users — each user's institution must also hold a UMLS license. Confirm your target users are covered before embedding SNOMED content.

**OncoKB** — Free for academic research via API. Two architecture-shaping restrictions: **AI/ML model training on OncoKB data is prohibited** (use live API annotation, don't distill it into a model); and **no bulk download** (API only). Commercial use needs a paid license.

**Genetic variant standards** — Use **HGVS** for nomenclature and **ClinVar** + OncoKB for interpretation.

---

## 5. Regulatory posture (academic doesn't mean exempt)

Relevant framework: the **FDA 2022 final guidance on Clinical Decision Support Software** (21st Century Cures Act), which narrowed the non-device exemption.

Defensible design posture:
- **Present, don't decide.** Show candidate trials and the specific criteria/source text so the physician independently reviews the basis.
- **Never auto-exclude.** Given ~86% exclusion accuracy, an automated "not eligible" verdict is clinically and regulatorily risky. Rank and surface; let the human rule out.
- **Always cite the source criterion.** Sentence-location grounding makes the tool an information-display aid, not an opaque recommender.

Not legal advice — involve your institution's compliance office before real-patient use.

**PHI warning:** the moment a physician types a real patient's diagnosis and mutations, you are handling PHI (HIPAA + IRB). Keep patient matching deterministic and local; do the LLM extraction on *trial* text (public data) offline. The MVP's self-contained HTML keeps all patient entry client-side — no PHI leaves the page.

---

## 6. Proposed architecture

A **thin client over a backend that does the heavy lifting** — do not attempt on-device extraction.

### Key design decisions
- **Extract offline, in batch — not at query time.** The ~500k trials are a fixed corpus that changes slowly. Batch-extract and store normalized criteria; this makes queries fast, cacheable, and human-QA-able.
- **Two-stage matching.** Cheap deterministic pre-filter (age/sex/status/condition) → expensive criterion comparison only on survivors.
- **Three-valued match logic** (met / not met / **unknown**), never a silent pass/fail.
- **PHI-aware boundary.** Keep patient matching local; extract only public trial data externally.
- **Freshness is a feature.** Refresh nightly and display last-verified dates — a trial shown "recruiting" that closed last week wastes a physician's time. *(Confirmed real in step 5: 20% of "recruiting" trials had a past completion date.)*

### Suggested build order (de-risk the hard part first)
1. Extraction spike; have a clinician score the output before writing UI.
2. Normalized trial store + batch pipeline over one disease area (NSCLC).
3. Deterministic matching API with three-valued logic and per-criterion citations.
4. Thin client last.

---

## 7. Honest risk register

| Risk | Severity | Notes |
|---|---|---|
| Extraction accuracy on complex genetic/logic criteria below usable threshold | **High** | Mitigate: scope to a disease area, human-QA, expose "unknown." |
| Wrongly excluding an eligible patient (exclusion acc. ~86%) | **High** | Never auto-exclude; rank-and-surface only. |
| SNOMED end-user licensing not covering users | Medium | Confirm institutions hold UMLS licenses. |
| OncoKB no-ML-training clause | Medium | Use live API annotation. |
| FDA CDS line if tool outputs verdicts | Medium | Stay in "display for independent review." |
| PHI leaving the HIPAA boundary via LLM API | Medium | Keep patient matching local. |
| Stale recruiting status | Medium | Nightly refresh; show verification dates. |
| Scope creep to "all of oncology" | Medium | Vertical slice first. |

## 8. What I'd push back on
- **Don't build the iOS app first.** Prove extraction first.
- **Don't promise "eligibility."** Promise "candidate trials + the criteria to check."
- **Don't cover every biomarker modality at launch.** Pick the ones that dominate the target disease and expand deliberately.

---

## Sources
- ClinicalTrials.gov Data API; NLM Technical Bulletin (API v2.0).
- TrialGPT — Matching patients to clinical trials with LLMs (Nature Communications, 2024); TrialGPT project page (NLM/NIH).
- OncoKB Licensing FAQ and API access.
- Licensing SNOMED CT (NLM); UMLS licensing.
- FDA Clinical Decision Support Software final guidance (2022); Federal Register notice.
