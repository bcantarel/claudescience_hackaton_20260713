# Integrated Analysis Plan — Conserved Co-expression → Cross-Species TF Regulons

**Project:** Conserved gene regulatory architecture across vertebrates
**Substrate:** Human GTEx reference modules → preservation across 26 vertebrates (Bgee + recount3 + FarmGTEx)
**This plan merges:** (A) formal phylogenetic modelling of conservation, (B) the transcription-factor / regulon layer, and the remaining steps of the uploaded *Cross-Species TF Regulatory Network Analysis Plan* (Colossal Biosciences, 10 steps).

---

## 0. What is already built (the foundation)

| Plan step it satisfies | Completed work | Key artifacts |
|---|---|---|
| Step 1 (normalization) | recount3 GTEx: 30 tissues, 3,267 samples; CPM→log2, variance-filtered to 14,000 genes. Same recipe reused for every species. | `stage1_gene_modules.csv` |
| Step 9 (module discovery), co-expression variant | Human WGCNA: **27 modules**, 7,034 assigned genes, tissue-mapped + marker-validated (pancreas 6/6, liver/muscle/spleen 5/6). | `stage1_module_tissue.png`, `stage1_module_summary.csv`, `stage1_module_eigengenes.csv` |
| Independent validation | Mouse cross-check (ENCODE, 419 samples): 14/27 modules strongly preserved; **23/26 modules recovered by an independently-built mouse network**. | `stage2_mouse_crosscheck.png`, `stage2_mouse_preservation.csv` |
| Step 8 (conservation), empirical basis | Preservation sweep across **26 vertebrates**, 6–429 My, 12 clades (Zsummary per module per species). FarmGTEx cattle added as a tissue-coverage contrast. Assembly-mismatched species recovered via a gene-symbol ortholog bridge. | `stage2_crossspecies_preservation.png`, `stage2_species_preservation_summary.csv`, `stage2_module_conservation.csv`, `stage2_preservation_full.csv` |

**Established results that constrain the next phases**
- Conservation is **module-identity-driven, not distance-driven** (Zsummary vs divergence ρ=−0.24, n.s.). Germline/neural programs (testis M8/M7, brain M9, ovary M2, pituitary M3) are universally preserved; metabolic-tissue programs (pancreas M23, adipose M25/M11, lung M27) are labile even between close relatives.
- Decomposition signal: **Zdensity high, Zconnectivity ≈ 0** — module *membership* is conserved but intramodular *hub wiring* diverges. This is the single most important handle for the TF layer: if membership is conserved but wiring drifts, the drift should track TF-binding-site turnover (Step 6).

**Panel composition (decides Step 8 stratification):**
- 21 mammals (19 placental + platypus + opossum) + 5 non-mammal outgroups (birds, anole, frog, zebrafish).
- Stratifiable mammalian clades: **Euarchontoglires (12 sp.)**, **Laurasiatheria (7 sp.)**. **Afrotheria and Atlantogenata are absent** from Bgee RNA-seq — the plan's 4-way clade split collapses to a 2-way contrast + outgroups. (Elephant/tenrec/armadillo have no multi-tissue RNA-seq in Bgee; would need dedicated SRA acquisition.)

---

## 1. Four methodological reconciliations (uploaded plan ⇄ what we have)

The uploaded plan assumed a curated resource that differs from the public data we assembled. Four decisions bridge them; each is a place I need your call (see §6).

1. **1:1 orthologs → orthogroups for the TF layer.** Preservation used high-confidence 1:1 orthologs (cleanest topology). But the plan's TF work *needs* orthogroups (fastOMA/OMA HOGs), because TF families — especially C2H2 zinc fingers — have heavy lineage-specific copy-number variation that 1:1 mapping discards. **Recommendation:** keep 1:1 orthologs for the co-expression/phylogenetics layer (Phase A); switch to orthogroups (OMA HOGs via the OMA API, or fastOMA if we run it) for TF annotation and GRN inference (Phase B).

2. **Tissue harmonization is already solved by UBERON.** The plan flagged cross-species tissue matching as a challenge. Bgee annotates every library with a **UBERON anatomical-entity ID** — a harmonized cross-species ontology. This lets us build the plan's unified `orthogroup × (species × tissue)` matrix with genuinely comparable tissue columns, which the raw data would not support. Major enabler; adopt UBERON as the tissue key.

3. **Two co-expression objects, kept complementary.** Our per-species-network + Zsummary design answers "is this module preserved." The plan's design — one pooled `(species × tissue)` matrix, TFs predicting targets across it — answers "which TF drives which target, and where did that break." Both are valid and non-redundant: Phase A finishes on our object; Phase B builds the pooled matrix. The pooled matrix reuses the same ortholog/UBERON infrastructure.

4. **Scope: vertebrates, not just mammals.** We went broader than the plan's 30–50 mammals. For Phase B this is an asset — the non-mammal outgroups **polarize** TFBS gain/loss events (ancestral-state reconstruction needs an outgroup to root on). Clade-stratified GRN stays mammal-only; outgroups serve rooting and turnover direction.

---

## 2. PHASE A — Phylogenetic formalization of conservation *(plan Step 8; ready to run now)*

Uses the data already in hand (`stage2_preservation_full.csv` = module × species Zsummary). No new downloads.

**A1. Build the ultrametric species tree.** TimeTree divergence times (already tabulated for all 26 species) → an ultrametric tree via `ape`; cross-check topology against Ensembl Compara. Output: `species_tree.nwk`.

**A2. Phylogenetic signal per module.** Treat each module's per-species preservation (Zsummary, and separately the raw intramodular correlation strength) as a continuous trait on the tree. Compute **Blomberg's K** and **Pagel's λ** (`phytools`) per module, with a Brownian-motion null and randomization p-values. *Reads directly on the plan's Step 8 K>0.7 "core conserved regulon" criterion, lifted to module scale.*

**A3. Clade contrasts.** Euarchontoglires vs Laurasiatheria: per-module preservation difference, test for clade-specific lability. Outgroups anchor the ancestral state.

**A4. Conservation vs biology.** Correlate K/λ with module properties (tissue class, size, marker-gene identity) to test the hypothesis from our current result: *germline/neural modules show high K (Brownian, deeply constrained); metabolic modules show K≈0 (labile).*

**Deliverables:** `species_tree.nwk`, `phylo_signal_by_module.csv` (K, λ, p-values), a phylogeny-annotated figure (tree + per-module conservation heatmap), short methods note. **Compute: trivial, local. This is the natural immediate next step.**

---

## 3. PHASE B — Transcription-factor / regulon layer *(plan Steps 3–7, 9, 10)*

This is the large phase. It needs three new data ingredients, then five analysis stages.

### B0. Data prerequisites (acquisition)
| Ingredient | Source | Use | Notes |
|---|---|---|---|
| Orthogroups | OMA HOGs (API) or fastOMA on Ensembl proteomes | Step 2/3 — TF families across species | replaces 1:1 for TFs |
| TF catalogue | AnimalTFDB v4 (~1,600 human TFs) + TFclass families | Step 3 — flag TF orthogroups | map human TFs → orthogroups |
| Motif PWMs | JASPAR 2024 vertebrate CORE | Steps 5, 10 — FIMO scanning | TF→motif linkage |
| Genome assemblies + GTFs | Ensembl (all 26 species already Ensembl) | Step 5 — promoter extraction (−2 kb/+200 bp of TSS) | ~large download; per-species FASTA+GTF |
| Species tree | from A1 | Steps 6, 8 — turnover mapping | reuse |

### B1. TF annotation on orthogroups *(Step 3)*
Map AnimalTFDB TFs through orthogroups; attach JASPAR PWM per TF orthogroup; compute expression breadth; define the active-TF set per UBERON tissue. **Checkpoint decision:** report how many of ~1,600 TFs are recoverable in ≥80% of species — this sets the ceiling on the whole TF layer.

### B2. Baseline GRN inference *(Step 4)*
Build the pooled `orthogroup × (species × UBERON-tissue)` expression matrix (aggregation = max paralog, with mean as sensitivity check). Run **GRNBoost2** (arboreto) and **GENIE3**, plus one information-theoretic method (**ARACNE** or **PIDC**); ensemble by rank product. Sanity gate: liver must recover HNF4A/FOXA2, muscle MYOD/MEF2 orthogroups. Output: ranked TF→target edge list, per-tissue + pooled.

### B3. Promoter motif scanning *(Step 5)*
Extract promoters per species from Ensembl GTF TSS; **FIMO** (JASPAR PWMs, q<0.05) → binary `orthogroup × TF-motif × species` presence tensor; per-target motif-conservation scores. *This is the compute-heavy step (26 genomes × ~20k promoters × ~800 PWMs).*

### B4. Expression–motif integration + TFBS turnover *(Step 6 — the plan's novel core)*
Four-class per-species labelling (corr×motif); **penalty-weighted LASSO** (`glmnet`, motif lowers penalty); **linear mixed model** `target ~ TF + (1|clade)` to split conserved from clade-specific signal; **ancestral-state reconstruction** (`phytools`) to map TFBS gain/loss on the tree. Directly extends Villar et al. 2015 from liver-ChIP to multi-tissue co-expression. *This is where our "membership conserved, wiring drifts" result gets a mechanistic test.*

### B5. Combinatorial TF cocktails *(Step 7)*
Per-target **XGBoost + SHAP interaction** values for TF synergy; two-stage elastic net with pairwise TF×TF terms among top-50 candidates; **PARAFAC tensor decomposition** (`tensorly`) of the orthogroup×species×tissue tensor; motif co-occurrence test for candidate pairs. Output: ranked cocktail programs.

### B6. Module refinement + cross-validation with Phase-1 modules *(Step 9)*
Consensus **NMF** (k=10–40, cophenetic selection) and/or **LDA** on the pooled matrix; GO/KEGG annotation; **reconcile against the existing 27 WGCNA modules** (do TF-defined programs align with the co-expression modules?). Cocktail programs from B5 should reappear as multi-TF NMF components.

### B7. Validation & prioritization *(Step 10)*
Gold-standard AUROC/AUPRC vs **ENCODE / ChIP-Atlas / DoRothEA**; motif-enrichment of inferred regulons (FIMO/AME); **leave-one-species-out** held-out prediction; novelty scoring for high-conservation + sequence-supported + held-out-accurate edges absent from gold standards. Output: benchmarking report + shortlist of 10–20 candidate cocktail programs for experimental follow-up.

---

## 4. Dependency graph & sequencing

```
[DONE] Stage1 modules ─┬─► PHASE A (Step 8)  ── ready now, ~local, days
                       │
                       └─► B0 data ─► B1 TF annot ─► B2 GRN ─┬─► B4 integration ─► B5 cocktails ─► B7 validation
                                            │                │
                              B3 motif scan ┴────────────────┘         B6 NMF modules ─────────────┘
```
- **Phase A is independent** and uses current data → do first.
- **B3 (motif scan) parallelizes** with B1–B2 once genomes are downloaded.
- **B4 depends on B2 + B3**; B5/B6 depend on B2; B7 depends on B4–B6.

## 5. Compute reality
Local host is arm64 macOS, no GPU, and `list_compute` is currently empty. Phase A and B1 are light. **B2 (GRNBoost2 across ~20k targets) and B3 (FIMO across 26 genomes) are heavy** — hours to days locally. If you can add a Linux remote-compute target (Customize → Compute), those two steps should be dispatched there; otherwise I scope them down (e.g. restrict targets to expressed genes and TFs to the active set per tissue) to stay local-feasible.

## 6. Decisions I need from you
1. **Start Phase A now?** (recommended — it's ready, cheap, and directly answers "is co-expression conservation phylogenetically structured.")
2. **Orthogroup source for Phase B:** OMA HOGs via API (faster, no proteome download) vs run fastOMA ourselves (matches your original plan exactly). 
3. **TF-layer scope first pass:** full pooled GRN (B2 across all genes) vs a **focused pilot** — take the 4–5 most-conserved and 2–3 most-labile modules and run the TF/motif/cocktail pipeline on just those, as a proof-of-concept before the genome-wide run.
4. **Remote compute:** will you add a Linux host for B2/B3, or should I scope them for local?
5. **Mammal-only vs keep outgroups** for the GRN matrix (outgroups help polarize turnover but add assembly/annotation heterogeneity).
