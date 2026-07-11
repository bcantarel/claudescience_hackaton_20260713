# Step 5 — Thin UI + clinician-test harness

Deliverable: `app/index.html` (self-contained, no server). Current dataset: **998 interventional recruiting NSCLC trials, 1,563 cached (trial, gene) classifications** (original build was 150 trials / 556 classifications).

Bottom line: the MVP is clinician-testable end to end. A physician enters an OncoTree diagnosis + age/sex + gene profile directly (the 12 synthetic cases are one-click presets, not required) and gets a ranked candidate list with per-dimension basis, the cited source sentence for every biomarker call, inclusion/exclusion section, confidence, and a CT.gov link — plus study details, a stale-trial filter, and flag/note capture with JSON export. It never emits an eligibility verdict and never auto-excludes. What it is **not** yet is clinically validated.

## What was built
- **Classification cache:** biomarker gates classified once (section-aware) and stored as `{nct|GENE → direction, confidence, cited_span, section}` — the tool reads it instantly (no live LLM calls).
- **The tool:** JS reimplements the Python matcher exactly — OncoTree ancestor walk-up, age range (absent-max = no cap), sex, then three-valued biomarker mapping. Ranked MET → UNKNOWN → no-gate → NOT_MET. Prominent gene-level (not variant-level) disclaimer.
- **12 synthetic de-identified test cases** spanning common drivers, a driver-negative IO candidate, an elderly squamous case, NSCLC-NOS, a no-biomarkers case, and deliberately "EGFR T790M" to expose the gene-level false-positive limitation.

## Validation (headless browser)
Logic mirrors the Python and behaves correctly: EGFR-altered patients surface EGFR-required trials at top; driver-negative patients get the clean inverse; the T790M case produces the same matches as ex19del (the gene-level limitation, catchable only via the cited sentence); a no-biomarker patient gets all-UNKNOWN.

## Clinician-review protocol
1. Enter the 12 synthetic cases and 3–5 **real de-identified** cases via the controls (no PHI leaves the static file).
2. Review the top (MET) group first, then scan NOT_MET for **wrong exclusions** — the highest-priority failure mode. Flag questionable trials + add a note.
3. Export the review (JSON) after each case and send it back — it captures the query + flagged NCTs + notes.
4. Probe in priority order: (a) wrong NOT_MET; (b) variant mismatches surfaced as MET; (c) diagnosis mismatches; (d) missing trials.

## Update — expansion to full corpus + data-quality filtering
Prompted by a real observation: a surfaced trial was a retrospective **observational** study whose completion date was already >1 year in the past, yet still tagged "recruiting."

Measured across the 1,287 "recruiting" NSCLC trials:
- **222 (17%) are observational**, not interventional.
- **269 (20%) have a primary completion date in the past**; 98 (7%) have an overall completion date in the past — all still tagged recruiting.
- **28% not updated in >12 months**; 124 not updated in >2 years.

Changes:
- Searchable set expanded **150 → 998** (interventional only; overall-completion-passed excluded).
- Gene cache expanded **556 → 1,563** (classified 1,079 more snippets; 1,294 high-confidence, cited_span exact in 1,078/1,079).
- Study details surfaced on every card: phase, enrollment, start / primary-completion / last-update dates.
- **Staleness flag + filter:** 265/998 flagged likely-stale (primary completion passed, or not updated in >12 months); "Hide likely-stale trials" on by default, revealable with a ⚠ badge.

One bug caught and fixed during the rebuild: the first expanded bundle omitted age/sex fields, so the sex filter silently rejected every non-stale trial (0 results).

## Still open
- **Staleness is heuristic, not authoritative** — production needs a scheduled CT.gov refresh reading the verification date.
- Coverage is the interventional set, not literally all trials — pan-tumor baskets with no lung diagnosis tag are still out.
