> SUPERSEDED — the canonical, plan-audited version is `../FUTURE_DIRECTIONS.md` at the repo root. This file is retained for the F1–F8 task detail.

# Future Directions — Genome-Scale Cross-Species Regulatory Layer (Tier 2)

**Status:** deferred. These steps need resources not available in the current
environment: a **Linux remote-compute host** (arm64 macOS local, no GPU,
`list_compute` empty) and/or **>150 GB scratch** (sandbox has ~13 GB). They are
fully specified here so the work can resume when compute is provisioned.

The active work (Tier 1 + 3) is in `analysis_plan_active.md`. This plan is what
turns the human-reference pilot into the genuinely cross-species regulatory
analysis the uploaded Colossal plan envisioned.

---

## Why these are deferred (the resource boundary)

| Step | Bottleneck | Requirement |
|---|---|---|
| Orthogroup construction | fastOMA on 26 proteomes is CPU-heavy | Linux compute host |
| Promoter motif scanning | FIMO: 26 genomes × ~20k promoters × ~800 PWMs | Linux compute + hours |
| Marsupial acquisition | ~161 GB raw fastq → salmon quant | >150 GB scratch or streaming host |

---

## F1. Orthogroup construction *(plan Step 2 — unblocks the cross-species TF layer)*
Replace 1:1 orthologs with **orthogroups (OMA HOGs or fastOMA)**. TF families —
especially C2H2 zinc fingers — have heavy lineage-specific copy-number variation
that 1:1 mapping discards, so the TF layer genuinely needs orthogroups.
- **Option A (lighter):** OMA HOGs via the OMA REST API — no proteome download.
- **Option B (matches uploaded plan):** run fastOMA on Ensembl proteomes for all 26 species.
- Output: `orthogroup_table.csv` (orthogroup ID ↔ per-species gene IDs).
- **Unblocks:** the one outstanding plan Step-3 field (orthogroup ID on the TF
  annotation table), and the pooled cross-species GRN matrix.

## F2. Pooled cross-species GRN matrix *(plan Step 4, full version)*
Build the `orthogroup × (species × UBERON-tissue)` expression matrix (max-paralog
aggregation, mean as sensitivity check), using Bgee's UBERON anatomical IDs as the
harmonized tissue key. Re-run the 3-method ensemble GRN on this pooled matrix
(vs the current human-only GRN). Adds one **information-theoretic method matching
the uploaded plan's named options (ARACNE or PIDC)** alongside the CLR already run.

## F3. Promoter motif scanning *(plan Step 5 — the compute-heavy step)*
Extract promoters per species from Ensembl GTF TSS (−2 kb/+200 bp); **FIMO**
(JASPAR 2024 vertebrate CORE, q<0.05) → binary `orthogroup × TF-motif × species`
presence tensor + per-target motif-conservation scores.
- ~26 genomes downloaded (large), then embarrassingly parallel per genome.
- **Dispatch target:** Linux compute host.

## F4. Expression–motif integration + TFBS turnover *(plan Step 6 — the novel core)*
Four-class per-species labelling (co-expression × motif presence); **penalty-weighted
LASSO** (`glmnet`, motif lowers the penalty); **linear mixed model**
`target ~ TF + (1|clade)` to separate conserved from clade-specific regulation;
**ancestral-state reconstruction** (`phytools`) to map TFBS gain/loss on the species
tree. Directly extends Villar et al. 2015 (liver ChIP) to multi-tissue co-expression.
This is where the "membership conserved, wiring drifts" result gets its mechanistic test.

## F5. Combinatorial cocktails — full version *(plan Step 7 completion)*
Extends the Tier-1 XGBoost/SHAP cocktails with: **PARAFAC tensor decomposition**
(`tensorly`) of the orthogroup×species×tissue tensor, and **motif co-occurrence**
testing of candidate TF pairs (needs F3). Tier 1 delivers the human-level cocktails;
this makes them cross-species and sequence-grounded.

## F6. Module refinement *(plan Step 9, pooled)*
Consensus **NMF** (k=10–40, cophenetic selection) / **LDA** on the pooled matrix;
reconcile TF-defined programs against the existing 27 WGCNA modules.

## F7. Full validation *(plan Step 10 completion)*
Full **ENCODE / ChIP-Atlas** overlap (beyond DoRothEA), motif-enrichment via
FIMO/AME (needs F3), and **leave-one-species-out** held-out prediction (needs the
cross-species matrix from F2). Novelty scoring for high-conservation +
sequence-supported + held-out-accurate edges absent from gold standards.

## F8. Clade-gap expansion *(data acquisition)*
- **Marsupials** (koala + Tasmanian devil): feasible from SRA (koala 5 tissues incl.
  brain/liver/spleen/testis; devil 3 normal tissues). ~161 GB raw fastq → salmon quant.
  Directly tests the **opossum low-preservation anomaly** (lowest-preservation mammal).
  Needs a host with >150 GB scratch or stream-and-discard quantification.
- **Afrotheria / Xenarthra** (elephant, tenrec, armadillo): **documented gap** — no
  replicated multi-tissue RNA-seq in public repos. Elephant feasibility verdict was
  NEGATIVE (7 solid tissues, ~n=1 each, below the co-expression replication floor).
  Revisit only if a multi-tissue atlas is published or generated.

---

## Sequencing when compute is available
```
F1 orthogroups ─► F2 pooled GRN ─┬─► F4 integration ─► F5 cocktails(full) ─► F7 validation(full)
                                 │
                 F3 motif scan ──┴──► F4                F6 NMF modules ──────┘
F8 clade expansion (marsupials) ─► feeds F2 (more species)
```
First move when a Linux host is added: **F1 (orthogroups)** — it unblocks F2/F5/F7
and closes the one outstanding Step-3 field. F3 (motif scan) parallelizes once genomes
are downloaded.
