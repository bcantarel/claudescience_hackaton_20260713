# ClinicalTrialFinder — NSCLC MVP

A decision-support prototype that helps a physician find **candidate** non-small cell lung cancer (NSCLC) clinical trials for a patient by matching on **diagnosis + gene profile**, plus the free structured filters (age, sex, recruiting status).

> **This is a candidate-trial finder, not an eligibility engine.** It ranks and surfaces trials for a physician to review — it never outputs an "eligible / ineligible" verdict, and it never auto-excludes a patient from a trial. Every biomarker judgment cites the trial's own source sentence so a clinician can verify it. Biomarker matching is at the **gene level, not the variant level** (see [Limitations](#limitations)).

Built for the ClaudeScience hackathon (2026-07). Data from [ClinicalTrials.gov v2 API](https://clinicaltrials.gov/data-api/api) (public domain) and [OncoTree](https://oncotree.mskcc.org/) (diagnosis hierarchy).

---

## What it does

A physician enters a patient's:
- **Diagnosis** — picked from the OncoTree hierarchy (e.g. Lung Adenocarcinoma).
- **Age** and **sex**.
- **Gene profile** — a list of altered / wild-type genes (EGFR, ALK, KRAS, ROS1, MET, BRAF, RET, …).

…and gets a **ranked list of candidate trials**, each annotated with a per-dimension basis:
- **Diagnosis** — how the trial matches (exact / broader / narrower on the OncoTree tree).
- **Age / sex** — the trial's range and whether the patient falls in it.
- **Biomarker** — a **three-valued** result (**met / not met / unknown**) for each of the patient's genes, with the **cited source sentence** from the trial's eligibility criteria and whether it came from an inclusion or exclusion section.

Trials are ranked biomarker-**met** first, then unknown, then **not-met** (surfaced, not hidden), with a link to the full record on ClinicalTrials.gov.

## Try it now

Open **[`app/index.html`](app/index.html)** in any browser. It is a **single self-contained file** — no server, no build, no network. All 998 trials and 1,563 cached gene classifications are embedded.

- Enter a diagnosis + age + sex, click gene chips to cycle **— → altered → wild-type**, then **Find candidate trials**.
- The 12 preset "synthetic test cases" are one-click shortcuts for demoing; they are optional.
- "Hide likely-stale trials" is on by default (see [Data quality](#data-quality)).
- Flag trials and add notes, then **Export clinician review (JSON)** to capture feedback.

## Architecture

Everything runs at query time against a pre-computed cache — no per-query LLM calls in the shipped tool.

```
Patient (OncoTree dx + genes + age + sex)
        │
        ▼
① DIAGNOSIS + STRUCTURED FILTER   (deterministic)
   • OncoTree dx → match trials by MeSH/condition, walking the
     hierarchy UP (patient LUAD → trial "NSCLC" / "Lung")
   • age in [min,max]  ·  sex  ·  recruiting status
        │
        ▼
② GENE CHECK                      (cached; classified once per trial×gene)
   • dictionary scan of eligibilityCriteria for the patient's genes
   • therapy-phrase filter (drops "EGFR-TKI" prior-therapy mentions)
   • section-aware LLM classifier → direction:
       ALTERED_REQUIRED | WILD_TYPE_REQUIRED | ALTERATION_EXCLUDED | NOT_A_REQUIREMENT
   • deterministic map (direction × patient status) → met / not met / unknown
        │
        ▼
③ RANK + SHOW   candidate trials, each with per-dimension basis
   + source sentence + trial link.  NEVER an eligible/ineligible verdict.
```

Key design decisions (the "why" is documented in [`docs/`](docs/)):
- **Diagnosis matching is fully deterministic and auditable** — an OncoTree ancestor walk, so a leaf diagnosis matches trials tagged at any broader level.
- **The LLM only interprets language** (which direction a criterion points). The **met/not-met logic is pure code** (a verified truth table in `classifier.py`), so the uncertain step is isolated and every result is explainable.
- **Classifications are cached per (trial, gene)** — a trial's EGFR requirement is identical for every EGFR patient, so it is classified once (not per query). This is why the tool is instant.
- **Three-valued matching** surfaces uncertainty ("unknown") rather than hiding it.

## Repository layout

```
app/
  index.html              Self-contained tool (data embedded). Just open it.
  tool_template.html      Template the build injects data into.
src/
  oncotree.py             OncoTree loader + ancestor-walk lookup.
  crosswalk.py            CT.gov diagnosis (MeSH/condition) → OncoTree code.
  matcher.py              Hierarchical diagnosis + age/sex/status filter.
  genes_dict.py           Curated NSCLC gene/biomarker dictionary + synonyms.
  gene_scan.py            Section-aware eligibility-text scan + snippet extractor.
  classifier.py           Swappable LLM-classifier interface + deterministic mapping.
  pipeline.py             End-to-end: patient → shortlist → gene check.
  01_pull_ctgov.py …      Numbered scripts that rebuild the dataset (see below).
  classifier_instructions.txt   Prompt/rules used for snippet classification.
  data/                   Pre-built data the tool/pipeline read (see data note).
tests/
  verify_tool.js          Headless-browser checks of the shipped tool (Playwright).
docs/                     Design docs + honest findings for each build step.
```

## Rebuilding the dataset

The core code depends only on the **Python 3.9+ standard library** (`urllib`, `json`, `re`) — no pip installs required for the pipeline itself.

```bash
cd src
python3 01_pull_ctgov.py        # pull recruiting NSCLC trials from CT.gov v2 → data/nsclc_recruiting.json (~25 MB, not committed)
python3 02_analyze_corpus.py    # corpus stats (MeSH coverage, biomarker phrasing)
python3 03_select_subset.py     # extract gene-gating snippets to classify
#   → classification step: run each snippet through an LLM using
#     classifier_instructions.txt (in this build it was done with Claude).
python3 04_build_gene_cache.py  # assemble the {trial|gene → direction} cache
python3 05_build_bundle.py      # build the embedded data bundle (interventional, quality-filtered)
python3 06_gen_testcases.py     # regenerate the 12 synthetic test cases
```

The **classification step (between 03 and 04) requires an LLM** and is the only non-deterministic part. The finished cache (`data/gene_cache_full.json`) and embedded bundle (`data/bundle_full.json`) are committed so the tool works out of the box; you only need to re-classify if you refresh the trial set. The raw 25 MB CT.gov pull is intentionally **not committed** — regenerate it with `01_pull_ctgov.py`.

The browser tests use Node + Playwright: `node tests/verify_tool.js`.

## Data quality

CT.gov's "recruiting" status is not fully trustworthy, so the tool applies its own filters and shows the physician the dates. Measured on the 1,287-trial pull:
- 17% are **observational**, not interventional (excluded).
- 20% have a **primary completion date already in the past**; 7% have an overall completion date in the past — yet still tagged recruiting (past-completion excluded).
- 28% haven't been updated in over a year.

The shipped set is **998 interventional trials** whose overall completion date has not passed; **265 are flagged "likely stale"** (primary completion passed, or not updated in >12 months) and hidden by default, revealable with a ⚠ badge that explains why. This staleness flag is a **heuristic proxy**; a production system needs a scheduled refresh reading CT.gov's verification date.

## Limitations

This is an MVP. Stated plainly:
- **Gene-level, not variant-level.** A match means the patient's gene is *named* in the criteria — not that their specific variant qualifies (e.g. EGFR T790M will match a trial wanting EGFR L858R). This is deliberate MVP scope; the cited source sentence is how a physician catches the mismatch.
- **Not independently accuracy-validated.** The classifier was validated LLM-against-LLM during the build; a clinician review is the first real accuracy signal. Expect roughly the published TrialGPT ceiling (~87% criterion-level accuracy, with exclusion worse than inclusion).
- **NSCLC only**, and only the diagnosis / gene / age / sex dimensions. Prior therapy, ECOG, stage, brain mets, etc. are out of scope — the physician reads the full criteria via the CT.gov link.
- **Snapshot data.** Status and criteria are as of the dataset pull.
- **Pan-tumor biomarker baskets** that carry no lung diagnosis tag are not included (a documented recall trade-off).

## Guardrails (kept even in the MVP)

- Three-valued matching (met / not met / **unknown**) — surface uncertainty, never hide it.
- Cite the trial's source sentence for every biomarker judgment.
- Rank-and-surface; **never auto-exclude** a patient from a trial.
- A clinician validates before any patient-facing use. This is not a medical device and gives no medical advice.

## License

[MIT](LICENSE) © 2026 Bran Cantarel. Trial data is from ClinicalTrials.gov (US Government, public domain); OncoTree is © Memorial Sloan Kettering Cancer Center, used under its terms.
