# Findings — Conserved Co-expression & TF Regulatory Logic Across Vertebrates

A complete record of what was done and what was found. Companion to `README.md`
(orientation) and `FUTURE_DIRECTIONS.md` (the plan-step audit of what was *not* done).

---

## The question, and how it narrowed
Started from "shared gene co-expression networks across the domains of life,"
narrowed with the researcher to: **discover tissue-resolved co-expression modules
in a well-powered reference (human GTEx), then test which modules are preserved
across vertebrates, and build the transcription-factor regulatory layer on the
conserved ones.** The move to a tissue-resolved reference was deliberate —
organism-averaged networks collapse the cell-type/differential-expression signal
that was the whole point.

---

## Stage 1 — Module discovery (human GTEx)
- **Input:** recount3 GTEx, 30 tissues, 3,267 samples (balanced subsample), CPM→log2,
  variance-filtered to 14,000 genes.
- **Method:** WGCNA, reimplemented in pure Python (no osx-arm64 r-wgcna build):
  signed-hybrid adjacency β=8 → signed TOM → average-linkage hclust →
  dynamicTreeCut → eigengene merge r>0.75.
- **Result: 27 modules**, 7,034 assigned genes. Cleanly tissue-organised and
  marker-validated (pancreas M23 6/6, liver M13 5/6, muscle M18 5/6, spleen M10 5/6).
- **Key structural finding:** WGCNA resolves *sub-tissue cellular programs*. Brain
  splits into neuronal-synaptic (M9), mitochondrial (M26) and glial/adhesion (M19);
  liver into xenobiotic-metabolism (M21) and core-metabolism (M13); testis into
  meiotic-recombination (M8), DNA-repair (M7) and spermatogenesis (M4). This is the
  cell-type structure the researcher wanted, recovered from bulk co-expression.
- **Independent cross-check:** an independently-built mouse WGCNA (ENCODE, 419
  samples) recovered **23/26 human modules** (Bonferroni-significant best-match).

## Stage 2 — Cross-species preservation (26 vertebrates)
- **Panel:** 26 species, 12 clades, 6.4–429 My divergence (Bgee v15.2 + recount3 +
  FarmGTEx). 4 assembly-mismatched species (chicken/dog/cat/sheep) recovered via a
  gene-symbol ortholog bridge through Bgee call files — this **added Carnivora**.
- **Method:** WGCNA `Zsummary` preservation (Langfelder 2011), 1:1 orthologs.
- **Headline result — conservation is module-identity-driven, NOT divergence-driven:**
  preservation vs divergence time **Spearman ρ = −0.24, p=0.23 (n.s.)**.
- **Universally conserved:** brain M9 (mean Zsum 24.9, preserved in 96% of species),
  testis M8 (22.6, 100%), ovary M2 (21.5, 100%), muscle M18 (17.3), spleen M10 (17.0).
- **Labile:** pancreas M23 (−0.85, 15%), adipose M25 (0.18), spleen M14 (0.87),
  lung M27 (0.96).
- **Mechanistic handle:** Zdensity is high but Zconnectivity ≈ 0 — module *membership*
  is conserved while intramodular *hub wiring* diverges.

## Phase A — Phylogenetic signal
- **Method:** Blomberg's K (1000-perm) + Pagel's λ (LR test) per module, on a
  TimeTree-calibrated ultrametric 26-species tree (ape/phytools).
- **Result: conservation does NOT track the phylogeny.** Every module K ≪ 1
  (range 0.055–0.468, mean 0.18; K=1 = Brownian expectation). Only 5/27 have
  significant K: **M3 pituitary (K=0.47, p=0.002)**, M14 spleen, M20 testis,
  M11 adipose, M5 ovary.
- **Counterintuitive core:** the *most-conserved* modules have the *lowest* K
  (M9 brain K=0.12 n.s., M8 testis K=0.07). Interpretation: core programs are
  conserved *everywhere at once* (deep stabilizing selection), not graded by
  relatedness; phylogenetic signal lives in the **labile** modules, where
  regulation genuinely varies by clade.

## Phase B — TF regulatory layer
**B1 — TF annotation.** 793 TFs in the network (403 module-assigned). DBD families
(C2H2-ZF 344, homeodomain 124, bHLH 58, bZIP 43, nuclear receptor 39, forkhead 28…),
892 JASPAR CORE motifs (58% coverage), expression breadth, tissue-activity flags.
**M24 is a HOX patterning module** — 32/33 TFs are the full HOXA/B/C/D complement +
TBX15, recovered from co-expression alone; also the tightest human↔mouse
correspondence (Jaccard 0.75).

**B2 — Baseline GRN (3-method ensemble).** GENIE3 + GRNBoost2 + CLR, rank-product
ensemble. 396,286 edges; 165,531 with ≥2-method support. **Sanity gate passes and
sharpens under consensus:** HNF4A #1 in liver, IKZF1 #1 in immune, SOX2 #2 in brain,
CEBPA #1 — master regulators rank top of their modules.

**B-Step 7 — TF cocktails.** XGBoost + SHAP interaction per module recovers textbook
combinatorial codes purely from expression: liver **HNF1A+HNF4A+HNF1B** (synergy
HNF4A×NR1H4/FXR), immune **IKZF1×SPI1**, testis **FOXM1×E2F2** (cell-cycle), the HOXA
cocktail. Strongest single interactions are in spleen/immune M14 (IKZF1×BHLHA15=1.18,
IKZF1×IRF4=1.15), then liver M13 NR1I3/CAR×ATF5 (1.11).

**Module functional annotation** (g:Profiler GO:BP/KEGG/Reactome). Every module has a
coherent biological-process signature refining its tissue label; the paralogous
modules split by *program* (liver→P450 vs carboxylic-acid catabolism; testis→meiotic
recombination vs DNA repair; brain→synaptic vs mitochondrial vs adhesion).

## Regulon conservation (the synthesis)
Fuses all four layers. **The regulatory backbone is the most-conserved part of a
module:** comparing edge-pattern preservation (human→mouse) of each module's
TF-regulator sub-block vs the full module, TF sub-networks preserve *better* on
average (0.46 vs 0.35, Wilcoxon p=0.06; better in 10/15 modules). Liver HNF core
0.94 vs 0.53 full module. The peripheral membership drifts; the core regulatory
logic is locked.
- **Exceptions localise clade-variable regulation:** M11 adipose (Δ=−0.17, K=0.29,
  significant phylo signal) has regulators that both rewire and vary by clade.
  (M22 vagina also preserves worse but has NO phylo signal — likely sparse-data noise.)
- **TF-family axis:** the most phylogenetically-structured module, M3 pituitary
  (K=0.47), is **93% C2H2 zinc-finger** — the fastest-evolving mammalian TF family.
  Phylo-signal modules average 48% C2H2-ZNF vs 27% elsewhere (n=17; suggestive,
  ρ=+0.15 n.s.); classical-TF fraction weakly anti-correlates with conservation
  (ρ=−0.47, p=0.057).
- **Answer to the motivating question:** the conserved co-expression architecture
  *does* carry a conserved regulatory logic, borne disproportionately by classical
  TF families, while the clade-variable signal concentrates in KRAB-ZNF-rich modules.

## Validation (DoRothEA gold standard)
Ensemble GRN vs curated DoRothEA regulons (OmniPath, tiers A/B/C). **AUROC 0.67–0.69,
best against highest-confidence tier A (0.69)**; AUPRC 4.5–7× over baseline — the
expected profile for a co-expression GRN vs a ChIP/curation gold standard. Master
regulators recover well individually: **HNF1A 0.93, FOXA2 0.78, SPI1 0.78, SOX2 0.75,
FOXA1 0.70, HNF4A 0.65, CEBPA 0.63** — but **GATA2 0.57 (near baseline)** is the one
sanity-gate TF DoRothEA does not confirm, coherently a member of the labile ZNF-rich
M11 module. Recall is capped by construction (top-30 regulators/target).

---

## Data-availability findings (negative results worth keeping)
- **Afrotheria / Xenarthra unavailable.** Elephant: 7 solid tissues, ~n=1 each —
  below the co-expression replication floor (verdict NEGATIVE). Armadillo/tenrec
  similarly lack replicated multi-tissue RNA-seq. Documented gap, not a fixable one.
- **Marsupials feasible but deferred.** Koala (5 tissues incl. brain/liver/spleen/
  testis) + Tasmanian devil (3 normal tissues) are assemblable from SRA (~161 GB raw
  fastq → salmon), but exceed the 13 GB sandbox. Would directly test the opossum
  low-preservation anomaly (lowest-preservation mammal).
- **Pig GTEx** portal is a JS single-page app (data URLs not statically extractable);
  Bgee pig already covers it (123 tissues). FarmGTEx cattle labeled matrix was
  truncated at source (2,784 of 8,742 samples served) but usable.

## Method decisions worth flagging (honest record)
- WGCNA is a **pure-Python reimplementation** (no osx-arm64 r-wgcna), validated
  against an independent mouse network.
- GRN third method is **CLR, substituted for the plan's named ARACNE/PIDC** for local
  tractability (all three are MI-based; the rank-product ensemble is robust to the choice).
- Soft-power β=8 chosen at the R² elbow (~0.74); scale-free R² never clears 0.80 —
  expected for heterogeneous 30-tissue data.
- FarmGTEx cattle kept **separate** from the main sweep (ag-skewed tissue coverage,
  not a balanced organ panel).
