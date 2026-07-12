# Future Directions — What the Original Plan Called For, What Was Done, and Why Not

The uploaded *Cross-Species TF Regulatory Network Analysis Plan* (Colossal Biosciences,
10 steps) is audited step-by-step below. The pilot completed the analyses that run on
data in hand; the deferred steps share one boundary — they need a **Linux remote-compute
host** and/or **>150 GB scratch** that the current environment (arm64 macOS, no GPU,
~13 GB scratch, `list_compute` empty) does not have.

---

## Original 10-step plan — completion audit

| Step | Plan called for | Status | Why / what was done instead |
|---|---|---|---|
| **1** | Per-species normalization (DESeq2 VST) | ✅ **Done (variant)** | CPM→log2 + variance filter to 14k genes; identical recipe across GTEx + mouse + 26 species. CPM/log2 substituted for DESeq2 VST — equivalent for co-expression, faster at 26-species scale. |
| **2** | Orthogroup expression matrix (fastOMA) | ❌ **Not done** | Used high-confidence **1:1 orthologs** instead. fastOMA needs 26 proteome downloads + heavy CPU; no remote compute. Consequence: TF table keys on human gene ID, not orthogroup ID. → **F1** |
| **3** | TF annotation (AnimalTFDB, JASPAR) | ✅ **Done** | 793 TFs, DBD families (InterPro), 892 JASPAR CORE motifs, expression breadth, tissue-activity. 4/5 fields; orthogroup ID deferred with Step 2. |
| **4** | Baseline GRN (multi-method + rank product) | ✅ **Done** | 3-method ensemble GENIE3 + GRNBoost2 + **CLR**, rank-product; 396,286 edges. *Deviation:* plan named ARACNE/PIDC; CLR substituted (documented). Adding ARACNE/PIDC → **F2**. |
| **5** | Promoter motif scan (FIMO −2kb/+200bp) | ❌ **Not done** | 26 genomes × ~20k promoters × ~800 PWMs — the compute-heaviest step; needs genome downloads + Linux compute. → **F3** |
| **6** | Expression–motif integration, TFBS turnover | ❌ **Not done** | Depends on the Step-5 motif tensor. Penalty-weighted LASSO / linear mixed model / ancestral-state reconstruction. → **F4**. *(Phase A phylogenetic-signal analysis is the co-expression-only analogue and IS done.)* |
| **7** | Combinatorial TF cocktails | ✅ **Done (pilot)** | XGBoost + SHAP interaction per module; recovered HNF / IKZF1–SPI1 / FOXM1–E2F2 codes. PARAFAC tensor decomposition + motif co-occurrence (need Steps 2/5) → **F5**. |
| **8** | Conservation scoring + phylogenetic signal | ✅ **Done** | Zsummary across 26 species + Blomberg K / Pagel λ (Phase A). Clade-stratified as far as data allows. |
| **9** | Module discovery via matrix factorization (NMF/LDA) | ⚠️ **Partial** | Modules came from **WGCNA** (co-expression clustering), not the plan's consensus-NMF/LDA. GO/KEGG functional annotation done; the matrix-factorization discovery + module-to-clade enrichment + top-20 heatmaps → **F6**. |
| **10** | Validation (ENCODE/ChIP-Atlas/DoRothEA) | ✅ **Done (partial)** | DoRothEA benchmark: AUROC 0.67–0.69, per-TF up to 0.93. Full ENCODE/ChIP-Atlas overlap + leave-one-species-out need genomes/orthogroups → **F7**. |

**Tally: 6 done (incl. variants), 1 partial, 3 not done.** Every "not done" is a
resource boundary, not a dead end — each maps to a future task below.

---

## Deferred work, specified for resumption

### F1. Orthogroup construction *(unblocks Step 2, and F2/F5/F7)*
Replace 1:1 orthologs with **orthogroups (OMA HOGs or fastOMA)**. TF families —
especially C2H2 zinc fingers, the family that carried the clade-variable signal —
have heavy lineage-specific copy-number variation that 1:1 mapping discards.
- **Lighter option:** OMA HOGs via the OMA REST API (no proteome download).
- **Plan-faithful option:** fastOMA on Ensembl proteomes for all 26 species.
- Closes the one outstanding Step-3 field (orthogroup ID on the TF table).
- **Resource:** Linux compute host. **First move when compute is added.**

### F2. Pooled cross-species GRN + named IT method *(Step 4 full version)*
Build the `orthogroup × (species × UBERON-tissue)` matrix (Bgee UBERON IDs as the
harmonised tissue key), re-run the ensemble GRN pooled across species, and add
**ARACNE or PIDC** (the plan's named information-theoretic method) alongside CLR.

### F3. Promoter motif scanning *(Step 5 — compute-heaviest)*
Ensembl GTF TSS → promoters (−2kb/+200bp) → **FIMO** (JASPAR vertebrate CORE, q<0.05)
→ binary `orthogroup × TF-motif × species` presence tensor. Embarrassingly parallel
per genome once downloaded. **Resource:** Linux compute + hours.

### F4. Expression–motif integration + TFBS turnover *(Step 6 — the novel core)*
Four-class per-species labelling (co-expression × motif); **penalty-weighted LASSO**
(motif lowers the penalty); **LMM** `target ~ TF + (1|clade)` to split conserved from
clade-specific regulation; **ancestral-state reconstruction** (phytools) to map TFBS
gain/loss on the tree. Extends Villar 2015 to multi-tissue. This is where the
"membership conserved, wiring drifts" result gets its sequence-level mechanistic test.

### F5. Combinatorial cocktails — full version *(Step 7 completion)*
Extend the pilot cocktails with **PARAFAC tensor decomposition** (tensorly) of the
orthogroup×species×tissue tensor and **motif co-occurrence** testing (needs F3).

### F6. Matrix-factorization module discovery *(Step 9 proper)*
Consensus **NMF** (k=10–40, cophenetic selection) / **LDA** on the pooled TF-target
matrix; module-to-clade enrichment tables; top-20-module heatmaps. Reconcile the
factorization-defined programs against the 27 WGCNA modules.

### F7. Full validation *(Step 10 completion)*
Full **ENCODE / ChIP-Atlas** overlap (beyond DoRothEA), motif-enrichment (needs F3),
and **leave-one-species-out** held-out prediction (needs F2's cross-species matrix).
Novelty scoring for high-conservation + sequence-supported + held-out-accurate edges
absent from gold standards.

### F8. Clade-gap expansion *(data acquisition)*
- **Marsupials (koala + Tasmanian devil):** feasible from SRA, ~161 GB raw fastq →
  salmon quant. Directly tests the **opossum low-preservation anomaly** (lowest
  mammal). Needs >150 GB scratch or a stream-and-discard host.
- **Afrotheria / Xenarthra (elephant, tenrec, armadillo):** documented **hard gap** —
  no replicated multi-tissue RNA-seq in public repositories. Elephant verdict was
  NEGATIVE (7 solid tissues, ~n=1 each). Revisit only if a new atlas is generated.

---

## Sequencing when a Linux compute host is available
```
F1 orthogroups ─► F2 pooled GRN ─┬─► F4 integration ─► F5 cocktails(full) ─► F7 validation(full)
                                 │
                 F3 motif scan ──┴──► F4                F6 NMF modules ──────┘
F8 clade expansion (marsupials) ─► feeds F2 (more species)
```
**First move: F1 (orthogroups)** — it unblocks F2/F5/F7 and closes the Step-3 gap.
F3 (motif scan) parallelizes once genomes are downloaded.

---
*The active pilot (this repo) established the co-expression + regulatory-logic
foundation on data in hand. F1–F8 turn it into the full genome-scale, sequence-grounded
cross-species regulatory analysis the original plan envisioned.*
