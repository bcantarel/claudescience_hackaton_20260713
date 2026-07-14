# =============================================================================
# geneNetworking — reproducible analysis container
# Conserved gene co-expression networks & TF regulatory logic across vertebrates
# =============================================================================
# One image, three isolated conda environments (their dependency worlds are
# mutually incompatible, so they must NOT share a Python):
#
#   coexpr    Python 3.11 / numpy 2.x  -> Stages 1-2 + Phase B GRN pipeline
#   wgcna-r   R 4.5 + canonical WGCNA  -> original R WGCNA + Phase A phylo signal
#   pyscenic  Python 3.10 / numpy 1.23 -> single-cell Tier-4 pySCENIC
#
# The wgcna-r env is the whole point of containerizing: bioconda ships no
# osx-arm64 build of r-wgcna, so the original analysis reimplemented WGCNA in
# Python. On linux-64 the canonical Bioconductor/CRAN WGCNA installs cleanly.
#
# Build:  docker build -t genenetworking:latest -f container/Dockerfile .
#   (build context = repo root, so scripts/, data/, pyscenic_tier4/ are copied)
# =============================================================================

FROM mambaorg/micromamba:1.5.8

# --- root for system packages, then drop back to the mamba user ------------
USER root

# System libraries: build tools + hdf5 (h5py/anndata in pyscenic env),
# curl/git for data fetches, and libs some R/py wheels link against.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        ca-certificates \
        libhdf5-dev \
        libxml2-dev \
        libcurl4-openssl-dev \
        libssl-dev \
        procps \
    && rm -rf /var/lib/apt/lists/*

# micromamba's default unprivileged user; envs live under /opt/conda
USER $MAMBA_USER
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- create the three environments from the pinned specs -------------------
# Copied one at a time so a change to one spec doesn't bust the cache of the
# earlier layers. Each solve is heavy; ordering cheap->heavy is intentional.
COPY --chown=$MAMBA_USER:$MAMBA_USER container/envs/coexpr.yml   /tmp/coexpr.yml
RUN micromamba create -y -f /tmp/coexpr.yml   && micromamba clean --all --yes

COPY --chown=$MAMBA_USER:$MAMBA_USER container/envs/wgcna-r.yml  /tmp/wgcna-r.yml
RUN micromamba create -y -f /tmp/wgcna-r.yml  && micromamba clean --all --yes

COPY --chown=$MAMBA_USER:$MAMBA_USER container/envs/pyscenic.yml /tmp/pyscenic.yml
RUN micromamba create -y -f /tmp/pyscenic.yml && micromamba clean --all --yes

# --- copy the analysis code into the image ---------------------------------
# Data (recount3/Bgee/h5ad/cisTarget) is NOT baked in — it is mounted at
# runtime via docker-compose so the multi-GB downloads persist on the host.
WORKDIR /opt/geneNetworking
COPY --chown=$MAMBA_USER:$MAMBA_USER scripts/                 ./scripts/
COPY --chown=$MAMBA_USER:$MAMBA_USER container/R/             ./R/
COPY --chown=$MAMBA_USER:$MAMBA_USER container/tools/         ./tools/
COPY --chown=$MAMBA_USER:$MAMBA_USER container/entrypoint.sh  /usr/local/bin/entrypoint.sh
COPY --chown=$MAMBA_USER:$MAMBA_USER data/                    ./data/
# pyscenic driver + support tables (small); h5ad/feather stay on host mount
COPY --chown=$MAMBA_USER:$MAMBA_USER pyscenic_tier4/pyscenic_tier4.py ./pyscenic_tier4/pyscenic_tier4.py
COPY --chown=$MAMBA_USER:$MAMBA_USER pyscenic_tier4/support/          ./pyscenic_tier4/support/

USER root
RUN chmod +x /usr/local/bin/entrypoint.sh
USER $MAMBA_USER

# entrypoint dispatches into the right env by subcommand (see entrypoint.sh)
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["help"]
