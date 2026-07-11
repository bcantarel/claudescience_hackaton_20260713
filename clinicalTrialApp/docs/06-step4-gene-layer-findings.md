# Step 4 — Gene layer (dictionary + scan + LLM classifier + three-valued matching)

Modules: `genes_dict.py`, `gene_scan.py` (section-aware), `classifier.py` (swappable LLM interface + deterministic mapping), `pipeline.py`.

Bottom line: the gene layer separates the trials an EGFR-mutant patient wants from the wild-type/immunotherapy trials a diagnosis-only match wrongly surfaces. The classifier handles messy phrasing well once given **section context** (inclusion vs exclusion), available on 97% of trials.

## What was built
- **Dictionary:** curated NSCLC panel (EGFR, ALK, ROS1, KRAS, MET, BRAF, RET, ERBB2/HER2, NTRK, NRG1) + PD-L1/TMB/MSI. **Two false-positive traps found & fixed:** "MET"/"neu" collide with English words — MET matched case-sensitively ("MET"/"c-Met", never "met"); "neu" alias dropped.
- **Scan:** query-time, patient's genes only; sentence-level snippets; therapy-phrase flag; **section tag** (inclusion/exclusion/unknown).
- **Classifier:** swappable `llm(prompt)->json`, strict schema (`direction` ∈ {ALTERED_REQUIRED, WILD_TYPE_REQUIRED, ALTERATION_EXCLUDED, NOT_A_REQUIREMENT} + confidence + cited_span). The **direction→patient mapping is pure code** (verified truth table) — the LLM never does the met/not-met logic.

## Classifier validation — good, with a caveat
On a 35-item stratified sample the classifier matched a hand read on 34/34 non-ambiguous items and flagged the one section-dependent snippet as low confidence. **Caveat: this was LLM-grading-LLM** — a design validation, not an independent accuracy benchmark. Expect ~87% (TrialGPT ceiling) in reality; only a clinician review gives a real number.

### Section context was the key fix
Single sentences lose inclusion/exclusion, which flips meaning ("no EGFR mutation" = wild-type-required under Inclusion, excluded under Exclusion). 97% of blobs carry both headers, so the extractor tags each snippet's section and feeds it to the classifier.

## The load-bearing finding: query-time cost
The plan assumed "a dozen calls." Reality for an EGFR patient: 510 of 1,216 shortlisted trials have an EGFR gating snippet → **753 classifier calls per query**. Minutes of latency, real cost.

**Fix — cache classification per (trial, gene), not per query.** A trial's EGFR requirement is identical for every EGFR patient. Classify once, reuse. This is the offline-batch extraction the feasibility doc recommended; the tool implements it.

## Known limitations (into step 5)
- **Gene-level false positives (by design):** EGFR T790M matches a trial wanting L858R — both resolve to MET. The cited sentence is how a physician catches it.
- **cited_span exactness:** verify the span is a verbatim substring; fall back to the whole snippet otherwise.
- **Cohort logic:** per-cohort biomarker rules classified at sentence level may miss cohort scoping.
