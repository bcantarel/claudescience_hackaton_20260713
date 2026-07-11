# Conserved Gene Co-expression Networks Across Vertebrates

Discovering tissue-defining gene co-expression modules in human, then testing
which of them are preserved across the vertebrate tree — and building the
transcription-factor regulatory layer on top of the conserved modules.

---

## 1. The questions

The project began from a broad question and was progressively focused with the researcher:

1. **(Original)** Can we identify shared gene co-expression networks across the
   domains of life?
2. **(Refined → mammals & vertebrates)** Within animals, which co-expression
   **modules** — groups of genes that vary together across tissues — are
   **conserved** across mammals and out to birds, reptiles, amphibians, fish?
3. **(Refined → cell-type / TF structure)** A species has one genome but many
   cell types, driven by differential expression and transcription factors.
   Organism-averaged networks collapse that structure. So: discover modules
   from a **tissue-resolved** reference (human GTEx), then ask
   **(a)** do those modules hold up across species, and **(b)** does their
   conservation follow the phylogeny or is it uniform?
4. **(TF layer)** Which transcription factors regulate each conserved module,
   and where does regulation vary by clade?

## 2. Approach (two-stage + two analysis phases)

The design treats **one well-powered reference** (human GTEx, 30 tissues) as
the place to *discover* modules, then uses **many species** (Bgee + FarmGTEx,
raw SRA where needed) only to *test preservation* of those modules. This avoids
the ortholog-intersection collapse that kills naive all-vs-all cross-species
co-expression.

```
Stage 1  Discover modules            human GTEx (recount3) -> WGCNA -> 27 modules
Stage 1b Cross-check                 independent mouse WGCNA (ENCODE) -> 23/26 recovered
Stage 2  Test preservation           26 vertebrates (Bgee/FarmGTEx) -> WGCNA Zsummary
-----------------------------------------------------------------------------------
Phase A  Phylogenetic formalization  Blomberg's K / Pagel's lambda on preservation
Phase B  TF regulatory layer         TF annotation -> ensemble GRN -> (cocktails, motifs)
```

### Method notes
- **WGCNA in Python.** The canonical R `WGCNA` package has no `osx-arm64`
  conda build, so the pipeline is a faithful pure-Python reimplementation
  (signed-hybrid adjacency at soft-power β=8 → signed TOM → average-linkage
  hclust → `dynamicTreeCut` → eigengene merge at r>0.75). Validated against an
  independently-built mouse network (23/26 modules recovered, Bonferroni-sig).
- **Preservation = WGCNA `Zsummary`** (Langfelder et al. 2011): density +
  connectivity Z-scores vs a permutation null. Zsum>10 strong, 2–10 moderate, <2 none.
- **Cross-species mapping** uses high-confidence **1:1 orthologs** (Ensembl
  BioMart). Four species with Ensembl assembly-version mismatches
  (chicken/dog/cat/sheep) were recovered via a **gene-symbol bridge** through
  Bgee's expression-call files.
- **GRN inference (Phase B)** is a **3-method rank-product ensemble**:
  GENIE3 (ExtraTrees), GRNBoost2 (LightGBM), and CLR (mutual-information).
  *Deviation from plan:* the plan named ARACNE or PIDC as the third method;
  **CLR was substituted** for tractability — see `scripts/07_grn_clr.py`.

## 3. Key results

**Stage 1 — 27 modules from human GTEx**, cleanly tissue-organized and
marker-validated (pancreas 6/6, liver 5/6, muscle 5/6, immune 5/6). WGCNA
resolves *sub-tissue cellular programs* — e.g. brain splits into a
neuronal-synaptic module (M9, SNAP25) and a glial/myelination module (M19,
GFAP/MBP/PLP1) — which is exactly the cell-type structure the researcher wanted.

**Stage 2 — preservation across 26 vertebrates (6.4–429 My).** Core programs
are broadly preserved; conservation is **module-driven, not divergence-driven**:
- Universally conserved: brain M9 (mean Zsum 24.9), testis M8 (22.6),
  ovary M2 (21.5), muscle M18, spleen M10.
- Labile: pancreas M23 (−0.85), adipose M25, lung M27.
- Preservation vs divergence time: Spearman ρ = **−0.24, n.s.**

**Phase A — conservation does NOT track the phylogeny.** Every module has
Blomberg's **K ≪ 1** (mean 0.18; K=1 = Brownian expectation); the most-conserved
modules have the *lowest* signal. Core programs are conserved *everywhere at
once* (deep stabilizing selection), not graded by relatedness. The exceptions
carrying phylogenetic signal are the labile modules — **M3 pituitary (K=0.47,
p=0.002)**, M14 spleen, M20 testis, M11 adipose, M5 ovary — where regulation
genuinely varies by clade.

**Phase B — TF regulatory layer.**
- **793 TFs** in the network (403 module-assigned), annotated with DBD family,
  JASPAR motif ID, expression breadth, and tissue-activity flags.
- **M24 is a HOX patterning module** — 32/33 TFs are homeodomain (the entire
  HOXA/B/C/D complement + TBX15), recovered purely from co-expression; also the
  tightest human↔mouse module correspondence (Jaccard 0.75).
- **Ensemble GRN** (396,286 edges; 165,531 with ≥2-method support) passes its
  sanity gate cleanly: HNF4A #1 in liver, IKZF1 #1 in immune, SOX2 #2 in brain,
  CEBPA #1 — canonical master regulators rank top of their modules, and
  requiring multi-method agreement *sharpens* the signal.

## 4. Data sources
- **recount3** (`recount-opendata.s3.amazonaws.com`) — human GTEx (30 tissues,
  ~3,300 samples subsampled), mouse ENCODE (SRP013027).
- **Bgee v15.2** (`www.bgee.org/ftp`) — per-species RNA-seq TPM, 25+ vertebrates.
- **FarmGTEx** (CattleGTEx) — livestock tissue atlas (kept separate; ag-skewed).
- **Ensembl BioMart** — 1:1 orthologs, GO TF annotation, InterPro DBD families.
- **JASPAR 2024** — TF binding motifs.

## 5. Scope & limitations (honest state)
- **Focused pilot.** Phase B runs on human-reference expression only. The
  genome-download-heavy steps — cross-species **orthogroup construction**
  (fastOMA), **promoter motif scanning** (FIMO across 26 genomes) — are
  **deferred**: no remote compute is configured and the sandbox has ~13 GB scratch.
  The TF annotation table therefore keys on human Ensembl gene IDs, not
  cross-species orthogroup IDs (the one outstanding plan Step-3 field).
- **Clade gaps.** Afrotheria (elephant, tenrec) and Xenarthra (armadillo) have
  no replicated multi-tissue RNA-seq in public repositories — a genuine
  data-availability gap, documented in `results/sra_clade_availability.csv`.
  Elephant feasibility was NEGATIVE (7 solid tissues, ~n=1 each — below the
  co-expression replication floor). Marsupials (koala, Tasmanian devil) ARE
  feasible from SRA but require raw-read quantification (deferred on disk).
- **Gene-set filter.** The top-14,000-by-variance cutoff excludes narrowly
  expressed TFs (MYOD1, PAX5, SRY…), so the GRN under-represents highly
  cell-type-restricted regulators.

## 6. Repository layout
```
README.md                         this file
reports/
  analysis_plan_integrated.md     full integrated plan (Phases A + B + uploaded TF plan)
  coexpr_feasibility_report.md    early STRING-based feasibility pilot
  phaseA_phylo_signal_report.md   Phase A results & interpretation
figures/                          publication-grade figures (one per stage/phase)
results/                          all result tables (CSV) + GRN ensemble (parquet)
scripts/                          analysis code, numbered by pipeline stage
  01_normalize_matrix.py          expression normalization recipe
  02_wgcna_modules.py             WGCNA module discovery (Python)
  04_bgee_preservation_sweep.py   cross-species Zsummary sweep
  05_phaseA_phylo_signal.R        Blomberg K / Pagel lambda
  06_grn_genie3.py / _grnboost2.py  GRN tree-ensemble methods
  07_grn_clr.py                   GRN information-theoretic method
  lib_dynamicTreeCut_patched.py   numpy-2.x-patched cutreeHybrid
data/species_tree.nwk             TimeTree-calibrated 26-species ultrametric tree
```

## 7. Environment
- Python 3.13 (`coexpr` conda env): numpy, pandas, scipy, scikit-learn,
  dynamicTreeCut, lightgbm, pyarrow, requests.
- R 4.5 (`phylo` env): ape, phytools, nlme.
- No GPU required; all steps CPU-bound and run locally on Apple Silicon.

*Analysis run in Claude Science. Co-expression conservation is the foundation
layer for the cross-species TF-regulon plan; Phases A and B build directly on it.*
