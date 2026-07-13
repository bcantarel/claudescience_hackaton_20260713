# Master module → TF-regulator → target tables

Two views of the same regulatory network. Built from the 3-method ensemble GRN
(GENIE3 + GRNBoost2 + CLR consensus), the 27 WGCNA modules, TF annotation, and
the 26-species cross-organism preservation results.

## Files
- **`master_module_summary.csv`** — one row per module (27 rows). Read this first.
- **`master_module_TF_target.csv`** — one row per (module, TF regulator, target gene)
  edge (165,531 rows). The full detail behind the summary.

## Core vs transient (edge_class)
Defined by **GRN method consensus** — how many of the three independent inference
methods recovered the edge:
- **core** = recovered by ALL THREE methods (GENIE3 ∧ GRNBoost2 ∧ CLR). The stable
  regulatory backbone; 71,243 edges. These are the edges the DoRothEA benchmark
  and the regulon-conservation analysis lean on.
- **transient** = recovered by exactly TWO methods. Weaker/context-sensitive support;
  94,288 edges. Single-method edges are excluded entirely (not part of the consensus
  network).

## Tissue / organism resolution — important scope note
- **Tissue** is the module's dominant GTEx tissue (`top_tissue`), assigned once from
  the human reference. Each module = one tissue-defining co-expression program.
- **Organism** resolution is at the **module level, not the per-edge level.** The GRN
  itself is inferred from human GTEx only (per-species GRNs are deferred future work —
  they need the cross-species orthogroup expression matrix, plan step F2). What IS
  resolved per organism is whether each module's *program* is preserved across the
  26-species panel:
  - `module_frac_species_preserved` — fraction of 26 species where the module
    preserves (Zsummary > 2)
  - `module_n_species_preserved` — count of species (of 26)
  - `blomberg_K` / `phylo_signal` — does preservation carry phylogenetic signal
  So "by tissue/organism" means: TF→target edges are human, tagged core/transient;
  the module they belong to carries a measured cross-organism conservation profile.
  Per-species edge rewiring is the explicit next step (F2), not claimed here.

## master_module_summary.csv columns
module, tissue, n_TF_regulators, n_target_genes, n_core_edges, n_transient_edges,
top_regulators (top 5 by core-target count), module_mean_Zsum, frac_species_preserved,
n_species_preserved, blomberg_K, phylo_signal, top_function (top enriched GO/KEGG term).

## master_module_TF_target.csv columns
module, tissue, TF_regulator, TF_family, target_symbol, edge_class (core/transient),
n_methods, ensemble_rank, rank_product, genie3/grnboost2/clr (per-method weights),
module_mean_Zsum, module_frac_species_preserved, module_n_species_preserved.
