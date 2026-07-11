# Conserved gene co-expression networks across amniotes — feasibility pilot

**Question.** Can we identify gene co-expression networks that are conserved across
species, starting in mammals and extending to other amniotes (birds, reptiles)?

**Answer from this pilot: yes, and the signal is strong and biologically sensible.**

---

## What was done

A proof-of-concept across **11 vertebrate species** spanning ~350 My of divergence:

- **Mammals (7):** human, mouse, rat, dog, cow, pig, horse
- **Birds (2):** chicken, zebra finch
- **Reptile (1):** anole lizard
- **Amphibian outgroup (1):** *Xenopus tropicalis*

**Gene panel:** 87 genes across 6 canonical functional modules — large- and
small-subunit ribosome, oxidative phosphorylation (OXPHOS), proteasome,
spliceosome, and DNA-replication/cell-cycle (MCM helicase + cyclins/CDKs).

**Data source.** STRING v12 **co-expression evidence channel** (`ascore`). STRING
computes a per-organism co-expression network from expression compendia for
>12,000 species; the `ascore` is that curated co-expression signal, not a proxy.
Cross-species comparison uses STRING's best-homology mapping from human to each
species (79–87 of 87 orthologs recovered per species), projecting every network
into a shared human-symbol label space.

## Key findings

1. **Within-module co-expression is highly conserved; cross-module is not.**
   Mean conservation (fraction of species retaining a co-expression link):
   within-module **0.90** vs cross-module **0.29** (Mann–Whitney p ≈ 4×10⁻¹⁹¹).
   453 of 588 within-module gene pairs (77%) show co-expression in **every species
   in which both genes have a mappable ortholog** (all *scored* species); of these,
   323 (55% of all within-module pairs) are co-expressed in **all 11 species** with
   no ortholog gaps. Conservation is scored as a fraction of scored species, so
   pairs with an ortholog missing in 1–3 species (e.g. birds, where 79–85/87
   orthologs map) can still be fully conserved among the species where they are
   measurable.

2. **Module ranking matches known biology.** Ribosome (large subunit) is
   essentially invariant (mean conservation 1.00; 100% of its edges co-expressed in
   every scored species); cell cycle, proteasome and small-subunit ribosome are
   ≥0.96; OXPHOS 0.90. The
   **spliceosome is the most evolutionarily labile module (0.53)** — consistent
   with lineage-specific variation in splicing regulation.

3. **Network topology tracks phylogeny.** Pairwise network overlap (Jaccard on
   binarized co-expression edges) averages 0.93; mammal–mammal pairs (0.948) are
   more similar than mammal–non-mammal pairs (0.923), and overlap with the mammal
   networks decays with divergence time from human (Fig. panel d).

## Feasibility notes / caveats

- **Data reachability.** recount3 (via its S3 backend) is reachable from this
  environment. **Bgee** — the many-species curated resource you flagged — is
  reachable at the server but sits behind a Cloudflare bot-challenge that the
  `BgeeDB` client cannot clear here; getting Bgee's per-species matrices will
  likely need a manual/browser download or a different access route.
- **STRING vs. raw RNA-seq.** STRING's `ascore` is a pre-computed co-expression
  network, which makes cross-species comparison immediate and avoids per-species
  normalization/batch issues — but it is one integrated summary per species, not
  the raw (tissue × sample) expression matrix. The full plan in
  `TF_Regulatory_Network_Analysis_Plan.docx` (orthogroup expression matrices from
  bulk RNA-seq → GRN inference → TFBS integration) needs the raw matrices; this
  pilot validates the **conservation-scoring layer** (its Steps 8–9) on real data
  before that heavier pipeline is built.
- **Ortholog mapping.** Best-homology hits are 1:1 approximations; a
  production run should use explicit orthogroups (fastOMA / OMA / Ensembl
  Compara) as the plan specifies, especially for multi-copy families.

## Artifacts

- `coexpr_conservation.png` — 4-panel summary figure
- `coexpr_conserved_edges.csv` — 453 within-module edges conserved in all *scored* species (323 flagged `all_11` = present in all 11)
- `coexpr_module_summary.csv` — per-module conservation statistics
- `coexpr_full_matrix.csv` — all 3,741 gene-pair × 11-species co-expression scores
- `coexpr_network_jaccard.csv` — pairwise cross-species network-overlap matrix
