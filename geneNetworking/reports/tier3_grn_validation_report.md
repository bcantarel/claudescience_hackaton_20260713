# Tier 3 Results — GRN Validation against DoRothEA

Benchmark of the ensemble GRN against **DoRothEA** curated human TF-regulons
(via OmniPath; confidence tiers A/B/C), the plan's Step 10 gold-standard test.

## Design
Fair benchmark: gold restricted to TFs & targets inside our candidate universe
(793 tested TFs × 7,034 module targets); only GRN edges from DoRothEA-covered TFs
evaluated. Edge confidence = −log10(rank_product) from the 3-method ensemble.

## Aggregate result (honest)
| Tier | gold edges | TFs | AUROC | AUPRC | baseline | enrichment |
|---|---|---|---|---|---|---|
| A       | 1,619 | 174 | **0.693** | 0.039 | 0.0055 | 7.1× |
| A/B     | 4,270 | 201 | 0.674 | 0.040 | 0.0089 | 4.5× |
| A/B/C   | 8,854 | 250 | 0.678 | 0.048 | 0.0167 | 2.9× |

AUROC 0.67–0.69 with best discrimination against the **highest-confidence tier A** —
the expected profile for a co-expression GRN vs a ChIP/curation gold standard, and
in line with published GENIE3/GRNBoost2 benchmarks. AUPRC is low in absolute terms
(sparse positives) but 4.5–7× over baseline.

## Master regulators recover well individually
Per-TF target recovery AUROC (all 8 sanity-gate TFs with ≥5 curated targets):
**HNF1A 0.93, FOXA2 0.78, SPI1 0.78, SOX2 0.75, FOXA1 0.70, HNF4A 0.65, CEBPA 0.63,
GATA2 0.57**. Seven of the eight recover their DoRothEA targets clearly above chance;
**GATA2 is the exception at AUROC≈0.57 (near baseline, 19/167 targets recovered)** —
a hematopoietic/endothelial regulator whose module (M11 adipose/endothelium) is one
of the labile, ZNF-rich, low-preservation modules, so its weak recovery is consistent
with the rest of the analysis rather than a surprise. The aggregate AUROC is diluted
by C2H2/KRAB-ZNF TFs, which have few curated targets and noisier co-expression signal.

## Honest limitations
- **Recall is capped by construction:** the GRN keeps only the top-30 regulators
  per target, so most of a large DoRothEA regulon can't be recovered even in principle.
- DoRothEA blends ChIP, motif and curated evidence — a co-expression GRN captures a
  different (correlational) edge definition, so partial overlap is expected, not a failure.
- Full **ENCODE/ChIP-Atlas** overlap and **leave-one-species-out** prediction remain
  in the future-directions plan (need genomes / the cross-species orthogroup matrix).

Artifacts: `figures/phaseB_grn_validation.png`,
`results/grn_validation_benchmark.csv`, `results/grn_validation_per_TF.csv`.
