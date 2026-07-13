# Single-cell refinement of cross-species TF regulatory networks
### Resolving composition from co-regulation, and testing the conservation floor to teleost

**Project:** geneNetworking · **Substrate:** Tabula Sapiens (human) / Tabula Muris Senis (mouse) / Tabula Microcebus (lemur) single-cell atlases + Developmental Zebrafish Reference Atlas (Track C outgroup) · **Gene space:** 14,073 three-way 1:1 orthologs

---

## 1. The question and why single-cell

The bulk cross-species program (Phase A/B, 26 vertebrates, GTEx-anchored WGCNA) landed on a specific thesis: **module membership is conserved, but hub wiring diverges** (high Zsummary preservation, near-zero connectivity preservation). It also produced TF "cocktails" — SHAP-ranked interacting TF pairs per module — and flagged a limitation it could not resolve: a bulk tissue mixes cell types, so a co-expression edge can reflect **genuine co-regulation within a cell** or merely **covarying cell-type composition** across samples. Single-cell data is the instrument that separates the two, at the resolution where regulatory wiring actually lives.

This report covers the complete single-cell arm: acquisition and harmonization (SC1.1), the composition-vs-coregulation diagnostic (SC1.2), per-cell-type regulon inference (SC1.3), bulk↔single-cell cocktail reconciliation (SC1.4), cross-species regulon conservation (SC2.1), the synthesis with Phase A phylogenetic signal (SC2.2), the zebrafish deep-outgroup floor (SC2.3), and validation (SC-Tier 3).

---

## 2. Data foundation (SC1.1)

CZ Biohub's data is the **Tabula** family, distributed through CELLxGENE (the survey established this; raw Tabula Sapiens reads are controlled-access, but the count matrices are open). Rather than the 136 GB full Tabula Sapiens download, matched-by-tissue collapses the footprint: **liver + spleen + lung + bone marrow trios = 9.5 GB, 357k cells** across the three species — one consortium, no cross-atlas batch confound.

- **Cell-type harmonization:** 96 distinct Cell Ontology terms rolled to a **34-type broad panel** via OLS4 hierarchical ancestors (94/96 mapped; ≤12.7% unmapped, lemur only).
- **Ortholog space:** 60,606 human genes → **16,042 three-way 1:1 triples**, **14,073 usable** (present in all matrices) — essentially the same gene space as the bulk 14k variance-filtered network.
- **Shared cell types (≥100 cells/species):** 10 well-powered types used throughout — hepatocyte, plasma cell, B/NK/T cell, macrophage, monocyte, endothelial, fibroblast, pneumocyte.

![Atlas overview]({{artifact:525dccd0-5099-477e-85b1-b7d2560b280f}})

*Later widened (SC1.2b, "option 3") with muscle/adipose/pancreas (3-way) + testis/ovary/uterus/pituitary (2-way or single-species) to reach phylo-signal home tissues: 1,116 pseudobulk profiles across 11 tissues.*

---

## 3. Composition vs co-regulation (SC1.2)

SC1.2 is a **diagnostic, not network inference**: for each WGCNA module, does its bulk co-expression reflect within-cell-type coherence or cross-sample composition covariance? Method: per-module cell-type enrichment on 857 (later 1,116) pseudobulk profiles, then `coherence_retention` = within-dominant-cell-type gene-gene coherence ÷ all-profile coherence.

**Of 27 modules, only those whose bulk home tissue is in the single-cell panel are evaluable.** In the core 4-tissue panel, **5/27** were evaluable and *none* was a clean within-cell-type co-regulation positive — all composition-driven or mixed. **M14 (spleen/plasma cell)** was the least composition-contaminated (retention 0.80) — the best candidate for direct regulon testing, which SC1.3 then confirmed.

![Module deconvolution]({{artifact:57a69cd9-a155-4c5d-842b-3e46e9086305}})

After widening, **M11 (adipose)** was the one additional properly-powered module — composition-driven (endothelial/stromal). The strongest phylo-signal modules (M3 pituitary, M20 testis) remained **data-limited, not method-limited**: the atlases these consortia built do not sample those tissues at cross-species depth (M3 lemur-only, M5 ovary human-only).

![Widened phylo-signal deconvolution]({{artifact:9cbe5a92-d584-4f00-80d4-c53323dd8111}})

---

## 4. Per-cell-type regulons (SC1.3)

Regulon inference used the GRNBoost2 core (gradient-boosted regression, per target gene) directly in scikit-learn — the dask/arboreto scheduler cannot spawn under the sandbox; the dask-free core was validated on a synthetic planted network (true regulator recovered at importance 0.91 vs <0.05 noise). Full pySCENIC + cisTarget motif pruning remains SC-Tier 4 (cisTarget DBs are human/mouse only).

Restricting targets to module genes (avoiding a cell-cycle dropout artifact), the plasma-cell (M14) and hepatocyte (M13) regulons were inferred in all three species:

- **XBP1 is the #1 plasma-cell regulator in all three species** — the conserved secretory master. PRDM1(BLIMP1) is present in human+lemur but not mouse top-25, so only XBP1 is strictly rank-1-conserved.
- **The bulk cocktail TFs demote species-specifically, not uniformly.** The M14 IKZF1×IRF4 pair (top spleen bulk cocktail, SHAP 1.15) sits deep in the human regulon (IKZF1=58, IRF4=120) and its IRF4 component also demotes in mouse (IRF4=42/168); only in lemur does the pair rank near the top (IRF4=3). The pair reconciles as genuine in lemur only (SC1.4) — the demotion is human+mouse, not human-alone.

![Regulon inference]({{artifact:91535a7b-e699-4074-8663-f53cc6d6a056}})

---

## 5. Bulk↔single-cell reconciliation (SC1.4)

Each bulk cocktail was scored **per species**: *genuine* if both TFs rank ≤30 in the cell-type regulon and co-regulate ≥2 shared module targets; *composition/weak* otherwise; *untestable* if either TF lacks a 3-way ortholog. Of 24 top pairs, 16 were testable.

**Headline: bulk SHAP magnitude does not predict single-cell validation.**
1. **MLXIPL×NR1H4 (hepatocyte) is genuine in all three species** — yet bulk *under*-ranked it (SHAP 0.20). Single-cell surfaced a robustly conserved cocktail the bulk ranking buried.
2. **NR1I3×ATF5 (top liver bulk cocktail, SHAP 1.11)** is genuine in mouse+lemur, composition/weak in human.
3. **IKZF1×IRF4 (top spleen bulk cocktail, SHAP 1.15)** is genuine in lemur only — the real plasma-cell master is XBP1, so this headline bulk cocktail is substantially a lymphocyte-composition signal, strongest in human.
4. Several M14 pairs (NKX2-3×IRF4, IKZF1×FOXA1) are not expressed in plasma cells at all.

![Bulk-single-cell reconciliation]({{artifact:5cbb0657-e069-4137-8ec4-62222a55cb07}})

The same bulk cocktail can be genuine regulation in one atlas and a composition artifact in another — the reconciliation is per-cocktail and per-species, never a blanket verdict.

---

## 6. Cross-species regulon conservation (SC2.1) — the bulk thesis, at cell-type resolution

For 10 shared cell types × 3 species, regulons were inferred on a fixed 400-variable-gene common target panel, then two axes were separated:
- **Regulator-identity conservation** — Spearman rank correlation of TF total-importance across species.
- **Target-set conservation** — mean target-list Jaccard for shared top regulators.

**The bulk thesis holds at cell-type resolution: mean regulator-identity conservation = 0.42 > mean target-set conservation = 0.17, and every cell type with a computable target score sits below the y=x line.** Regulator identity is the conserved axis; target wiring is the labile one — exactly "membership conserved, connectivity drifts," now localized to individual cell types. Most regulator-conserved: NK/macrophage/T cell (0.46–0.48); least: pneumocyte/hepatocyte (0.31–0.34). Lowest target conservation: NK cell (0.09), plasma cell (0.11).

![Regulon conservation]({{artifact:cc616411-8f6f-49fa-a454-14bcb2a6e181}})

---

## 7. Synthesis with Phase A phylogenetic signal (SC2.2)

Fusing Phase A (Blomberg K, Zsummary) × driver cell type (SC1.2) × cross-species regulon conservation (SC2.1), for the 6 modules with a reliable single-cell driver:

**M14/plasma cell is the clearest case** — high phylogenetic signal (K=0.40, K_p=0.004) coinciding with a driver cell type whose target wiring is among the least conserved (0.11), even though its regulator identity (XBP1) is conserved. But the pattern does **not** generalize cleanly: M11/endothelial (also significant phylo-signal, K=0.29) has *higher* target conservation (0.19) than several non-significant modules. With n=6 and M11 as a counterexample, this is a **suggestive single case, not a module-population trend** — a definitive test needs deeper multi-species atlases.

The interpretive point that does hold: **phylogenetic signal at the tissue level can arise from either conserved cell-intrinsic regulation (M14) or conserved tissue composition (M11) — and single-cell is exactly what distinguishes them.**

![Synthesis]({{artifact:97ee8316-6e79-460b-b12d-85ae09f35d60}})

---

## 8. The conservation floor to teleost (SC2.3, Track C) — "does it go the distance?"

A one-directional positive control: does the conserved regulatory core reach a teleost fish (~450 My)? This split **brackets** the clades of downstream interest — Marsupialia (~160 My) and Afrotheria (~100 My) — so a regulator conserved to zebrafish necessarily spans those intermediate nodes, even though no single-cell atlas exists for either clade to test directly.

Three probe lineages (neuron, muscle, immune) from the Developmental Zebrafish Reference Atlas, restricted to **8,486 strict 1:1 human↔zebrafish orthologs** (filtering out the teleost-WGD one-to-many), tested whether canonical mammalian master regulators recur in the zebrafish top-20. **They do, at strong ranks:** muscle MEF2D=1, SOX6=2; immune SPI1(PU.1)=4, FLI1=6, IKZF1=9; neuron EBF3=4, PBX3=5. Permutation null (10,000 random TF sets): **muscle p=0.003, neuron p=0.002, immune p=0.016**.

![Deep-outgroup floor]({{artifact:811534d1-7af0-4bce-b684-c7201ef3f7b3}})

**Scoped honestly:** this confirms regulator-*identity* conservation reaches teleost for deep lineage masters. It does not test target wiring (already the labile axis among mammals), and negatives are uninterpretable (larval-only zebrafish, coarse cross-clade alignment, 1:1-ortholog bias). Only positive hits carry information — and they landed. **Prediction: MEF2, SPI1/PU.1, IKZF1, EBF3, PBX/MEIS hold across marsupials and afrotherians.**

---

## 9. Validation (SC-Tier 3)

Three independent checks on the 10 human cell-type regulons:

1. **DoRothEA A/B gold standard:** cell-type AUROC ~0.57, *below* the bulk tissue-average (0.674). Expected — DoRothEA is tissue-agnostic (curation/ChIP, largely bulk), so it rewards aggregate breadth over cell-type specificity. The single-cell layer buys **resolution, not gold-standard breadth**; all cell types are above random.
2. **Motif support: mean 83%** (0.70–0.95) of top-20 regulators carry a JASPAR motif — genuine sequence-specific TFs, not co-expression artifacts.
3. **Cross-species held-out: mean Spearman 0.53** (human+mouse → lemur), and **held-out accuracy tracks SC2.1 regulator-identity conservation at ρ=0.79** — the most-conserved cell types predict lemur best. An independent, predictive confirmation of the conservation gradient.

![Validation]({{artifact:0daf33e1-f2bb-407d-a9a3-83035aca01a4}})

---

## 10. Bottom line

- **The bulk "membership conserved, wiring drifts" thesis is confirmed at cell-type resolution** (SC2.1: regulator identity 0.42 > target wiring 0.17, universal across cell types), and independently reconfirmed by a held-out predictive test (SC-Tier 3, ρ=0.79 with conservation).
- **Single-cell resolves the composition confound the bulk network could not** — reclassifying headline bulk cocktails as genuine (MLXIPL×NR1H4, all 3 species) or composition-driven (IKZF1×IRF4, largely human), per species.
- **The conserved regulator core reaches teleost** (SC2.3, p≤0.016 all lineages), which brackets marsupials and afrotherians and predicts these masters "go the distance."
- **The thesis holds under motif pruning** (SC-Tier 4): with full pySCENIC + cisTarget + bootstrap stability on the four headline cell types, regulator-set conservation runs 3.2–5.0× above its random floor and 3.5× above target-wiring conservation, and the canonical masters (XBP1, HNF4A, CEBPB/FOS) survive motif pruning.
- **Honest boundaries:** the phylo-signal↔regulon-divergence synthesis (SC2.2) is a suggestive single case (M14), not a powered population test; the strongest phylo-signal modules (pituitary, testis) are data-limited; deep-outgroup and DoRothEA results are interpreted asymmetrically; SC-Tier 4 covers 4 of 10 cell types.

## 11. Motif-pruned, bootstrap-stabilized regulons (SC-Tier 4)

Full pySCENIC — GRNBoost2 → cisTarget motif pruning → AUCell, with 10 bootstrap runs per unit — was run natively (Dockerized) for the four headline cell types across all three species (12 units, ~26 h compute). This replaces the co-expression regulons of §4–§6 with motif-supported, stability-filtered networks for the cell types that carry every headline claim.

![SC-Tier 4 summary]({{artifact:art_1e3c0a94-b672-4cfd-845b-9c6817dcc14a}})

**The conservation thesis survives the stricter method.** On the motif-pruned regulons, regulator-set conservation exceeds its random floor by **3.2–5.0×** in every cell type (monocyte 4.7×, T cell 5.0×), and regulator-set conservation exceeds target-set (wiring) conservation by a mean of **3.5×** — the same ordering the co-expression analysis found (2.4×). Conserved *regulators*, divergent *targets*, now confirmed with cisTarget motif support.

**Canonical masters survive cisTarget pruning where it matters.** Motif pruning is strict — only ~28% of the top-20 co-expression regulators survive as motif-supported regulons — but the lineage masters are among the survivors: **XBP1** (plasma cell, human + mouse), **HNF4A** (hepatocyte, mouse + lemur), and **CEBPB + FOS** (monocyte, all three species). Of the canonical masters tested, 9/22 survive in ≥1 species and 4/22 in ≥2. The XBP1 result is more nuanced than the co-expression run implied: it is a motif-supported plasma-cell regulon in human and mouse but not lemur, where its regulon is dominated by other factors.

**Bootstrap stability gives a confidence layer the earlier networks lacked.** Averaged across units, ~3,900 edges recur in ≥8/10 bootstraps (~7,200 in ≥7/10) — a reproducible network core distinct from the long tail of run-to-run noise.

*Method note: dask/arboreto cannot spawn workers under the analysis sandbox, so the pipeline was containerized and run on the user's Mac; the GRNBoost2 core is identical to arboreto's. One unit (plasma cell/lemur) ran ~3× slower than its siblings for reasons not captured in the logs.*

### Further work (SC-Tier 4, remaining)

Extend pySCENIC to the six Tier-2 cell types (B/NK/macrophage/endothelial/fibroblast/pneumocyte); a **stage-matched developmental mammalian atlas** (e.g. mouse organogenesis) to make the zebrafish comparison bidirectional; additional clades (marsupial/afrotherian atlases as they appear) to widen the phylogenetic span toward the bulk 26-species panel; the 660 CELLxGENE spatial datasets for tissue-architecture context.

---

*All figures and tables are saved as project artifacts; the full method-level plan with per-step parameters is in `analysis_plan_singlecell.md`.*
