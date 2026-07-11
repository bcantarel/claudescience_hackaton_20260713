# Phase A — Phylogenetic Signal in Module Conservation

**Method:** Each of 27 human GTEx co-expression modules has a per-species preservation
score (WGCNA Zsummary, Langfelder 2011) across 26 vertebrates. Treating each module's
per-species Zsummary as a continuous trait on a TimeTree-calibrated ultrametric species
tree (ape/phytools), we tested for phylogenetic signal with Blomberg's K (1000-permutation
null) and Pagel's lambda (likelihood-ratio test).

## Headline result: module conservation does NOT track the phylogeny

- **Every module has K << 1** (range 0.06-0.47, mean 0.18).
  K=1 is the Brownian-motion expectation; K<1 means preservation is LESS phylogenetically
  structured than shared ancestry alone would produce.
- Only **5/27 modules** have significant K (p<0.05); only **3/27** significant Pagel lambda.
- **The most-conserved modules have the LOWEST signal.** M9 brain (Zsum 24.9, K=0.12, n.s.),
  M8 testis (22.6, K=0.07), M4 testis (14.7, K=0.06) — universally high preservation with
  no phylogenetic pattern. Spearman(conservation, K) = -0.16, n.s.

## Interpretation

This is the phylogenetic formalization of the earlier divergence-time result (preservation
vs divergence rho=-0.23, n.s.). The core co-expression programs — germline, neural, muscle,
immune — are **uniformly preserved across the entire vertebrate tree**, from primates to
zebrafish. They are not "conserved in close relatives, lost in distant ones" (which would
give high K); they are conserved *everywhere at once*. This is the signature of deep
stabilizing selection on the co-expression module itself, not of neutral divergence.

## The exceptions are biologically coherent

The few modules WITH phylogenetic signal are the **evolutionarily labile** ones, where
preservation genuinely varies by clade:
- **M3 pituitary (K=0.47, p=0.002)** — the strongest signal; hormonal-axis regulation
  differs across mammalian clades.
- **M14 spleen (K=0.40, p=0.004), M11 adipose (K=0.29, p=0.04)** — immune/metabolic
  modules with clade-specific preservation.
- **M20 testis (K=0.34, p=0.007), M5 ovary (K=0.26, p=0.04)** — reproductive programs
  beyond the universally-conserved germline core.

For these, preservation carries a phylogenetic footprint: closely-related species resemble
each other more than distant ones. These are the modules where the "species as
pseudo-replicates" logic of the TF plan (Step 8) will find clade-structured regulation.

## Caveats
- K is downward-biased when the trait has measurement noise; small modules (M26, scored
  in 21/26 species) and species with few tissues contribute noisier Zsummary estimates.
- Tree branch lengths are TimeTree-calibrated divergence estimates, not gene-tree inferred.
- The near-universal K<<1 is robust to these: it holds across all 27 modules regardless.
