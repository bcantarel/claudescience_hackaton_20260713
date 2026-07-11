# ClinicalTrialFinder — iOS (SwiftUI)

A native iOS port of the ClinicalTrialFinder NSCLC MVP. Same matcher, same data,
same guardrails as the web tool — candidate list for physician review, never an
eligibility verdict; gene-level (not variant-level) matching; every biomarker and
criterion call cites the trial's source sentence.

## Build & run
1. Open `ClinicalTrialFinder.xcodeproj` in Xcode 16+ (developed on Xcode 26.6).
2. Select an iOS Simulator (e.g. iPhone 17) and press Run. No signing needed for
   the simulator. To run on a device, set your signing team in the target.
3. Deployment target: iOS 17.0.

Verified building and running in the iOS 26 Simulator.

## Architecture — hybrid (offline-first + remote refresh)
- **Offline-first:** the app ships with `ClinicalTrialFinder/bundle_full.json`
  (998 interventional NSCLC trials + gene & criteria caches) embedded as a
  resource. It loads and matches entirely on-device, so **no patient data ever
  leaves the phone** — the strong PHI posture the feasibility assessment argued
  for.
- **Refresh:** on launch, `DataStore.refresh()` fetches a newer copy of the same
  bundle (public trial data only) from a static URL and swaps it in if available;
  it falls back silently to the embedded copy when offline. Point `remoteURL` in
  `DataStore.swift` at wherever you host the bundle (currently the repo's GitHub
  raw path).

## Source map
- `Models.swift` — Codable models for the bundle (mirrors `src/05_build_bundle.py`),
  including the clinical-criteria cache.
- `Matcher.swift` — the matcher ported to Swift: OncoTree ancestor walk-up for
  diagnosis, age/sex filter, three-valued gene mapping, and three-valued
  clinical-criteria matching (ECOG, brain mets, prior therapy/IO, labs). Plus the
  started-on/after and hide-fails filters. Deterministic; mirrors `src/matcher.py`
  and the web JS.
- `DataStore.swift` — embedded + remote bundle loading (the hybrid logic).
- `ContentView.swift` — the UI (input card, clinical-criteria inputs, ranked trial
  cards with per-dimension basis + citations, full inclusion/exclusion disclosure,
  flag/notes + review export).
- `ClinicalTrialFinderApp.swift` — app entry point.
- `bundle_full.json` — embedded data (same file as `../src/data/bundle_full.json`).

## Feature parity vs the web tool — complete
- Diagnosis (OncoTree walk-up) + age/sex.
- Three-valued gene-level biomarker matching with cited basis + section.
- Clinical criteria (optional): ECOG, prior treatment, brain/CNS mets, prior
  immunotherapy, and labs — each matched to met/not-met/unknown with cited basis.
  **Labs are annotation-grade — the UI stamps "verify units" (source data mixes
  g/dL vs g/L, mg/dL vs ×ULN).**
- Sort (biomarker relevance / start date newest-oldest / recently updated).
- Filters: started-on/after year, hide likely-stale, and hide-trials-patient-fails
  (off by default — never auto-excludes).
- Collapsible full inclusion/exclusion criteria per trial.
- Flag + clinician note per trial, exportable as JSON via the share sheet.

## Guardrails (unchanged from the web tool)
Three-valued matching (met / not met / unknown); cite the source sentence for
every judgment; rank-and-surface, never auto-exclude; a clinician validates
before any patient-facing use. Not a medical device.

## Known limitation carried from the pipeline
This is a UI over the same extraction — it does not change accuracy. See
`../docs/08-known-issues-criteria-normalization.md`. The clinician accuracy
review remains the #1 open item.
