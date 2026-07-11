# Design docs & build findings

These document the design decisions and honest findings from each build step.
They are written to be read in order.

- `01-feasibility-and-architecture.md` — scope, data reality, extraction problem, licensing/regulatory constraints, proposed architecture.
- `02-build-plan.md` — the locked-in MVP plan and step breakdown.
- `03-step1-ctgov-findings.md` — CT.gov v2 pull; MeSH tagging + biomarker phrasing read.
- `04-step2-oncotree-findings.md` — OncoTree load + ancestor-walk lookup; the MeSH↔UMLS crosswalk gap.
- `05-step3-matcher-findings.md` — diagnosis crosswalk (98% coverage) + hierarchical matcher + structured filters.
- `06-step4-gene-layer-findings.md` — gene dictionary, section-aware scan, LLM classifier, three-valued matching; the query-time-cost finding.
- `07-step5-ui-and-clinician-test.md` — the thin UI, clinician-test protocol, corpus expansion, and data-quality filtering.
- `08-known-issues-criteria-normalization.md` — **known issues & future work** for the free-text → structured criteria normalization pipeline (diagnosis, biomarker, clinical criteria). Read this before extending the extractors.
