# Active Analysis Plan — Conserved Co-expression → TF Regulatory Logic

**Project:** Conserved gene regulatory architecture across vertebrates
**Substrate:** Human GTEx reference modules → preservation across 26 vertebrates (Bgee + recount3 + FarmGTEx)
**Scope of this plan:** the work that is finishable *now* on data in hand (no remote
compute, no large genome downloads). The genome-scale layer is split out into
`analysis_plan_future_directions.md`.

---

## 0. Foundation already built

| Plan step satisfied | Completed work | Key artifacts |
|---|---|---|
| Step 1 (normalization) | recount3 GTEx: 30 tissues, 3,267 samples; CPM→log2, variance-filtered to 14,000 genes. | `stage1_gene_modules.csv` |
| Module discovery (WGCNA variant of Step 9) | Human WGCNA: **27 modules**, 7,034 assigned genes, tissue-mapped + marker-validated. *NB: plan Step 9 proper is matrix-factorization discovery (NMF/LDA); WGCNA is the co-expression alternative used here. NMF/LDA deferred → future plan F6.* | `stage1_module_tissue.png`, `stage1_module_summary.csv` |
| Independent validation | Mouse cross-check (ENCODE): 23/26 modules recovered by an independent mouse network. | `stage2_mouse_crosscheck.png` |
| Step 8 (conservation) | Preservation sweep across **26 vertebrates**, 6–429 My, 12 clades (Zsummary per module). | `stage2_crossspecies_preservation.png`, `stage2_module_conservation.csv` |
| **Phase A** (Step 8, phylo) | **Blomberg's K / Pagel's λ** per module. Conservation is deep & uniform (K≪1), not clade-graded; labile modules (M3 pituitary, M14 spleen) carry the phylo signal. | `phaseA_phylo_signal.png`, `phaseA_phylo_signal.csv` |
| **Phase B1** (Step 3) | TF annotation: **793 TFs**, DBD families, JASPAR motifs, expression breadth, tissue-activity flags. M24 = HOX patterning module. | `phaseB_TF_annotation_table.csv` |
| **Phase B2** (Step 4) | **3-method ensemble GRN** (GENIE3 + GRNBoost2 + CLR, rank-product): 396,286 edges, sanity gate passed (HNF4A #1 liver, IKZF1 #1 immune). | `phaseB_GRN_ensemble.parquet`, `phaseB_GRN.png` |

**Established results that constrain what's next**
- Conservation is **module-identity-driven, not distance-driven** (ρ=−0.24, n.s.; K≪1 for all modules).
- **Zdensity high, Zconnectivity ≈ 0**: module *membership* is conserved but intramodular *hub wiring* diverges — the key handle for the regulatory layer.
- The modules carrying phylogenetic signal (M3 pituitary K=0.47, M14 spleen, M20 testis, M5 ovary, M11 adipose) are the labile ones — the natural place to look for clade-structured regulation.

---

## TIER 1 — Regulatory logic on data in hand *(active)*

### T1.1 — TF cocktails *(plan Step 7)* — RUNNING
Which **minimal combination** of TFs jointly specifies each module's activity program?
- Per-module **XGBoost** regression of module eigengene on the 793-TF expression matrix → single-TF importance (gain).
- **SHAP interaction values** among each module's top-15 TFs → synergistic TF *pairs* (combinatorial signal beyond additive).
- Output: ranked single-TF drivers + top interacting pairs per module (`cocktail_singles.csv`, `cocktail_pairs.csv`, figure).
- *Deferred to future plan:* PARAFAC tensor decomposition across the species×tissue tensor (needs the orthogroup matrix); motif co-occurrence test (needs FIMO).

### T1.2 — Module functional annotation *(GO/KEGG enrichment line-item of Step 9; NOT the full step)*
GO / KEGG / Reactome enrichment per module → biological-process labels beyond top tissue.
*Plan Step 9's defining method — matrix-factorization module discovery (consensus
NMF/LDA) — is deferred to future plan F6; this delivers only the enrichment-annotation
line-item, applied to the existing WGCNA modules.*
- Enrichment via g:Profiler or Enrichr API on each module's gene set (background = 14,000-gene network).
- Output: `module_functional_annotation.csv` (top terms + FDR per module), integrated into the module summary.
- Compute: light, local.

### T1.3 — Regulon conservation synthesis *(the project's thesis — fuses Phase A + B)*
Does the conserved co-expression structure have a conserved **regulatory logic**, and where does it vary by clade?
- For each module, take its top regulators (GRN out-degree, T1.1 cocktails) and ask whether *those TFs'* own cross-species expression preservation tracks the module's preservation.
- Test the mechanistic prediction from "membership conserved, wiring drifts": labile modules (low K, e.g. M3 pituitary, M14 spleen) should be driven by TFs with clade-variable expression; universally-conserved modules (M9 brain, M8 testis) by broadly-conserved TFs.
- Cross-reference regulator identity with the phylo-signal table: are the phylo-signal-bearing modules the ones with clade-variable regulators?
- Output: `regulon_conservation.csv` + a synthesis figure tying module preservation, phylo signal, TF-density, and regulator conservation into one view. **This is the headline deliverable.**
- Compute: light, local (reuses GRN + preservation + phylo-signal tables).

---

## TIER 3 — Validation *(active, partial)*  *(plan Step 10)*

Benchmark the ensemble GRN against gold-standard regulatory networks.
- **DoRothEA** (downloadable human regulon reference, confidence-tiered A–E) — AUROC/AUPRC of our TF→target edges vs DoRothEA A/B regulons.
- Motif-enrichment sanity: do inferred regulons for a TF over-represent that TF's JASPAR motif in target promoters? *(partial — full FIMO promoter scan is Tier 2; a proximal-promoter proxy is doable now.)*
- **Leave-one-tissue-out** held-out prediction as a within-data robustness check (full leave-one-species-out needs the cross-species orthogroup matrix — Tier 2).
- Output: `grn_validation_benchmark.csv` + ROC/PR figure.
- ENCODE / ChIP-Atlas TF-ChIP benchmarking is **partially** here (DoRothEA incorporates ChIP evidence); full ChIP-Atlas overlap deferred with Tier 2.

---

## Dependency & sequencing (Tier 1 + 3)
```
[DONE] Phase A + B1 + B2 ─┬─► T1.1 cocktails (Step 7)      ── running
                          ├─► T1.2 functional annotation   ── light, independent
                          └─► T1.3 regulon conservation ◄── needs T1.1 + Phase A + B2  [HEADLINE]
                                        │
                          T3 validation (DoRothEA) ◄────────┘  independent of T1.1
```

## Compute
All Tier 1 + 3 steps are **light and local** (arm64 macOS, no GPU). `list_compute` empty.
The heavy genome-scale work is deliberately excluded → see future-directions plan.
