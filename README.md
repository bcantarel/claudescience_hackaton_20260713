# ClaudeScience Hackathon 2026

Two independent projects built during the ClaudeScience hackathon (July 2026),
each exploring a different way computation meets biology and medicine:

| | Project | One-line summary |
|---|---|---|
| **1** | [**`geneNetworking/`**](geneNetworking/) — *Gene Regulation* | Which gene co-expression programs are conserved across the vertebrate tree, and is the transcription-factor control logic conserved with them? |
| **2** | [**`clinicalTrialApp/`**](clinicalTrialApp/) — *ClinicalTrialFinder* | A clinical-trial matching tool (web + native iOS) that surfaces candidate NSCLC trials for a physician to review, matching on diagnosis, gene profile, and eligibility. |

The two projects share no code and can be read independently. Each has its own
detailed README and design docs; this file is the orientation layer.

---

## 1. Gene Regulation — conserved co-expression & TF regulatory logic

**Directory:** [`geneNetworking/`](geneNetworking/) · **Full write-up:**
[`geneNetworking/README.md`](geneNetworking/README.md) ·
[`geneNetworking/FINDINGS.md`](geneNetworking/FINDINGS.md)

**The question.** Every animal builds many tissues from one genome; the
instructions live in *gene co-expression programs* — sets of genes switched on
together to make a liver, a neuron, an immune cell. Across the vertebrates,
which of these programs are conserved, does conservation simply fade with
evolutionary distance, and is the transcription-factor logic that drives each
program conserved too?

**The approach.** Learn the programs once in a well-powered human reference,
then test them everywhere else:

1. **Find the programs** — WGCNA on human GTEx (30 tissues, ~3,300 samples) →
   **27 tissue-defining co-expression modules**, marker-validated.
2. **Test conservation** — module preservation (`Zsummary`) across **26
   vertebrate species** spanning ~6–429 million years (human → fish).
3. **Read the regulators** — a 793-TF annotation and a 3-method ensemble
   gene-regulatory network on the conserved modules, extended with a
   single-cell arm (Tabula human/mouse/lemur + zebrafish outgroup).

**Key findings.**
- **Conservation is program-driven, not distance-driven** — a fish can share as
  much as a mouse (Spearman ρ = −0.24, n.s.). Core body-plan programs
  (brain, testis, ovary, muscle, immune) are kept in 77–100% of species;
  specialised programs (pancreas, lung, fat) are re-wired lineage-by-lineage.
- **The control logic is the conserved core** — which TFs run a program is
  better conserved than exactly which genes they wire to; one TF does different
  jobs by switching partners (FOXA1, PU.1 each control non-overlapping target
  sets across tissues).
- **The core reaches fish (~450 My)** — canonical mammalian master regulators
  recur at top ranks in zebrafish (MEF2D, PU.1, EBF3; p<0.02), confirmed at
  single-cell resolution.

Presentations: a full technical deck (`geneNetworking.pptx`) and a 5-slide
biology-audience summary (`geneNetworking_5slide_biology.pptx`).

**Environment.** Python 3.13 (`coexpr`) + R 4.5 (`phylo`); CPU-only, runs on
Apple Silicon. Data from recount3 GTEx, Bgee v15.2, FarmGTEx, Ensembl BioMart,
JASPAR 2024, and the CZ Biohub Tabula atlases.

---

## 2. ClinicalTrialFinder — clinical-trial matching (web + iOS)

**Directory:** [`clinicalTrialApp/`](clinicalTrialApp/) · **Full write-up:**
[`clinicalTrialApp/README.md`](clinicalTrialApp/README.md) · per-step design
findings in [`clinicalTrialApp/docs/`](clinicalTrialApp/docs/)

**What it is.** A decision-support prototype that helps a physician find
*candidate* NSCLC clinical trials for a patient by matching on diagnosis + gene
profile + age/sex. It produces **a ranked candidate list for independent
physician review — never an "eligible/ineligible" verdict and never an
auto-exclusion.** This is the clinically safe posture (the worst failure is
wrongly ruling a patient out of a trial) and the regulatorily defensible one
(display-for-review, per FDA 2022 CDS guidance). It is not a medical device and
gives no medical advice.

**How it works.** Deterministic where it can be, LLM only where it must be,
uncertainty surfaced rather than hidden:

```
Patient (OncoTree dx + genes + age + sex)
        │
        ▼
① DIAGNOSIS + STRUCTURED FILTER   (deterministic, auditable)
   OncoTree ancestor walk-up (patient LUAD → trial "NSCLC"/"Lung")
   + age + sex + recruiting status
        │
        ▼
② GENE CHECK                      (LLM interprets; cached per trial×gene)
   dictionary scan → section-aware classifier → direction
   (ALTERED_REQUIRED | WILD_TYPE_REQUIRED | ALTERATION_EXCLUDED | NOT_A_REQUIREMENT)
   × patient status → met / not met / unknown   (mapping is pure code)
        │
        ▼
③ RANK + SHOW   candidate trials, per-dimension basis + source sentence +
   full inclusion/exclusion criteria + trial link.  NEVER a verdict.
```

**Two front-ends, one matcher.**
- **Web** — a single self-contained static page (`clinicalTrialApp/app/index.html`);
  no PHI leaves the browser.
- **Native iOS (SwiftUI)** — an offline-first port ([`clinicalTrialApp/ios/`](clinicalTrialApp/ios/))
  that ships the trial+cache bundle (998 interventional NSCLC trials) embedded
  on-device so **no patient data ever leaves the phone**, with a silent remote
  refresh of the public trial data. Full feature parity with the web tool,
  including three-valued clinical-criteria matching (ECOG, brain mets, prior
  therapy/IO, labs). Xcode 16+, iOS 17.0 target.

**Design principles.**
- **Isolate the uncertain step** — the LLM only interprets which direction a
  criterion points; the met/not-met logic is a verified deterministic truth
  table, and every result cites the real trial sentence.
- **Cache the expensive work** — classify each (trial, gene) once (~1,563 cached
  classifications) so queries are instant.
- **Three-valued matching** — met / not met / **unknown**, never a silent pass/fail.
- **Rank-and-surface, never auto-exclude** — "not met" trials are ranked low, not hidden.
- **Physician in the loop** — a clinician validates before any patient-facing use.
- **Don't trust the "recruiting" flag** — the tool filters to interventional /
  not-past-completion and flags likely-stale trials, showing the physician the
  dates rather than hiding behind the status field.

**Honest limitations.** Gene-level, not variant-level (deliberate MVP scope —
right gene / wrong variant over-surfaces; the cited sentence is how the
physician catches it); NSCLC only; diagnosis/gene/age/sex dimensions; snapshot
data (production needs a scheduled refresh); not yet independently
accuracy-validated — a clinician review is the #1 open item. Test cases are
synthetic and de-identified.

---

## License
[MIT](clinicalTrialApp/LICENSE) © 2026 Bran Cantarel. Trial data from
ClinicalTrials.gov (public domain); OncoTree © Memorial Sloan Kettering Cancer
Center. Gene-expression data from recount3/GTEx, Bgee, FarmGTEx, Ensembl,
JASPAR, and CZ Biohub Tabula atlases under their respective terms.
