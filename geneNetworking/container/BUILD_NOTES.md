# Build notes — geneNetworking container

Static-validation record for the container definition. The image could **not**
be built or run where it was authored (no Docker daemon in that sandbox), so
this file separates *what was verified statically* from *what must be confirmed
on the first real build*, and gives the exact build + smoke-test commands.

---

## 1. What was verified statically (no Docker needed)

**Package resolution** — every pinned dependency in the three env specs was
re-resolved against the live anaconda.org / PyPI APIs on the target platform:

- **24 / 24 conda pins** resolve on `linux-64` (or `noarch`), channel order
  `conda-forge` then `bioconda`:
  - `coexpr`: python 3.11, numpy 2.1, pandas 2.2, scipy 1.14, scikit-learn 1.5,
    lightgbm 4.6, py-xgboost 2.0.3, shap 0.46, pyarrow 17, joblib 1.4,
    requests 2.32, matplotlib-base 3.9, seaborn 0.13, networkx 3.3.
  - `wgcna-r`: r-base 4.5, **bioconda r-wgcna 1.74**, r-dynamictreecut 1.63,
    r-fastcluster 1.3, r-ape 5.8, r-phytools 1.2, r-nlme 3.1, r-data.table,
    r-optparse.
  - `pyscenic`: python 3.10, numpy 1.23.5, pandas 1.5.3, scipy 1.10.1,
    numba 0.57.1.
- **8 / 8 PyPI pins** exist: dynamicTreeCut 0.1.1 (coexpr); pyscenic 0.12.1,
  ctxcore 0.2.0, arboreto 0.1.6, dask/distributed 2023.5.0, anndata 0.9.2,
  scanpy 1.9.8 (pyscenic).

**Key resolution facts that shaped the pins**

- `r-wgcna 1.74`'s newest bioconda build is compiled against **R 4.5** and
  declares its own Bioconductor deps (`GO.db 3.22`, `AnnotationDbi 1.72`,
  `impute 1.84`, `preprocessCore 1.72`). The spec therefore pins `r-base=4.5`
  and lets WGCNA pull those Bioconductor packages itself. Pinning R 4.3 or
  hand-pinning older Bioconductor versions is what makes the solve fail.
- `xgboost` on `linux-64` tops out at **2.0.3** on conda-forge (3.x is
  `noarch`-only there); pinned to `2.0.3` to keep a real linux-64 build.
- The `coexpr` (numpy 2.x) and `pyscenic` (numpy 1.23.5) worlds are
  **mutually incompatible** and are deliberately separate conda envs in one
  image, never a shared Python.

**Definition correctness**

- Dockerfile build context = repo root; **all 10 `COPY` sources exist**
  (`scripts/`, `container/R/`, `container/tools/`, `container/entrypoint.sh`,
  `data/`, `pyscenic_tier4/pyscenic_tier4.py`, `pyscenic_tier4/support/`, the
  three env YAMLs).
- `entrypoint.sh` passes `bash -n`; subcommand dispatch + help extraction
  exercised.
- `R/01_wgcna_modules.R` passes R `parse()` cleanly.
- `tools/pkl_to_tsv.py` passes `ast.parse`.
- `.dockerignore` keeps the heavy artefacts (*.pptx, *.pdf, *.h5ad, *.feather,
  *.parquet, *.pkl, results/, figures/) out of the build context.

---

## 2. Must be confirmed on the first real build

Static API checks prove each package/version **exists** for the platform; they
do **not** prove the full dependency graph co-solves. Confirm on first build:

1. **Full environment solves.** The `micromamba create` for `wgcna-r` is the
   one to watch — R + Bioconductor + WGCNA is the deepest graph. If it stalls,
   see §4.
2. **WGCNA loads and runs**, not just installs (it compiles Rcpp/C++
   internals): `library(WGCNA)` + a tiny `adjacency()` call.
3. **pyscenic import** under numpy 1.23.5 (the `np.object` constraint that
   forces the pin).
4. **Architecture.** Pins were resolved for **linux-64**. On an Apple-Silicon
   Mac, Docker builds `linux/arm64` by default — `r-wgcna` has a
   `linux-aarch64` bioconda build, but not every pinned dep necessarily does.
   Build for a known-good arch explicitly:
   `docker build --platform=linux/amd64 ...` (runs under emulation on M-series;
   slower but matches the resolved pin set). See §4.

---

## 3. Build + smoke-test commands

```bash
# from the repo root (build context = repo root)
docker build --platform=linux/amd64 -t genenetworking:latest -f container/Dockerfile .

# --- smoke tests (each should print a version / OK) ---
# list the three envs
docker run --rm genenetworking:latest envs

# canonical R WGCNA is importable and is the real package
docker run --rm genenetworking:latest wgcna-r Rscript -e 'library(WGCNA); cat("WGCNA", as.character(packageVersion("WGCNA")), "\n")'

# main Python stack
docker run --rm genenetworking:latest coexpr python -c "import numpy,pandas,sklearn,lightgbm,xgboost,shap,pyarrow,dynamicTreeCut; print('coexpr OK', numpy.__version__)"

# phylogenetics (Phase A)
docker run --rm genenetworking:latest wgcna-r Rscript -e 'library(phytools); cat("phytools OK\n")'

# single-cell pySCENIC (numpy<1.24 world)
docker run --rm genenetworking:latest pyscenic python -c "import pyscenic,numpy; print('pyscenic OK', numpy.__version__)"

# end-to-end R WGCNA driver help
docker run --rm genenetworking:latest wgcna --help
```

Via compose (from `container/`): replace `docker run --rm genenetworking:latest`
with `docker compose run --rm gn`.

---

## 4. Troubleshooting the build

- **Slow / stuck conda solve.** micromamba's solver is fast, but the R graph is
  large. If it churns, the usual cause is channel priority — the specs already
  order `conda-forge` above `bioconda`, which is required (r-wgcna is bioconda,
  its R deps are conda-forge).
- **arm64 gap.** If a dep is missing on `linux-aarch64`, build
  `--platform=linux/amd64` (emulated on M-series Macs). All pins were resolved
  against `linux-64`, so amd64 is the reference target.
- **hdf5 / anndata errors in pyscenic.** `libhdf5-dev` is installed at the
  system layer; if a wheel still fails, it is a numpy-version clash — keep numpy
  at exactly 1.23.5.

---

## 5. Pre-existing repo detail (not introduced here)

`scripts/02_wgcna_modules.py` loads its patched dynamicTreeCut via
`spec_from_file_location("dtc", "dtc_patched.py")`, but the file committed to
the repo is `scripts/lib_dynamicTreeCut_patched.py`. If you run the **Python**
WGCNA route (rather than the canonical R driver added here), symlink or copy it
first:

```bash
cp scripts/lib_dynamicTreeCut_patched.py scripts/dtc_patched.py
```

The canonical R route (`R/01_wgcna_modules.R`) is unaffected — it does not use
the Python patch.
