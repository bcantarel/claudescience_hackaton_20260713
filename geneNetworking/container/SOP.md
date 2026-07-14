# Standard Operating Procedure
## Conserved gene co-expression networks & TF regulatory logic across vertebrates

A standalone procedure for reproducing the geneNetworking analysis from a clean
machine, using the container in `container/`. It runs the pipeline end to end and
gives the operator **two interchangeable routes for module discovery**: the
**canonical R WGCNA** package (in the container) and the repo's pure-Python
reimplementation.

Companion documents (in the repo root): `README.md` (orientation),
`FINDINGS.md` (every result with numbers), `FUTURE_DIRECTIONS.md` (what was and
wasn't done). This SOP is the *how-to-run*; those are the *what-and-why*.

---

## 0. Pipeline map

```
Stage 1   Discover modules        human GTEx (recount3) -> WGCNA -> 27 modules
Stage 1b  Cross-check             independent mouse WGCNA (ENCODE) -> 23/26 recovered
Stage 2   Test preservation       26 vertebrates (Bgee/FarmGTEx) -> WGCNA Zsummary
------------------------------------------------------------------------------------
Phase A   Phylogenetic signal     Blomberg's K / Pagel's lambda on preservation
Phase B   TF regulatory layer     TF annotation -> 3-method ensemble GRN
                                   -> cocktails (SHAP) -> validation (DoRothEA)
(optional) SC Tier-4              single-cell pySCENIC regulons (cross-species)
```

Each numbered stage maps to a script in `scripts/` (or `container/R/`) and to
result files in `results/` / `figures/`. The mapping is in §7.

---

## 1. Prerequisites

- **Docker** (Desktop on macOS/Windows, or Engine on Linux) with Compose v2.
- **Memory:** the GRN steps (GENIE3/GRNBoost2 over ~14,000 genes) and pySCENIC
  are the RAM peaks. Set **Docker Desktop → Settings → Resources → Memory ≥ 32 GB**.
  `docker-compose.yml` sets `mem_limit: 32g`; the host VM cap must be ≥ that.
- **Disk:** code + envs image ≈ 6–8 GB. Data is downloaded at runtime into the
  mounted repo, not into the image:
  - recount3 GTEx + mouse: a few GB.
  - Bgee per-species tarballs: fetched and **deleted after each species** by
    `04_bgee_preservation_sweep.py` (peak ~1–2 GB at a time).
  - Optional SC Tier-4: ~9.5 GB h5ad + ~2 GB cisTarget feathers.
- **No GPU** required; everything is CPU-bound.
- **Architecture:** pins were resolved for `linux-64`. On Apple Silicon, build
  with `--platform=linux/amd64` (see `BUILD_NOTES.md` §2/§4).

---

## 2. One-time image build

From the **repo root** (build context must be the root so the Dockerfile can
copy `scripts/`, `data/`, `pyscenic_tier4/`):

```bash
docker build --platform=linux/amd64 -t genenetworking:latest -f container/Dockerfile .
```

This creates three isolated conda environments inside one image:

| env        | interpreter        | drives                                             |
|------------|--------------------|----------------------------------------------------|
| `coexpr`   | Python 3.11 / np2  | Stages 1–2, Phase B GRN pipeline                   |
| `wgcna-r`  | R 4.5 + WGCNA 1.74 | **canonical R WGCNA** + Phase A phylo signal       |
| `pyscenic` | Python 3.10 / np1.23 | single-cell Tier-4 regulons                      |

Verify the build (see `BUILD_NOTES.md` §3 for the full smoke-test set):

```bash
docker run --rm genenetworking:latest envs
docker run --rm genenetworking:latest wgcna-r Rscript -e 'library(WGCNA); cat("WGCNA", as.character(packageVersion("WGCNA")),"\n")'
```

**All subsequent commands** are run via compose from the `container/` directory,
which mounts the whole repo read-write at the container's working dir:

```bash
cd container
docker compose run --rm gn <subcommand> ...
docker compose run --rm gn help          # show the subcommand reference
```

Outputs written to `results/` / `figures/` land back on your host, because the
repo is bind-mounted.

---

## 3. Stage 1 — module discovery (human GTEx)

### 3.1 Data acquisition & normalization

Source: **recount3** GTEx (`recount-opendata.s3.amazonaws.com`), 30 tissues,
~3,300 samples subsampled. The normalization recipe is
`scripts/01_normalize_matrix.py` (documents the transform; the recount3
per-tissue download loop is described in `README.md §4`):

1. subsample ≤120 samples/tissue (rng seed 0) to balance tissues,
2. assemble raw base-coverage counts (int64),
3. CPM → `log2(cpm+1)`,
4. keep genes with logCPM > 1 in ≥ 20 % of samples,
5. take the top **14,000 genes by variance** → `wgcna_input.pkl`.

Product: `wgcna_input.pkl` (14,000 genes × N samples). Place it under
`results/` (or wherever you point the driver).

### 3.2 Module discovery — TWO interchangeable routes

Both use identical parameters: signed-hybrid adjacency, soft power **β = 8**,
signed TOM, average-linkage hclust, dynamic hybrid tree cut
(minModuleSize = 30, deepSplit = 2, pamStage = FALSE), then merge close modules
at eigengene correlation > 0.75 (`mergeCutHeight = 0.25`).

**Route A — canonical R WGCNA (in the container; the added capability).**
First export the pickle to the TSV the R driver reads:

```bash
docker compose run --rm gn py tools/pkl_to_tsv.py results/wgcna_input.pkl results/wgcna_input.tsv
```

Then run the driver (optionally do a soft-power sweep first):

```bash
# optional: scale-free-fit sweep + QC plot only
docker compose run --rm gn wgcna --input results/wgcna_input.tsv --outdir results --sweep-power

# full run
docker compose run --rm gn wgcna --input results/wgcna_input.tsv --outdir results --power 8
```

Outputs: `results/stage1_gene_modules_R.csv`, `results/module_eigengenes_R.csv`,
`results/wgcna_softthreshold_R.png`, `results/wgcna_dendrogram_R.png`,
`results/wgcna_run_R.log`.

**Route B — pure-Python reimplementation (original run).**
`scripts/02_wgcna_modules.py` (uses `lib_dynamicTreeCut_patched.py`; note the
filename fix in `BUILD_NOTES.md §5`):

```bash
docker compose run --rm gn py scripts/02_wgcna_modules.py
```

Expected: **27 modules**, 7,034 assigned genes, tissue-organized and
marker-validated. Compare the two routes' `stage1_gene_modules*.csv` by
best-match module overlap to confirm agreement.

### 3.3 Stage 1b — independent mouse cross-check

Repeat §3.1–3.2 on recount3 **mouse ENCODE** (SRP013027, 419 samples), same
recipe, then best-match human↔mouse modules. Expected: **23/26** human modules
recovered (Bonferroni-significant). Products: `results/mouse_correspondence.csv`,
`results/mouse_preservation.csv`.

---

## 4. Stage 2 — cross-species preservation (26 vertebrates)

Source: **Bgee v15.2** per-species RNA-seq TPM
(`https://www.bgee.org/ftp/current/download/processed_expr_values/rna_seq`),
plus recount3 and FarmGTEx (kept separate — ag-skewed). Ortholog mapping via
**Ensembl BioMart** 1:1 orthologs; four assembly-mismatched species
(chicken/dog/cat/sheep) recovered via a gene-symbol bridge through Bgee call
files.

Driver `scripts/04_bgee_preservation_sweep.py` expects (paths in the script use
`/tmp/gtex`; edit to your mounted workdir or symlink):
`wgcna_input.pkl`, `stage1_gene_modules_local.csv`, per-species ortholog TSVs
under `orth/`, and `work_species.csv` (the species list). It downloads each Bgee
tarball, computes WGCNA `Zsummary` preservation (150-permutation null), appends
to `results/allsp_preservation.csv`, and **deletes each tarball** to bound disk.

```bash
docker compose run --rm gn py scripts/04_bgee_preservation_sweep.py
```

Expected headline: conservation is **module-identity-driven, not
divergence-driven** (preservation vs divergence time Spearman ρ = −0.24, n.s.);
brain M9 / testis M8 / ovary M2 universally conserved; pancreas M23 / adipose
M25 labile. Products: `results/allsp_preservation_expanded.csv`,
`results/stage2_module_conservation.csv`,
`figures/stage2_crossspecies_preservation.png`.

---

## 5. Phase A — phylogenetic signal

Tree: `data/species_tree.nwk` (TimeTree-calibrated ultrametric, 26 species).
Trait matrix: `results/phaseA_trait_matrix.csv` (per-species Zsummary per
module). Driver `scripts/05_phaseA_phylo_signal.R` computes **Blomberg's K**
(1000-permutation null) and **Pagel's λ** (LR test) per module — in the
`wgcna-r` env (ape / phytools / nlme):

```bash
docker compose run --rm gn phylo
```

Expected: conservation does **not** track the phylogeny — every module K ≪ 1
(mean 0.18); only 5/27 significant, led by M3 pituitary (K = 0.47, p = 0.002).
Product: `results/phaseA_phylo_signal.csv`, `figures/phaseA_phylo_signal.png`.

---

## 6. Phase B — TF regulatory layer

Run in order, all in the `coexpr` env. Inputs (`wgcna_input.pkl`,
`phaseB_gene_TF_module.csv`, `ME_local.csv`) follow the paths in each script;
external sources are **JASPAR 2024** motifs, **Ensembl BioMart** GO/InterPro TF
annotation, **g:Profiler** REST (`biit.cs.ut.ee/gprofiler`), and **DoRothEA**
via OmniPath.

```bash
# B2 — three GRN methods (each writes an edge table)
docker compose run --rm gn py scripts/06_grn_genie3.py       # ExtraTrees
docker compose run --rm gn py scripts/06_grn_grnboost2.py    # LightGBM
docker compose run --rm gn py scripts/07_grn_clr.py          # mutual-information CLR
# rank-product ensemble of the three
docker compose run --rm gn py scripts/08_grn_ensemble.py     # -> phaseB_GRN_ensemble.parquet

# B-Step 7 — TF cocktails (XGBoost + SHAP interaction)
docker compose run --rm gn py scripts/09_grn_cocktails.py

# module functional annotation (g:Profiler GO:BP/KEGG/Reactome)
docker compose run --rm gn py scripts/10_module_functional_annotation.py

# regulon-conservation synthesis (fuses Zsummary + K + TF family + subnetwork)
docker compose run --rm gn py scripts/11_regulon_conservation.py

# Tier-3 validation vs DoRothEA gold standard
docker compose run --rm gn py scripts/12_grn_validation_dorothea.py
```

Expected: 396,286 ensemble edges (165,531 ≥2-method); sanity gate passes
(HNF4A #1 liver, IKZF1 #1 immune, SOX2 #2 brain); cocktails recover
HNF1A+HNF4A+HNF1B (liver), IKZF1×SPI1 (immune); DoRothEA AUROC 0.67–0.69.
Products: `results/phaseB_*`, `results/grn_validation_*`,
`results/regulon_*`, `figures/phaseB_*`.

---

## 7. Optional — single-cell Tier-4 pySCENIC

Motif-pruned, bootstrap-stabilized regulons across human/mouse/lemur cell
types. This is the numpy<1.24 world; it runs in the `pyscenic` env. It needs the
large h5ad atlases (CELLxGENE) + cisTarget feather DBs — mounted, not baked in.

```bash
# 1. fetch h5ad + cisTarget DBs into pyscenic_tier4/data and .../cistarget_db
docker compose run --rm gn pyscenic python pyscenic_tier4/pyscenic_tier4.py download

# 2. run (Tier-1 cell types first, checkpoints per (cell type, species))
docker compose run --rm gn pyscenic python pyscenic_tier4/pyscenic_tier4.py run \
    --bootstrap 10 --max-cells 2000 --n-workers 11 --mem-limit 3GB
```

Time budget and safety notes are in `pyscenic_tier4/README.md` (Tier-1 all
species ≈ 6–8 h; re-running resumes from `out/tier4_summary.csv`).

---

## 8. Stage → script → output map

| Stage | Script | Env | Key outputs |
|---|---|---|---|
| 1a normalize | `scripts/01_normalize_matrix.py` | coexpr | `wgcna_input.pkl` |
| 1b modules (R) | `container/R/01_wgcna_modules.R` | wgcna-r | `stage1_gene_modules_R.csv`, `module_eigengenes_R.csv`, QC PNGs |
| 1b modules (Py) | `scripts/02_wgcna_modules.py` | coexpr | `stage1_gene_modules.csv`, `ME` |
| 1b mouse check | (§3.3) | both | `mouse_correspondence.csv`, `mouse_preservation.csv` |
| 2 preservation | `scripts/04_bgee_preservation_sweep.py` | coexpr | `allsp_preservation_expanded.csv`, `stage2_module_conservation.csv` |
| A phylo signal | `scripts/05_phaseA_phylo_signal.R` | wgcna-r | `phaseA_phylo_signal.csv` |
| B GRN methods | `scripts/06_*`, `07_grn_clr.py` | coexpr | `genie3_edges`, `grnboost2_edges`, `clr_edges` |
| B ensemble | `scripts/08_grn_ensemble.py` | coexpr | `phaseB_GRN_ensemble.parquet` |
| B cocktails | `scripts/09_grn_cocktails.py` | coexpr | `phaseB_cocktail_*.csv` |
| B annotation | `scripts/10_module_functional_annotation.py` | coexpr | `module_functional_annotation.csv`, `module_enrichment_full.csv` |
| B regulon synth | `scripts/11_regulon_conservation.py` | coexpr | `regulon_subnetwork_preservation.csv`, `regulon_family_composition.csv` |
| B validation | `scripts/12_grn_validation_dorothea.py` | coexpr | `grn_validation_benchmark.csv`, `grn_validation_per_TF.csv` |
| SC Tier-4 | `pyscenic_tier4/pyscenic_tier4.py` | pyscenic | `pyscenic_tier4/out/*` |

---

## 9. Runtime & RAM (14-core / 36 GB reference; scales with cores)

| Step | Wall-time (order) | Peak RAM |
|---|---|---|
| Stage 1 normalize | minutes | < 8 GB |
| WGCNA (R or Python), 14k genes | ~10–30 min | ~10–16 GB (14k×14k TOM) |
| Stage 2 sweep (26 species) | several hours (network-bound) | ~2 GB/species |
| Phase A phylo | minutes | < 2 GB |
| GRN GENIE3 / GRNBoost2 | tens of min each (14 threads) | ~8–16 GB |
| CLR + ensemble | minutes | < 8 GB |
| Cocktails (SHAP) | tens of min | < 8 GB |
| SC Tier-4 pySCENIC | 6–20 h (see §7) | ≤ 33 GB (11 × 3 GB) |

---

## 10. Troubleshooting

- **Build / solve issues, arch gaps:** see `BUILD_NOTES.md §4`.
- **`dtc_patched.py` not found** (Python WGCNA route only):
  `cp scripts/lib_dynamicTreeCut_patched.py scripts/dtc_patched.py`
  (`BUILD_NOTES.md §5`).
- **Script hard-coded paths.** Several scripts read/write under `/tmp/gtex`
  (the original run's scratch). Either symlink your workdir there inside the
  container shell (`docker compose run --rm gn shell coexpr`) or edit the `G=`
  path at the top of the script to point at the mounted repo.
- **Out-of-memory / killed container.** Lower thread count (`n_jobs` in the GRN
  scripts) or raise Docker's memory cap. The 14k×14k TOM in WGCNA is the single
  largest allocation.
- **Bgee/recount3/g:Profiler network errors.** These are live external services;
  retry, and confirm outbound HTTPS is allowed from the Docker VM.

---

## 11. Provenance

- Container definition + this SOP: `container/`. Package pins verified against
  linux-64 (see `BUILD_NOTES.md §1`).
- Canonical WGCNA is **bioconda r-wgcna 1.74** (R 4.5). The original analysis
  used a pure-Python WGCNA reimplementation only because that build is
  unavailable on osx-arm64; the R route added here removes that limitation and
  lets the two implementations be compared directly.
- Method decisions and honest limitations (β=8 at the R² elbow, CLR substituted
  for ARACNE/PIDC, deferred genome-scale steps): `FINDINGS.md` and
  `FUTURE_DIRECTIONS.md`.
