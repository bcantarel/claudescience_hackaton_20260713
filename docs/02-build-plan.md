# ClinicalTrialFinder — MVP Plan

**Goal:** A working MVP (not App Store) that helps a physician find NSCLC clinical trials for a patient by matching on **diagnosis + gene profile**, plus the free structured filters (age, sex, recruiting status). Output is a *ranked list of candidate trials to review* — never an eligibility verdict.

**Constraints locked in:** Solo dev · NSCLC first · Data from ClinicalTrials.gov v2 API · Diagnosis via **OncoTree** (hierarchy matching) · Biomarker matching at **gene level** (no OncoKB, no HGVS parsing, no variant-class reasoning) · Python/FastAPI stack · Physician in the loop.

---

## The data reality (what each side gives you)

**Trial side (ClinicalTrials.gov v2 API — public, no key):**
- Structured, free: `minimumAge` / `maximumAge`, `sex`, recruiting status.
- Semi-structured: `conditions` (free-text names) + derived **MeSH** terms. → diagnosis normalization target.
- **Free text only:** `eligibilityCriteria` blob. → the *only* place trial biomarker requirements live. This is why genetics needs a (small, bounded) LLM step.

**Patient side (physician enters — structured, no NLP):**
- Diagnosis: picked from the **OncoTree** hierarchy.
- Age, sex.
- Gene profile: list of altered genes (e.g., EGFR, KRAS, ALK).

**The two ontologies:**
- **OncoTree** (diagnosis): hierarchy + native maps to NCIt / UMLS / ICD-O. Note: **no direct ICD-10 or SNOMED map** — those need UMLS as a bridge, so MVP accepts **OncoTree input only**; ICD-10/SNOMED input is a later upgrade.
- **Gene symbols** (HGNC + synonyms): a nearly-closed vocabulary of a few hundred cancer-relevant genes. Makes "is gene X mentioned?" a dictionary lookup, not open extraction.

---

## Architecture — everything at query time, no batch pipeline

The MVP does not pre-extract criteria from 500k trials. It filters cheaply, then does the small expensive work only on the survivors.

```
Patient (OncoTree dx + genes + age + sex)
        │
        ▼
① DIAGNOSIS + STRUCTURED FILTER  (deterministic, cheap)
   • OncoTree dx → match trials by condition/MeSH, walking the
     hierarchy UP (patient LUAD → trial "NSCLC"/"Lung Cancer")
   • age in [min,max] · sex · status = recruiting
   → shortlist of ~5–30 trials
        │
        ▼
② GENE CHECK  (only on shortlist, only patient's genes)
   • dictionary scan of eligibilityCriteria for patient's gene symbols+synonyms
   • no hit → biomarker "not specified / unknown"
   • hit → one small LLM call on the snippet, classify:
       gene ALTERED required | gene WILD-TYPE required | alteration EXCLUDED
     → met / not met / unknown
        │
        ▼
③ RANK + SHOW  candidate trials, each with per-dimension basis
   (dx match, age/sex, biomarker) + source sentence + trial link
   NEVER an overall eligible/ineligible verdict; NEVER auto-exclude
```

Why this shape: the LLM runs on ~a dozen trials × the patient's handful of genes, so it's fast and cheap; diagnosis matching stays fully deterministic and auditable; nothing needs a nightly job for an MVP (refresh on demand or daily).

> **Note (post-build):** the "a dozen trials" assumption did not survive contact with the data — see `06-step4-gene-layer-findings.md`. The gene layer runs on hundreds of trials per query, so classifications are **cached per (trial, gene)**, which is the offline-batch approach the feasibility doc recommended.

---

## Steps

1. **Pull NSCLC trials from CT.gov v2.** Inspect real `conditions`, MeSH terms, `eligibilityCriteria`, age/sex/status. Deliverable: a local cache + an honest read on how good the MeSH tagging and biomarker phrasing actually are. *(1–2 days)*
2. **Load OncoTree.** Pull the full tree (hierarchy + NCIt/UMLS refs) from the OncoTree API. Build the ancestor-walk lookup. *(1 day)*
3. **Diagnosis crosswalk + matcher.** Map trial conditions/MeSH → OncoTree nodes (start with name/synonym/MeSH string match; measure unmatched rate before adding anything heavier). Implement hierarchical match (patient node + ancestors). Add age/sex/status filters. *(3–5 days)*
4. **Gene layer.** Build the gene symbol+synonym dictionary (cancer-relevant subset). Query-time scan of shortlisted trials; LLM snippet classifier for altered/wild-type/excluded → three-valued result. *(3–5 days)*
5. **Thin UI + clinician test.** One web page or CLI: pick OncoTree dx, enter genes + age + sex → ranked trials with per-dimension basis and links. Run 10–15 real de-identified NSCLC cases past a clinician. Fix what they flag — especially any wrong exclusions. *(3–5 days + review)*
6. **(Then, only if MVP proves out)** iOS wrapper over the same API. Diagnosis biological-equivalence (OncoKB), variant-level matching, ICD-10/SNOMED input, and other eligibility dimensions (prior therapy, ECOG) are all deferred past the MVP.

Rough solo total: **~2–4 weeks** to a clinician-testable MVP. The swing factors are diagnosis-crosswalk coverage (step 3) and gene-classifier accuracy (step 4), not UI.

---

## Stack
Python + FastAPI · PostgreSQL (or even SQLite for the MVP) · CT.gov v2 API · OncoTree API · one frontier LLM behind a swappable interface, called only on eligibility snippets (public text — no PHI, no BAA needed) · thin web page first, SwiftUI later.

> The delivered MVP ships as a single self-contained HTML page over a pre-computed cache (no server needed to test), with the Python pipeline behind it. FastAPI is the natural production wrapper.

## Guardrails that stay even in the MVP
- Three-valued matching (met / not met / **unknown**) — surface uncertainty, never hide it.
- Cite the trial's source sentence for every biomarker judgment.
- Rank-and-surface; **never auto-exclude** a patient from a trial.
- A clinician validates before any patient-facing use.

## Honest risks
- **Gene-level false positives:** right gene, wrong variant (patient EGFR T790M vs. trial wanting L858R) will over-surface. Acceptable for an MVP that a physician reviews; it's the reason to show the source sentence.
- **MeSH tagging gaps:** if trial MeSH terms are too coarse, diagnosis recall suffers — measure in step 1 before over-investing.
- **Wild-type/excluded direction:** the classifier must get altered-vs-wild-type-vs-excluded right, or it will wrongly match immunotherapy/wild-type trials. This is the one place gene-level still needs real care.
