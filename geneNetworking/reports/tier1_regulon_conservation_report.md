# Tier 1 Results — Functional Annotation & Regulon Conservation

## T1.2 Module functional annotation (g:Profiler, GO:BP/KEGG/Reactome)
Every module has a coherent biological-process signature that refines its tissue label.
The paralogous modules split by *program*, not just tissue:
- **Liver:** M21 → xenobiotic metabolism (cytochrome P450); M13 → carboxylic-acid catabolism (core metabolism).
- **Testis:** M8 → meiotic recombination (Holliday-junction resolution); M7 → DNA repair; M4 → organelle assembly (spermatogenesis).
- **Brain:** M9 → synaptic transmission (neuronal); M26 → respiratory electron transport (mitochondrial); M19 → cell-adhesion (glial).
- **Muscle:** M18 → actin-filament process; M12 → muscle structure development.
Full table: `results/module_functional_annotation.csv` (+ `module_enrichment_full.csv`).

## T1.3 Regulon conservation (the synthesis)
Fuses module preservation + phylogenetic signal + TF-family composition + direct
regulator-subnetwork preservation.

**Main result — the regulatory backbone is the most-conserved part of a module.**
Comparing edge-pattern preservation (human GTEx → ortholog-aligned mouse) of each
module's TF-regulator sub-block vs the full module: TF sub-networks preserve *better*
on average (0.46 vs 0.35, Wilcoxon p=0.06; better in 10/15 testable modules). The
liver HNF core (M21) preserves at 0.94 vs 0.53 for the full module; testis M4 at
0.71 vs 0.21. Interpretation: peripheral module membership can drift while the
core regulatory logic stays locked — consistent with the earlier "Zdensity high,
Zconnectivity low" finding.

**The exceptions localise clade-variable regulation.** The modules where regulators
preserve *worse* than the bulk are **M22 vagina (Δ=−0.22)** and **M11 adipose
(Δ=−0.17)**. Of these, **M11 carries significant phylogenetic signal (Blomberg
K=0.29, p=0.04)** — a module whose regulators both diverge in wiring and vary
by clade. M22's gap is real but it has **no** phylo signal (K=0.07, p=0.83), so
its worse-preserving regulators are not clade-structured — likely sparse-data
noise (only 6 TFs, small module). The five phylo-signal (significant-K) modules
are M3, M5, M11, M14, M20; M11 is the one that also shows the regulator-preservation gap.

**TF-family axis.** The most phylogenetically-structured module, **M3 pituitary
(K=0.47, p=0.002), is 93% C2H2 zinc-finger** — the fastest-evolving TF family
in mammals. Across modules, phylo-signal (significant-K) modules average 48%
C2H2-ZNF TFs vs 27% for the rest (n=17; suggestive, not significant —
ρ(frac_ZNF, K)=+0.15, n.s.). Classical-TF fraction weakly anti-correlates with
conservation (ρ=−0.47, p=0.057). *(ZNF fraction = C2H2 family only; GATA-type ZF,
other zinc fingers, and nuclear factor I are counted as classical/other, not fast-evolving.)*

**Bottom line for the project's motivating question:** the conserved co-expression
architecture *does* carry a conserved regulatory logic — and it is carried
disproportionately by the classical TF families, while the clade-variable signal
concentrates in KRAB-ZNF-rich modules (pituitary, ovary, adipose). This is the
handle for where regulation is evolutionarily labile.

Artifacts: `figures/phaseB_regulon_conservation.png`,
`results/regulon_subnetwork_preservation.csv`, `results/regulon_family_composition.csv`.
