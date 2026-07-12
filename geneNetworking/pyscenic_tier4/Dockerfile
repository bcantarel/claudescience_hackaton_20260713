# SC-Tier 4 pySCENIC — no conda, runs the pipeline in a container.
# Base: slim Python; pySCENIC + arboreto + dask are pure-Python/CPU (no GPU).
FROM python:3.10-slim

# system libs some wheels expect (hdf5 for h5py/anndata, build tools for a few sdists)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libhdf5-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Pinned, mutually-compatible stack. pyscenic 0.12.1 still uses np.object internally,
# which was REMOVED in numpy 1.24 -> numpy MUST be <1.24. 1.23.5 is the last 1.23 and
# is compatible with numba 0.56/0.57, pandas 1.5, and scipy 1.10. Everything else is
# pinned to versions that resolve against numpy 1.23.
RUN pip install --no-cache-dir \
        "numpy==1.23.5" \
        "pandas==1.5.3" \
        "scipy==1.10.1" \
        "numba==0.57.1" \
        "pyscenic==0.12.1" \
        "ctxcore==0.2.0" \
        "arboreto==0.1.6" \
        "dask==2023.5.0" "distributed==2023.5.0" \
        "anndata==0.9.2" \
        "scanpy==1.9.8" \
        "pyarrow>=11"

WORKDIR /work
# the script + support/ are mounted at runtime (see docker-compose / run command),
# so the image stays generic and you can edit the script without rebuilding.
ENTRYPOINT ["python", "/work/pyscenic_tier4.py"]
CMD ["--help"]
