# Analysis Plan — Single-Cell Refinement of the TF Regulatory Layer

**Project:** Conserved gene regulatory architecture across vertebrates
**This plan:** add a **cell-type-resolved** layer to the existing bulk TF work, using
cross-species single-cell atlases, to answer the core question at the resolution
where regulation actually lives — *which cocktail of TFs regulates which genes, in
which cell type, and where does that logic vary across species.*
**Substrate carried over:** human GTEx WGCNA modules (27) → preservation across 26
vertebrates → Phase A phylo-signal → Phase B ensemble GRN + SHAP cocktails (793 TFs).

---

## 0. Why single-cell, and what it fixes

The bulk pipeline is well-powered but has two limitations it flagged itself:

1. **Composition confound.** A tissue-level co-expression edge cannot separate
   *within-cell-type co-regulation* (TF and target co-vary inside the same cell —
   real regulation) from *cell-composition covariation* (TF and target both mark the
   same cell type, so they correlate across bulk samples that differ in that cell
   type's abundance — an artifact). A "cocktail of TFs" is by definition a
   within-cell-type object; bulk regulons are cell-type mixtures.
2. **Wiring vs membership (the repo's own key result).** Preservation showed
   **Zdensity high, Zconnectivity ≈ 0** — module *membership* conserves but
   intramodular *hub wiring* appears to diverge across species. That divergence could
   be genuine regulatory rewiring **or** an artifact of species differing in cell
   composition. Only cell-type resolution can tell these apart.

**What the single-cell layer delivers on top of the bulk work**

| Bulk deliverable (done) | Single-cell refinement (this plan) |
|---|---|
| WGCNA modules, tissue-mapped | **Which cell type(s) drive each module** (deconvolution) — resolves composition confound |
| Ensemble GRN, 396k edges | **Per-cell-type regulons** (pySCENIC) — TF→target within a cell type, motif-pruned |
| SHAP TF cocktails per module | **Cell-type cocktails** — cooperative TFs inside a defined cell type, not a tissue average |
| Phase A: conservation is deep/uniform (K≪1) | **Cell-type regulon conservation** across human/mouse/lemur — does membership conserve while wiring drifts, at the resolution where wiring lives |
| Deferred FIMO motif layer | **Partial motif delivery for free** — pySCENIC's cisTarget step prunes edges to motif-supported ones |

This maps onto the attached 10-step plan: single-cell sharpens **Step 4** (TF→target),
**Step 5/6** (motif support & context-dependence), **Step 7** (cocktails), and
**Step 10** (validation), and it does so at cell-type resolution rather than tissue
average.

---

## 1. Data — matched cross-species single-cell atlases

The **Tabula** family is the ideal substrate: three multi-organ atlases from one
consortium (CZ Biohub), so cross-species comparison is free of the protocol/batch
confounds that wreck cross-study single-cell integration. All are **openly
downloadable as processed count matrices from CELLxGENE Discover** (`.h5ad`), even
where the raw human reads are access-controlled.

| Atlas | Species | Tree position | Datasets | Cells | Tissues |
|---|---|---|---:|---:|---:|
| Tabula Sapiens | *Homo sapiens* | reference | 35 | ~3.4M | 75 |
| Tabula Muris Senis | *Mus musculus* | ~90 My from human | 42 | ~1.1M | 23 |
| Tabula Microcebus | *Microcebus murinus* (mouse lemur) | ~70 My, basal primate | 27 | ~0.5M | 40 |

- **15 tissues are shared across all three**; **9 map directly onto the GTEx WGCNA
  module panel** and are present in all three atlases (liver, muscle, spleen,
  pancreas, lung, kidney, heart, bone marrow, adipose). This is the cross-species
  cell-type comparison set. *Note:* testis and ovary are present in Tabula Sapiens
  and Tabula Microcebus but **absent from Tabula Muris Senis**, so the germ-cell
  modules (M8 testis, M2/M5 ovary) and the testis FOXM1×E2F2 cocktail can be
  reconciled across **human + lemur only** (2-species), not all three — flagged in
  SC1.4/SC2.1 below.
- **Cell-type labels are already ontology-mapped** (Cell Ontology `CL:` terms) in
  each atlas — the cross-species linkage for cell types, analogous to the 1:1
  ortholog bridge used for genes in the bulk pipeline.
- Source: CELLxGENE Discover curation API (`api.cellxgene.cziscience.com`); each
  dataset's `.h5ad` asset is a direct download. **Track C outgroup:** zebrafish
  (*Danio rerio*, 2.4M cells, *developmental* atlas — no adult stage) used only as a
  narrow deep-divergence positive control in SC2.3, not as a peer of the adult Tabula
  set.

**Gene linkage.** Reuse the existing Ensembl BioMart 1:1-ortholog bridge from the bulk
pipeline (human↔mouse; human↔lemur via the primate ortholog set). Cell-type-level
work is done per species first, then linked through orthologs — no new orthogroup
construction required for the Tabula three-species core.

---

## SC-TIER 1 — Cell-type regulatory logic on data in hand *(local-feasible)*

### SC1.1 — Acquire, QC, and harmonize the three atlases ✅ **DONE (4 tissues)**
Download the Tabula human/mouse/lemur `.h5ad` matrices; standardize gene IDs to the
BioMart ortholog space; harmonize cell-type annotations to shared `CL:` terms and
collapse to a common ~20–30-cell-type panel present across species.
- **Methods:** scanpy load; standard QC (min genes/cell, mito fraction, doublet
  flag); per-tissue cell-type frequency table; ortholog subsetting.
- **Figure:** `sc_atlas_overview.png` — cells per tissue × cell type × species,
  plus a shared-cell-type coverage matrix (which of the common cell types are
  present in each species/tissue).
- **Output:** harmonized per-species `AnnData` (cell-type + tissue + ortholog gene
  IDs); `sc_celltype_panel.csv`. Compute: local (streamed/subsampled per tissue).
- **Results (executed):** matched-tissue download avoids the 136 GB Tabula Sapiens
  bulk — **liver + spleen + lung + bone marrow trios = 9.5 GB, 357k cells** total.
  Cell types harmonized via **Cell Ontology hierarchical ancestors** (OLS4): 94/96
  fine `CL:` terms rolled to a **34-type broad panel** (0% unmapped human/mouse,
  ≤12.7% lemur). Gene space: **14,073 three-way 1:1 orthologs** present in all
  matrices (≈ the bulk 14k variance-filtered network — same gene space).
  **Shared cell types (≥20 cells in all 3 species): lung 17, bone marrow 8, spleen
  6, liver 4; 21 distinct across tissues.** Hepatocyte well-powered (7.4k/2.9k/458
  h/m/l) — the Phase B HNF4A/HNF1A test cell type. Artifacts: `sc_atlas_overview.png`,
  `celltype_harmonization_map.csv`, `harmonized_celltype_panel.csv`,
  `shared_celltype_summary.csv`, `ortholog_triples_usable.csv`, `sc1_qc.csv`.
  *Env note:* scanpy's numba-JIT import fails under the sandbox wrapper; `anndata`
  alone handles all `.h5ad` I/O here (relevant for SC1.3 pySCENIC).

### SC1.2 — Cell-type deconvolution of the bulk WGCNA modules *(resolves the composition confound)*
For each conserved bulk module, ask **which cell type(s) actually carry it**.
- **Methods:** build per-cell-type **pseudobulk** (sum counts per cell type ×
  tissue × donor); score each WGCNA module's gene set as a cell-type signature
  (mean expression / AUCell). A module whose genes are high in one cell type across
  many tissues was a *composition* signal in bulk; a module whose genes co-vary
  *within* a cell type is genuine co-regulation.
- Cross-reference with Phase A: are the **labile, phylo-signal modules**
  (M3 pituitary, M14 spleen, M20 testis, M5 ovary, M11 adipose) the ones dominated
  by a single, composition-variable cell type?
- **Figure:** `sc_module_celltype_deconv.png` — module × cell-type enrichment
  heatmap, modules ordered by their Phase A K statistic, annotated with
  "within-cell-type" vs "composition-driven" call.
- **Output:** `sc_module_celltype_assignment.csv` (per module: driver cell type(s),
  within-vs-composition flag, agreement with tissue mapping). Compute: local.

#### SC1.2b — Tissue widening to rescue phylo-signal modules ✅ **DONE**
The 4-tissue pilot could only evaluate 5/27 modules. To reach the **significant
phylo-signal modules** (Phase A K_p<0.05 or λ_p<0.05: M3 pituitary K_p=0.002, M20
testis K_p=0.007, M24 uterus λ_p=0.018, M5 ovary K_p=0.041, M11 adipose K_p=0.041;
M14 spleen already done), added 7 tissues (testis, ovary, muscle, adipose, pancreas,
uterus, pituitary) from the same three Tabula atlases. Efficient acquisition: picking
the smallest bundle covering each tissue = **6.6 GB** (14 files) rather than the naive
~17 GB; extracted per-cell-type pseudobulk, then deleted raw bundles. Widened master
pseudobulk = **1,116 profiles × 12,006 orthologs** across 11 tissues.
- **Availability is the binding constraint — most phylo-signal tissues are missing from
  ≥2 of the 3 atlases:** pituitary exists **lemur-only**; ovary **human-only**; testis
  human+lemur (no mouse); uterus human+lemur. Only adipose, muscle, pancreas exist in
  all three.
- **Result (with a power filter — profiles≥6 in the driver cell type, ≥2 species,
  0≤retention≤1.05 to reject small-sample artifacts):** of the newly-covered modules,
  **only M11 (adipose) clears the bar** — 3-way, 20 profiles, and it is
  **composition-driven** (endothelial-cell-enriched, coherence retention 0.18; the
  adipose phylo-signal reflects vascular/stromal composition, not within-adipocyte
  co-regulation). M24 (uterus, 2-way), M20 (testis, 2-way, 0–3 profiles/cell type),
  and the muscle modules (M18/M17/M12) are **evaluable in principle but underpowered**
  — retention>1 artifacts or too few per-cell-type profiles — so no trustworthy call.
  M3 pituitary and M5 ovary remain **not evaluable** (single-species only).
- **Bottom line — phylo-signal modules are heterogeneous in what drives them.** The
  two trustworthy verdicts point in *opposite* directions, and that contrast is the
  scientific payload: **M14 (spleen/plasma cell) is a HIGH-phylo-signal module (K=0.398,
  K_p=0.004 — second-highest K of any significant module) AND shows genuine conserved
  within-cell-type regulation** (XBP1 as the conserved plasma-cell master regulator, all
  three species; SC1.3). **M11 (adipose) is also significant (K_p=0.041) but is
  composition-driven** (endothelial/stromal, not within-adipocyte). So phylogenetic
  signal at the tissue level can reflect *either* conserved cell-intrinsic regulation
  (M14) *or* conserved tissue composition (M11) — and single-cell is exactly what
  distinguishes them. A properly-powered test of the remaining strongest phylo-signal
  modules (M3 pituitary K_p=0.002, M20 testis K_p=0.007) is **data-limited, not
  method-limited**: it needs atlases these three consortia did not sample at depth
  (SC-Tier 4 upgrade path).
- **Artifacts:** `sc_widened_phylo_deconv.png`, `sc12_widened_deconv.csv` (per module:
  driver cell type, retention, call, profile power, trustworthy flag),
  `pseudobulk_widened.parquet` (checkpoint), `pseudobulk_widened_meta.csv`.

### SC1.3 — Per-cell-type regulon inference *(plan Steps 4–6, cell-type resolution)* ✅ **DONE (pilot: M14 plasma cell, M13 hepatocyte × 3 species)**
Infer TF→target regulons **inside each cell type**, motif-pruned — the single-cell
analog of the bulk ensemble GRN.

- **Results (executed).** Reused Phase B TF panel (793 TFs; **564 in the 3-way
  ortholog space**) and the top SHAP cocktails as targets. Inferred regulons for the
  two evaluable pilot cell types (plasma cell/M14, hepatocyte/M13) in human/mouse/lemur
  by regressing each **module gene** on the TF panel (module-restricted GRNBoost2, ≤1500
  cells/type, seed 0). **Sanity gate passes strongly:** the recovered plasma-cell
  master regulators are **XBP1 (rank 1 in all 3 species), PRDM1/BLIMP1, CREB3L2** —
  textbook plasma-cell identity TFs. Cross-species conserved top-15 regulators:
  **M14 = XBP1, MEF2C, MXD4; M13 = MLXIPL, NFIA.**
  **Key refinement finding (species-specific, not uniform):** the *bulk* SHAP cocktail
  TFs demote at single-cell resolution **primarily in human** — all four (M14 IKZF1=58,
  IRF4=120; M13 NR1I3=64, ATF5=32) fall beyond top-15, displaced by XBP1/PRDM1 (M14) and
  CUX2/NFIA (M13). In **mouse and lemur they are largely retained** near the top (M14
  IKZF1 rank 7/9, IRF4 42/3; M13 NR1I3 5/10, ATF5 3/15) — 7 of 12 cocktail-TF×species
  cells sit within top-15. So the composition-confound correction is strongest in the
  human spleen/liver (where the bulk cocktail most overstated the within-cell-type
  regulator), and weaker in the other two atlases. XBP1 is the one regulator that is
  rank-1 within plasma cells in **all three** species (PRDM1/BLIMP1 is top-ranked in
  human+lemur but absent from the mouse top-25). SC1.4 quantifies this reconciliation
  per cocktail and per species.
- **Env / method note (important).** pySCENIC's `arboreto`/GRNBoost2 requires a **dask
  distributed cluster, which the sandbox blocks** (`LocalCluster` → "Operation not
  permitted", no socket spawn). Ran the **equivalent GBM-regression core** directly with
  scikit-learn `GradientBoostingRegressor` (validated on a synthetic planted network:
  recovers the true regulator at importance ~0.9 vs <0.05 noise). Motif pruning
  (cisTarget) and AUCell remain **SC-Tier 4** — cisTarget DBs are human/mouse only
  (no lemur), so cross-species motif pruning was always deferred; the co-expression
  regulon + existing JASPAR/DoRothEA support layer (SC-Tier 3) is the motif evidence here.

**Original spec (retained for SC-Tier 4 full run):**
- **Methods:** pySCENIC per species: GRNBoost2 (co-expression adjacencies) →
  cisTarget motif enrichment (prunes to motif-supported targets, using JASPAR/
  cisTarget databases for human & mouse; human motifs as proxy for lemur) → AUCell
  regulon activity per cell. This is exactly the pySCENIC tool named in the plan's
  appendix.
- **Compute realism (no remote compute configured):** run on **subsampled cells per
  cell type** (e.g. ≤2,000 cells/type/tissue) or on **metacells** to stay within the
  local arm64 budget; full all-cell pySCENIC across all species is deferred to
  SC-Tier 4. Keep the subsampling seed fixed and report a stability check.
- **Figure:** `sc_regulon_activity.png` — regulon × cell-type AUCell heatmap
  (human), with canonical master regulators (HNF4A hepatocyte, SPI1/IKZF1 immune,
  MYOD myocyte) flagged as a sanity gate mirroring the bulk GRN gate.
- **Output:** per-species regulon table (TF, motif-supported targets, cell-type
  activity), `sc_regulons_<species>.csv`. Compute: local, subsampled.

### SC1.4 — Bulk ↔ single-cell reconciliation *(refines the existing networks — the immediate payoff)* ✅ **DONE (pilot: M14/M13 cocktails × 3 species)**
Ask which bulk ensemble-GRN edges and SHAP cocktails **survive at within-cell-type
resolution**, and which were composition artifacts.

- **Results (executed).** Scored the top-12 SHAP cocktail pairs of each pilot module
  (M14 plasma cell, M13 hepatocyte) for within-cell-type support in each species.
  A pair is **genuine** if both TFs rank ≤30 in the cell-type regulon AND co-regulate
  ≥2 shared module targets; **composition/weak** otherwise; **untestable** if either TF
  lacks a 3-way 1:1 ortholog. Of 24 top pairs, **16 are testable** (8 untestable —
  BHLHA15, HHEX, ZNF552, ZNF738 have no 3-way ortholog; notably BHLHA15 removes M14's
  single strongest bulk pair IKZF1×BHLHA15 from cross-species testing).
  **Headline reconciliation findings:**
  1. **MLXIPL×NR1H4 (M13 hepatocyte) — genuine in ALL three species**, yet bulk
     *under*-ranked it (SHAP 0.20). Single-cell surfaces a robustly conserved hepatocyte
     cocktail the bulk SHAP ranking buried — a genuine network *addition*, not just a
     filter.
  2. **NR1I3×ATF5 (M13, top liver bulk cocktail, SHAP 1.11) — genuine in mouse+lemur,
     composition/weak in human.** The NR1H4-partnered variants (NR1I3×NR1H4, ATF5×NR1H4)
     are also genuine in mouse+lemur — a consistent NR1I3/ATF5/NR1H4 hepatocyte program
     outside human.
  3. **IKZF1×IRF4 (M14, top spleen bulk cocktail, SHAP 1.15) — genuine in lemur only**,
     composition/weak in human+mouse. The plasma-cell master regulator is XBP1 (SC1.3),
     not the bulk IKZF1×IRF4 pair — so this headline bulk cocktail is substantially a
     lymphocyte-composition signal, confirmed most strongly in human.
  4. Several M14 pairs (NKX2-3×IRF4, IKZF1×FOXA1, …) are **not expressed** in plasma
     cells at all — bulk associations that don't exist within the driver cell type.
- **Interpretation.** The reconciliation is **per-cocktail and per-species**, not a
  blanket verdict: the same bulk cocktail can be genuine regulation in one atlas and a
  composition artifact in another. Bulk SHAP magnitude does **not** predict single-cell
  validation (the strongest bulk pair for each module is NOT the most cross-species-robust;
  the all-3-species winner MLXIPL×NR1H4 was mid-ranked in bulk).
- **Artifacts:** `sc_bulk_sc_reconciliation.png`, `sc14_cocktail_reconciliation.csv`
  (all 24 pairs, per-species verdict + ranks + shared-target counts),
  `sc14_cocktail_reconciliation_scored.csv` (16 testable, n_genuine per pair).

**Original spec (retained; edge-level reconciliation + more cell types = SC-Tier 4 scale-up):**
- **Methods:** intersect bulk high-confidence edges (≥2-method support) and the
  SHAP cocktail pairs (`phaseB_cocktail_pairs.csv`) with the pySCENIC regulons.
  Classify each bulk edge: (i) confirmed within a cell type, (ii) present but
  redistributed to a different cell type than the tissue implied, (iii) not
  recovered in any cell type (candidate composition artifact). Re-examine the
  headline bulk cocktails (liver HNF1A+HNF4A+HNF1B; immune IKZF1×SPI1; the HOXA
  patterning cocktail) for within-cell-type support across all three species; the
  testis FOXM1×E2F2 cocktail is reconciled **human + lemur only** (testis absent in
  the mouse atlas).
- **Figure:** `sc_bulk_reconciliation.png` — confusion-style panel of bulk edges by
  reconciliation class + a per-cocktail confirmation strip.
- **Output:** `sc_edge_reconciliation.csv` (every benchmarked bulk edge/cocktail
  with its single-cell verdict + driver cell type). Compute: local.

---

## SC-TIER 2 — Cross-species cell-type regulon conservation *(the headline extension)*

### SC2.1 — Does regulon logic conserve at cell-type resolution? ✅ **DONE**
The bulk thesis was "membership conserved, wiring drifts." Test it where wiring
actually lives.

- **Results (executed).** Inferred regulons for **10 shared cell types × 3 species**
  (hepatocyte, plasma cell, B/NK/T cell, macrophage, monocyte, endothelial, fibroblast,
  pneumocyte; ≥100 cells/species, best-powered tissue each) on a fixed 400-variable-gene
  common target panel. Separated two axes: **regulator-identity conservation** (Spearman
  rank corr of TF total-importance across species, over TFs present in all 3) vs
  **target-set conservation** (mean target-list Jaccard for shared top regulators).
  **The bulk thesis holds at cell-type resolution: mean regulator-identity conservation
  = 0.42 > mean target-set conservation = 0.17, and all 9 cell types with a computable
  target-set score sit below the y=x line** (identity more conserved than wiring; B cell
  has no top-regulator shared across all 3 species so no target Jaccard, 9/10 plotted).
  Most-conserved regulator identity: NK/macrophage/T cell (0.46–0.48); least:
  pneumocyte/hepatocyte (0.31–0.34). Lowest target-set conservation: NK cell (0.09),
  plasma cell (0.11).
  Sanity check: XBP1 is top-5 plasma-cell regulator in all 3 species over the generic
  panel (rank 1 mouse/lemur), consistent with SC1.3's module-specific rank-1.
- **Artifacts:** `sc_regulon_conservation.png`, `sc_regulon_conservation.csv`.

**Original spec:**
- **Methods:** for each shared cell type, compute regulon overlap across the species
  in which that cell type is present (3-way for the 9 shared-panel tissues; **2-way
  human+lemur** for germ-cell types from testis/ovary, absent in the mouse atlas)
  (Jaccard of motif-supported targets per TF; regulon-activity correlation across the
  shared cell types). Separate **regulator identity
  conservation** (is the same TF the top regulator of that cell type in all three
  species?) from **target-set conservation** (does its target list conserve?).
- **Prediction under the bulk finding:** regulator identity conserves broadly
  (membership), target wiring is the labile axis (connectivity) — now testable at
  the resolution that bulk could not reach.
- **Figure:** `sc_regulon_conservation.png` — per-cell-type regulator-conservation
  vs target-conservation, three species, with the conserved-vs-labile cell types
  called out.
- **Output:** `sc_regulon_conservation.csv`. Compute: local.

### SC2.2 — Tie cell-type regulon variability to the phylo-signal modules *(fuses with Phase A)* ✅ **DONE (headline)**
Close the loop with the project thesis: are the modules that carried **phylogenetic
signal** in bulk (M3 pituitary, M14 spleen, …) the ones whose **cell-type regulons
vary across species**?

- **Results (executed).** Fused Phase A (K, Zsummary) × SC1.2 driver cell type × SC2.1
  cross-species conservation. Restricted to the **6 modules with a reliable single-cell
  driver** (evaluable in our panel: M14 plasma cell, M11 endothelial, M10 T cell, M15
  monocyte, M13/M21 hepatocyte) — the other 21 either have unavailable home tissues or
  drivers assigned on tissues outside the panel (not trustworthy, excluded).
- **Pattern (n=6, exploratory — mixed, not a clean split).** **M14 (K=0.40, K_p=0.004)**
  drives the plasma cell, one of the **lowest-target-conservation cell types (0.11; only
  NK cell at 0.09 is lower)** — labile wiring — even though its regulator *identity*
  (XBP1) is conserved. This is the clearest single case. But the pattern does **not**
  generalize cleanly across the 6: **M11 (K=0.29, K_p=0.04)** is endothelial-driven with
  target conservation 0.19 — *higher* than the non-phylo-signal hepatocyte modules
  (M13/M21, 0.13) and T-cell module (M10, 0.17). So among these 6, low target
  conservation is NOT a property shared by both significant phylo-signal modules; only
  M14 shows it strongly. The regulator-identity axis is likewise mid-range for the
  phylo-signal drivers (plasma cell 0.36, endothelial 0.45) and not systematically
  lower than the others. **Honest read:** the M14/plasma-cell case is a compelling
  example of "conserved regulator identity, divergent targets" coinciding with high
  phylo-signal, but with n=6 and M11 breaking the pattern, this is a suggestive single
  case, not a module-population trend.
- **Caveat (stated on the figure and here):** n=6 reliably-mapped modules is a
  small, exploratory synthesis, not a population test; the strongest phylo-signal
  modules (M3 pituitary, M20 testis) could not be mapped for lack of cross-species
  single-cell data (SC1.2b). The direction is suggestive and consistent across all
  independent lines here, but a powered test needs deeper multi-species atlases.
- **Artifacts:** `sc_synthesis.png` (**headline**), `sc_thesis_synthesis.csv`.
- **Methods:** map each phylo-signal module to its driver cell type (SC1.2) and that
  cell type's cross-species regulon conservation (SC2.1). A coherent story: labile,
  phylo-signal modules → composition-variable or regulon-divergent cell types;
  deep-conserved modules (M9 brain neuronal, M8 testis) → cell types with conserved
  regulators *and* targets.
- **Figure:** `sc_synthesis.png` — the headline figure: module preservation (Zsum) ×
  Phase A K × driver cell type × cross-species regulon conservation, one integrated
  view extending the bulk `phaseB_regulon_conservation.png`.
- **Output:** `sc_thesis_synthesis.csv`. Compute: local. **Headline deliverable.**

### SC2.3 — Deep-outgroup conservation floor: zebrafish positive control *(Track C)* ✅ **DONE**

- **Result — the conserved core reaches teleost, and it "goes the distance."** Extracted
  3 probe lineages (neuron 192k, muscle 166k, immune 8k cells) from the Developmental
  Zebrafish Reference Atlas, restricted to **8,486 strict 1:1 human↔zebrafish orthologs**
  (BioMart `ortholog_one2one`, filtering out the teleost-WGD one2many/many2many), inferred
  lineage regulons, and asked whether **canonical mammalian master regulators recur in the
  zebrafish top-20**. They do, at strong ranks: **muscle MEF2D rank 1, SOX6 rank 2, TCF7L2
  rank 4, MEF2A rank 5; immune SPI1(PU.1) rank 4, FLI1 rank 6, KLF3 rank 7, IKZF1 rank 9;
  neuron EBF3 rank 4, PBX3 rank 5, NPAS3 rank 6, MEIS1 rank 7.** Permutation null (10,000
  random TF sets): all three lineages enriched above chance — **muscle p=0.003, neuron
  p=0.002, immune p=0.016** (4/4, 5/5, 5/7 of present canonical masters in top-20 vs
  ~1–2 expected). RUNX3 (28) and CEBPB (31) fall just outside — the floor is not total.
- **Evolutionary reach.** The zebrafish split (~450 My) **brackets** the clades of
  interest — Marsupialia (~160 My) and Afrotheria (~100 My) — so a regulator whose
  identity is conserved to teleost necessarily spans those intermediate nodes. These
  master regulators (MEF2, SPI1/PU.1, IKZF1, EBF3, PBX/MEIS) are therefore predicted to
  hold across marsupials and afrotherians even though CELLxGENE has no single-cell atlas
  for either clade to test directly (the survey found only vertebrates, ~95% human+mouse).
- **Interpretation, honestly scoped.** This is a **one-directional positive control**:
  it confirms regulator-*identity* conservation reaches teleost for deep lineage masters.
  It does NOT test target-wiring conservation (SC2.1 already showed wiring is the labile
  axis even among mammals — it would only be more diverged at 450 My), and negatives are
  uninterpretable (larval-only zebrafish, coarse cross-clade cell-type alignment,
  1:1-ortholog bias toward dosage-sensitive genes). Positive hits carry the information.
- **Artifacts:** `sc_deep_outgroup.png`, `sc_deep_outgroup_floor.csv` (masters surviving
  to zebrafish + ranks), `sc23_canonical_ranks.csv`, `sc23_permutation_test.csv`.

**Original spec / rationale (retained):**
The mammal-vs-mammal work above (Tabula human/mouse/lemur, ~90 My) gives the
quantitative conservation *gradient*. Track C asks a different, binary question:
**does the conserved regulatory core reach all the way out to a teleost fish
(~450 My)?** A regulon that survives to zebrafish is about as strong a claim of
ancient, hard-constrained regulation as this data can support. This is deliberately
scoped as a **narrow, one-directional positive control — not a fourth point on the
Track A gradient** — because three confounds make a symmetric whole-body comparison
uninterpretable:

1. **Life stage (decisive).** The only CELLxGENE zebrafish single-cell atlas is the
   *Developmental Zebrafish Reference Atlas* — one collection, `sci-RNA-seq3`, 2.4M
   cells spanning **segmentation → pharyngula → hatching → larval** stages, with
   **zero adult cells** (verified against the CELLxGENE curation API). An adult
   mammalian cell type and a larval zebrafish cell state differ in *stage*, not only
   species. A negative result would therefore confound evolutionary divergence with
   developmental-stage mismatch and is not interpretable; only *positive* hits (a
   regulon conserved despite both) carry information.
2. **Teleost whole-genome duplication.** Zebrafish underwent a WGD, so human↔zebrafish
   orthology is heavily many-to-many — the paralog-aggregation problem the bulk plan
   flagged at Step 2. Restrict to the **high-confidence 1:1 ortholog set** to human
   (a few thousand genes, biased toward dosage-sensitive conserved genes) and report
   the ortholog-coverage fraction so that bias is explicit; it tilts the test *toward*
   finding conservation, which is acceptable for a positive control but must be stated.
3. **Cross-clade cell-type alignment.** Across 450 My only **coarse** cell types map
   reliably through Cell Ontology (neuron, myocyte, broad immune/blood); fine subtypes
   do not. The comparison is well-posed only at coarse granularity.

**Design (what to actually run):**
- **Restrict to the deepest-conserved, coarsely-defined cell types** that both exist
  in a larva and carry a universally-conserved bulk module: **neuronal** (brain M9),
  **muscle** (M18), and broad **blood/immune**. Explicitly exclude adult-homeostatic
  types (hepatocyte, adipocyte, pancreatic islet) that have no larval counterpart.
- **Test regulator *identity*, not full target wiring.** Ask "is the master TF of
  this cell type the same ortholog in zebrafish?" — e.g. myogenic bHLH (MyoD family)
  in muscle, SoxB/neurogenic factors in neurons — rather than target-set Jaccard,
  which is too noisy across 450 My + WGD + stage mismatch to interpret.
- **1:1 orthologs only**; carry the coverage fraction into every statement.
- **Interpret asymmetrically:** regulator conserved to zebrafish = evidence of a deep
  conserved core; regulator *not* recovered = **not interpretable** (confounded),
  never reported as evidence of divergence.
- **Figure:** `sc_deep_outgroup.png` — for the 3 probe cell types, master-regulator
  ortholog identity across human/mouse/lemur/zebrafish, with the 1:1-coverage
  fraction and the "positive-only" interpretation band annotated.
- **Output:** `sc_deep_outgroup_floor.csv` (per probe cell type: master TF, zebrafish
  1:1 ortholog present Y/N, recovered as top regulator Y/N, coverage fraction).
  Compute: local (few thousand orthologs, 3 cell types).
- *A genuinely symmetric deep comparison would require a stage-matched **developmental
  mammalian** atlas (e.g. mouse organogenesis) to pair against the larval zebrafish —
  a larger, separate scope, noted in SC-Tier 4.*

---

## SC-TIER 3 — Validation *(plan Step 10, at cell-type resolution)* ✅ **DONE**

- **Results (executed).** Three validation lines on the 10 human cell-type regulons:
  1. **Gold-standard recovery vs DoRothEA A/B.** Cell-type regulons score **AUROC ~0.57**
     (0.51–0.59), *below* the bulk tissue-average (0.674) — expected and informative:
     DoRothEA is a **tissue-agnostic** gold standard (curation/ChIP, largely bulk-derived),
     so it rewards the breadth of the aggregated bulk network over cell-type specificity.
     All cell types are above random (0.50); fibroblast/B/plasma highest. The cell-type
     layer buys **resolution, not gold-standard breadth** — the right tool for the
     composition-vs-coregulation question (SC1.2/SC1.4), not for maximizing DoRothEA AUROC.
  2. **Motif support: mean 83%** (0.70–0.95) of each cell type's top-20 regulators carry
     a JASPAR motif (from the Phase B annotation) — the regulons are dominated by genuine
     sequence-specific TFs, not co-expression artifacts. (Full 26-genome FIMO / pySCENIC
     cisTarget remains SC-Tier 4; cisTarget DBs are human/mouse only, no lemur.)
  3. **Cross-species held-out: mean Spearman 0.53** (train human+mouse consensus TF-importance
     ranking, predict lemur). Critically, **held-out accuracy tracks SC2.1 regulator-identity
     conservation at ρ=0.79** — the most-conserved cell types (T cell 0.62, monocyte 0.60,
     NK 0.59) predict lemur best; the least-conserved (plasma/B cell 0.40) worst. This is an
     **independent confirmation of the SC2.1 conservation gradient** from a held-out predictive
     test rather than a descriptive overlap.
- **Artifacts:** `sc_validation.png` (3-panel: DoRothEA cell-type-vs-bulk, motif support,
  held-out-vs-conservation), `sc_validation_benchmark.csv`, `sc3_motif_support.csv`,
  `sc3_heldout.csv`.

**Original spec (retained):**
- **Motif support (partial delivery of the deferred FIMO layer):** pySCENIC's
  cisTarget step already provides motif enrichment per regulon — report the fraction
  of each regulon that is motif-supported; this partially satisfies plan Steps 5–6
  without the full 26-genome FIMO scan.
- **DoRothEA / gold-standard benchmark, now cell-type-aware:** extend the existing
  Tier-3 DoRothEA harness (`12_grn_validation_dorothea.py`) to score pySCENIC
  regulons against DoRothEA A/B, and compare AUROC/AUPRC of *cell-type* regulons vs
  the *tissue-average* bulk regulons — quantifying how much resolution the
  single-cell layer buys.
- **Cross-species held-out:** train regulons on human+mouse, predict lemur cell-type
  regulon activity; Spearman per cell type (the cell-type analog of the deferred
  leave-one-species-out check).
- **Figure:** `sc_validation.png` — ROC/PR (cell-type vs bulk) + motif-support bars +
  held-out accuracy.
- **Output:** `sc_validation_benchmark.csv`. Compute: local.

---

## SC-TIER 4 — Deferred *(needs remote compute or large downloads)*

Mirrors the repo's existing `analysis_plan_future_directions.md` split.
- **Full-scale pySCENIC** across all cells and all species (no subsampling), with
  100-run GRNBoost2 stability — GPU/large-RAM job.
- **More species / clades** via other single-cell atlases (primate/marsupial atlases
  as they appear) to widen the phylogenetic span toward the bulk 26-species panel.
  (Zebrafish is already used as the SC2.3 deep-outgroup control — Track C.)
- **Stage-matched deep comparison** — pair the larval zebrafish atlas against a
  *developmental* mammalian atlas (e.g. mouse organogenesis / MOCA) so the fish–mammal
  comparison is symmetric in life stage, converting the SC2.3 positive-control into a
  full bidirectional deep-conservation test.
- **Spatial layer** — 660 CELLxGENE spatial datasets could add tissue-architecture
  context to cell-type regulons.
- **Raw-read reprocessing** of the access-controlled Tabula Sapiens FASTQs (dbGaP-
  style application) if allele- or isoform-level regulation is needed; not required
  for the count-matrix analyses above.

---

## Dependency & sequencing
```
[DONE bulk] Phase A + B ──► SC1.1 acquire/harmonize
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
   SC1.2 deconv        SC1.3 pySCENIC regulons   (reuse bulk GRN/cocktails)
        │                     │                      │
        └───────► SC1.4 bulk↔SC reconciliation ◄─────┘   [immediate payoff]
                              │
                    SC2.1 cross-species regulon conservation
                              │
                    SC2.2 fuse with Phase A  ──► sc_synthesis.png  [HEADLINE]
                              │
                    SC-Tier 3 validation (DoRothEA + motif + held-out)
```

## Compute & environment
- `list_compute` is **empty** — all SC-Tier 1–3 steps are designed to run **local**
  on arm64 macOS via **subsampling / metacells**; SC-Tier 4 is the compute-heavy
  deferral. This matches the repo's existing active-vs-future split.
- **New env** (`sc` conda): `scanpy`, `anndata`, `pyscenic`/`ctxcore`, `pySCENIC`
  motif+track databases (human, mouse), `AUCell` scoring, `scikit-learn`. Reuses the
  `coexpr` ortholog tables and the `phylo` env for any phylo overlay.
- **Data footprint:** Tabula matrices are a few GB each as `.h5ad`; the sandbox
  ~13 GB scratch handles them one species at a time (stream + subsample; checkpoint
  the harmonized objects).

## Consolidated deliverables
- **Figures:** `sc_atlas_overview`, `sc_module_celltype_deconv`, `sc_regulon_activity`,
  `sc_bulk_reconciliation`, `sc_regulon_conservation`, `sc_synthesis` (headline),
  `sc_validation`.
- **Tables:** `sc_celltype_panel`, `sc_module_celltype_assignment`,
  `sc_regulons_<species>`, `sc_edge_reconciliation`, `sc_regulon_conservation`,
  `sc_thesis_synthesis`, `sc_validation_benchmark`.
- **Report:** `sc_regulon_synthesis_report.md` — how single-cell refined the bulk
  networks (edges confirmed vs composition artifacts; cocktails validated at
  cell-type resolution; conservation of regulatory logic across the primate/rodent
  split).

## Honest scope & limitations
- **Three species, not 26.** The clean cross-species cell-type comparison is
  human/mouse/lemur (Tabula). This is a rodent + two-primate span (~90 My), narrower
  than the bulk 429-My vertebrate panel — it tests the thesis where the data are
  clean, and SC-Tier 4 widens it.
- **Motifs are human/mouse-anchored.** cisTarget databases exist for human and mouse;
  lemur regulons use human motifs as proxy (reasonable within primates, a documented
  assumption).
- **Subsampling.** Local compute forces per-cell-type subsampling for pySCENIC; rare
  cell types with few cells will have lower-confidence regulons (flagged, and the
  full run is SC-Tier 4).
- **Cell-type label harmonization** across species is imperfect at fine granularity;
  the common panel is deliberately held at ~20–30 broad types where cross-species
  `CL:` mapping is reliable.
