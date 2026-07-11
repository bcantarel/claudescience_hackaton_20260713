# ClinicalTrialFinder — iOS (SwiftUI)

A native iOS port of the ClinicalTrialFinder NSCLC MVP. Same matcher, same data,
same guardrails as the web tool — candidate list for physician review, never an
eligibility verdict; gene-level (not variant-level) matching; every biomarker
call cites the trial's source sentence.

## Build & run
1. Open `ClinicalTrialFinder.xcodeproj` in Xcode 16+ (developed on Xcode 26.6).
2. Select an iOS Simulator (e.g. iPhone 17) and press Run. No signing needed for
   the simulator. To run on a device, set your signing team in the target.
3. Deployment target: iOS 17.0.

Verified building and running in the iOS 26 Simulator.

## Architecture — hybrid (offline-first + remote refresh)
- **Offline-first:** the app ships with `ClinicalTrialFinder/bundle_full.json`
  (998 interventional NSCLC trials + gene classification cache) embedded as a
  resource. It loads and matches entirely on-device, so **no patient data ever
  leaves the phone** — the strong PHI posture the feasibility assessment argued
  for.
- **Refresh:** on launch, `DataStore.refresh()` fetches a newer copy of the same
  bundle (public trial data only) from a static URL and swaps it in if available;
  it falls back silently to the embedded copy when offline. Point `remoteURL` in
  `DataStore.swift` at wherever you host the bundle (currently the repo's GitHub
  raw path).

## Source map
- `Models.swift` — Codable models for the bundle (mirrors `src/05_build_bundle.py`).
- `Matcher.swift` — the matcher ported to Swift: OncoTree ancestor walk-up for
  diagnosis, age/sex filter, three-valued gene mapping. Deterministic; mirrors
  `src/matcher.py` and the web tool's JS.
- `DataStore.swift` — embedded + remote bundle loading (the hybrid logic).
- `ContentView.swift` — the UI (input card, ranked trial cards with per-dimension
  basis, biomarker badges + citations).
- `ClinicalTrialFinderApp.swift` — app entry point.
- `bundle_full.json` — embedded data (same file as `../src/data/bundle_full.json`).

## Parity status vs the web tool
Ported in this first pass: diagnosis (OncoTree walk-up) + age/sex, three-valued
gene-level biomarker matching with cited basis, trial detail chips (phase,
enrollment, dates, stale flag), sort (relevance / start date / recently updated),
hide-stale filter, and the hybrid refresh.

Not yet ported (web tool has these; next iteration): the clinical-criteria layer
(ECOG, labs, brain mets, prior therapy/IO), the "started on/after" date filter,
the collapsible full inclusion/exclusion criteria view, and flag/notes export.

## Guardrails (unchanged from the web tool)
Three-valued matching (met / not met / unknown); cite the source sentence for
every biomarker judgment; rank-and-surface, never auto-exclude; a clinician
validates before any patient-facing use. Not a medical device.
