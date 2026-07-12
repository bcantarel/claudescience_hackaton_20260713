# SC-Tier 4 — full pySCENIC on your Mac (no GPU)

Motif-pruned, bootstrap-stabilized regulons for the shared cell types across
human/mouse/lemur — the Tier-4 upgrade over the co-expression regulons used in
SC1.3/SC2.1. Runs natively on macOS (14 cores / 36 GB); **no GPU needed** —
GRNBoost2 is CPU-parallel via dask.

## No conda — runs in Docker
The whole stack (pySCENIC + arboreto + dask, all CPU) is pinned in the `Dockerfile`.
No conda, no local Python deps. You only need Docker Desktop.

**One-time:** Docker Desktop → Settings → Resources → **Memory ≥ 32 GB** (the pipeline
uses most of the Mac's RAM). Then build the image once:
```bash
cd pyscenic_tier4
docker compose build            # ~5 min, one time
```

**Run it** (two steps — download, then run). The current folder is mounted into the
container, so `data/`, `cistarget_db/`, and `out/` all land on your Mac and persist:
```bash
# 1. fetch data + cisTarget DBs (~9.5 GB h5ad + ~2 GB feather) into ./data, ./cistarget_db
docker compose run --rm pyscenic download

# 2. run (default 10 bootstraps, 2000-cell cap, Tier-1 cell types first)
docker compose run --rm pyscenic run --bootstrap 10 --max-cells 2000 --n-workers 11
```
`--n-workers 11` leaves cores free; the container's `mem_limit` (32 GB in
`docker-compose.yml`) is the hard ceiling. To run in the background and keep the
log, add `-d` is not available with `run` — instead use:
```bash
nohup docker compose run --rm pyscenic run --bootstrap 10 --max-cells 2000 --n-workers 11 > tier4.log 2>&1 &
```
then `tail -f tier4.log`.

*(No Docker either? The script is plain Python — `pip install pyscenic anndata scanpy
pyarrow "dask[distributed]"` into any Python 3.10 venv and run it directly. Docker just
saves you the dependency-pinning fight.)*

## Time budget (<24 h window)
Working average ~5 min per GRNBoost2 run (2,000-cell cap, 11 workers).

| Command | Units | Est. wall-time | Note |
|---|---|---|---|
| `--tier 1 --bootstrap 10` | 4 ct × 3 sp | **~6–8 h** | headline cell types, all species — **safest complete result** |
| `--tier 1 --species human mouse --bootstrap 10` | 4 ct × 2 sp | ~4–5 h | fastest meaningful result |
| `--bootstrap 10` (default, tier 2) | 10 ct × 3 sp | ~15–20 h | everything, Tier-1 first |
| `--bootstrap 20` | 10 ct × 3 sp | ~30+ h | **won't finish in 24 h — don't** |

**Recommendation for <24 h:** launch `--bootstrap 10` (default). It runs Tier-1
cell types first and **checkpoints after every (cell type, species)** — if the
clock runs out, everything finished so far is complete and usable, and Tier 1
(your headline claims) is done in the first ~6–8 h. 10 bootstrap runs is a
sound stability filter; 20 buys a marginally tighter recurrence estimate for
double the time and is not worth it here.

## Safety / robustness
- `--mem-limit 3GB` per worker → 11 workers ≈ 33 GB ceiling, leaves headroom on 36 GB.
- Per-cell-type processing never loads a whole atlas into RAM.
- Re-running resumes: finished (cell type, species) units in `out/tier4_summary.csv` are skipped.

## Outputs (`out/`)
- `<ct>_<sp>_adjacencies.tsv` — consensus GRNBoost2 TF→target edges (recur ≥70% of bootstraps)
- `<ct>_<sp>_stability.csv` — per-edge recurrence frequency (the stability metric)
- `<ct>_<sp>_regulons.gmt` — cisTarget motif-pruned regulons
- `aucell_<ct>_<sp>.csv` — per-cell regulon activity
- `tier4_summary.csv` — n_regulons / n_stable_edges / runtime per unit

## Design notes
- All species relabeled to a common **human-symbol** ortholog space (14,073 1:1
  triples) so GRNBoost2 output and the hg38 cisTarget DB share one gene index —
  exactly the SC2.1/SC2.2 analysis space. Lemur has no cisTarget DB, so lemur
  regulons are motif-pruned against hg38 via 1:1 orthology (stated bias, same as SC2.3).
- An mm10-native mouse variant (more correct mouse motifs, more moving parts) is
  documented in the `NOTE` at the bottom of `pyscenic_tier4.py`.
- Data-loading path validated against the real h5ad files before shipping
  (plasma cell/spleen: 2000×14072 human, 802×12908 mouse, 1089×14072 lemur; XBP1 present).
