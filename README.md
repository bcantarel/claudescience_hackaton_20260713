# ClaudeScience Hackathon 2026

This repository contains work from the ClaudeScience hackathon (July 2026).

- **[`clinicalTrialApp/`](clinicalTrialApp/)** — **ClinicalTrialFinder**, a decision-support prototype that helps a physician find *candidate* NSCLC clinical trials for a patient by matching on diagnosis + gene profile + age/sex. See its [README](clinicalTrialApp/README.md) to run it (open `clinicalTrialApp/app/index.html`) and its [`docs/`](clinicalTrialApp/docs/) for the full per-step design findings.
- **`geneNetworking/`** — (separate component)

The rest of this file is the design narrative for ClinicalTrialFinder: the questions we settled before building, the plan we followed, and the general approach.

---

## The questions we answered first

The project was scoped by resolving a handful of decisions up front — getting these wrong is how this class of project usually fails (by underestimating extraction and overbuilding the app).

**1. What is the output — an eligibility verdict, or a candidate list?**
A ranked list of *candidate trials for a physician to review*, never an "eligible / ineligible" verdict, and never an auto-exclusion. This is both the clinically safe posture (the worst failure is wrongly ruling a patient out of a trial they could join) and the regulatorily defensible one (display-for-independent-review vs. a patient-specific directive, per the FDA 2022 CDS guidance).

**2. What do we match on?**
Diagnosis, gene profile, and the free structured fields (age, sex, recruiting status). Everything clinically interesting on the trial side lives in one free-text `eligibilityCriteria` blob — age and sex are the only genuinely structured fields.

**3. Which diagnosis ontology?**
**OncoTree** (a clean single-parent cancer hierarchy). The MVP accepts OncoTree input only. OncoTree keys on UMLS/NCI, not ICD-10 or SNOMED; bridging to those needs a UMLS Metathesaurus license, so ICD-10/SNOMED input is deferred.

**4. Variant-level or gene-level biomarker matching?**
**Gene-level** for the MVP — "is the gene named as a requirement, and in which direction (altered / wild-type / excluded)." No OncoKB, no HGVS parsing, no variant-class reasoning. The known cost is over-surfacing (a patient's EGFR T790M matches a trial wanting EGFR L858R); the mitigation is citing the source sentence so the physician catches it.

**5. Disease scope?**
**NSCLC first.** A vertical slice beats "all of oncology" before the hard part (extraction) is proven.

**6. Query-time LLM, or batch/cached?**
The build plan assumed the gene classifier would run on "a dozen trials" per query. Measured reality: ~750 LLM calls per patient. So classifications are **cached per (trial, gene)** — a trial's EGFR requirement is identical for every EGFR patient — which is the offline-batch approach the feasibility assessment recommended.

**7. How much to build for the clinician test, and with what cases?**
A scoped classification cache first, then expanded to the full interventional set (998 trials, 1,563 cached classifications). Test cases are **synthetic and de-identified** (12 profiles spanning the real decision space), with the tool also accepting real de-identified cases entered by the clinician — no PHI leaves the static page.

**8. Data quality — trust CT.gov's "recruiting" flag?**
No. Measured on the pull: 17% of "recruiting" trials are observational, 20% have a primary completion date already in the past, 28% weren't updated in over a year. The tool filters to interventional / not-past-completion and flags likely-stale trials, showing the physician the dates rather than hiding behind the status field.

---

## The plan

A ~2–4 week solo MVP, de-risking the hard part (extraction) before any UI:

1. **Pull NSCLC trials from CT.gov v2** and get an honest read on MeSH tagging + biomarker phrasing.
2. **Load OncoTree** and build the ancestor-walk lookup.
3. **Diagnosis crosswalk + hierarchical matcher** (CT.gov MeSH/condition → OncoTree, walk up the tree) + age/sex/status filters.
4. **Gene layer** — dictionary scan + section-aware LLM classifier → three-valued (met / not met / unknown) result with cited source sentence.
5. **Thin UI + clinician test** — a single self-contained page; run real de-identified cases past a clinician and fix what they flag (especially wrong exclusions).
6. *(Deferred until the MVP proves out)* iOS wrapper, variant-level matching (OncoKB/HGVS), ICD-10/SNOMED input, and other eligibility dimensions (prior therapy, ECOG, stage).

Each step's honest findings are written up in [`clinicalTrialApp/docs/`](clinicalTrialApp/docs/).

---

## General approach

Deterministic where it can be, LLM only where it must be, uncertainty surfaced rather than hidden.

```
Patient (OncoTree dx + genes + age + sex)
        │
        ▼
① DIAGNOSIS + STRUCTURED FILTER   (deterministic, auditable)
   OncoTree ancestor walk-up (patient LUAD → trial "NSCLC"/"Lung")
   + age in [min,max] + sex + recruiting status
        │
        ▼
② GENE CHECK                      (LLM interprets; cached per trial×gene)
   dictionary scan of eligibility text → section-aware classifier →
   direction (ALTERED_REQUIRED | WILD_TYPE_REQUIRED | ALTERATION_EXCLUDED | NOT_A_REQUIREMENT)
   × patient status → met / not met / unknown   (mapping is pure code)
        │
        ▼
③ RANK + SHOW   candidate trials, per-dimension basis + source sentence +
   full inclusion/exclusion criteria + trial link.  NEVER a verdict.
```

Design principles that hold throughout:
- **Isolate the uncertain step.** The LLM only interprets language (which direction a criterion points); the met/not-met logic is a verified deterministic truth table. Every biomarker result is explainable and cites real trial text.
- **Cache the expensive work.** Trial criteria change slowly, so classify each (trial, gene) once and reuse — queries are instant.
- **Three-valued matching.** met / not met / **unknown** — never a silent pass/fail.
- **Rank-and-surface, never auto-exclude.** "Not met" trials are ranked low, not hidden.
- **Physician in the loop.** A clinician validates before any patient-facing use. This is not a medical device and gives no medical advice.

---

## Honest limitations
- **Gene-level, not variant-level** (deliberate MVP scope) — right gene / wrong variant over-surfaces; the cited sentence and full criteria are how the physician catches it.
- **Not independently accuracy-validated** — the classifier was validated LLM-against-LLM; a clinician review is the first real accuracy signal (expect roughly the TrialGPT ~87% criterion-level ceiling, exclusion worse than inclusion).
- **Snapshot data** — status and criteria are as of the dataset pull; production needs a scheduled refresh.
- **NSCLC only**, diagnosis/gene/age/sex dimensions only.

## License
[MIT](clinicalTrialApp/LICENSE) © 2026 Bran Cantarel. Trial data from ClinicalTrials.gov (public domain); OncoTree © Memorial Sloan Kettering Cancer Center.
