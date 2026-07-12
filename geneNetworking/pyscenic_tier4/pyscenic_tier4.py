#!/usr/bin/env python3
"""
SC-Tier 4 — full pySCENIC (GRNBoost2 -> cisTarget motif pruning -> AUCell) with
bootstrap stability, for the shared cell types across human/mouse/lemur.

Runs NATIVELY on your Mac (not the sandbox) so dask can spawn workers.
No GPU required — GRNBoost2 is CPU-parallel across your cores.

DESIGN (chosen for a <24 h window):
  * Cell types are TIERED. Tier 1 (headline claims) runs first; if you run out of
    time you still have a complete, usable result for the cell types that matter.
  * All species are relabeled to a common HUMAN-SYMBOL ortholog space (14,073 1:1
    triples) so GRNBoost2 output and the hg38 cisTarget DB share one gene index.
    This matches the SC2.1/SC2.2 analysis space exactly. (mm10-native mouse is a
    documented alternative — see NOTE at bottom — but the common-space design is
    simpler, reproducible, and what the report's conservation claims are built on.)
  * CHECKPOINTED after every (cell type, species): a crash at hour 6 loses nothing
    before it. Re-running skips finished units.
  * Memory-capped LocalCluster so a runaway run cannot OOM a 36 GB machine.

USAGE (on your Mac):
  # 0. one-time env (native conda, NOT the sandbox 'sc' env):
  #    conda create -n pyscenic python=3.10 -y && conda activate pyscenic
  #    pip install pyscenic anndata scanpy pyarrow "dask[distributed]"
  # 1. fetch data + cisTarget DBs (~9.5 GB h5ad + ~2 GB feather):
  python pyscenic_tier4.py download
  # 2. run (default 10 bootstrap runs, 2000-cell cap, Tier-1 cell types first):
  python pyscenic_tier4.py run --bootstrap 10 --max-cells 2000 --n-workers 11
  # options: --species human mouse   --tier 1   (Tier 1 only, fastest safe result)

OUTPUTS (per cell type x species, under ./out/):
  <ct>_<sp>_adjacencies.tsv        raw GRNBoost2 TF-target importances (consensus)
  <ct>_<sp>_regulons.gmt           motif-pruned regulons (cisTarget)
  <ct>_<sp>_stability.csv          per-edge recurrence frequency across bootstraps
  aucell_<ct>_<sp>.csv             AUCell regulon activity per cell
  tier4_summary.csv                per-unit: n_regulons, n_stable_edges, runtime
"""
import argparse, json, os, sys, time, glob, urllib.request
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
SUP  = HERE / "support"
DATA = HERE / "data"          # h5ad files land here
DB   = HERE / "cistarget_db"  # feather + motif tbl land here
OUT  = HERE / "out"
for d in (DATA, DB, OUT): d.mkdir(exist_ok=True)

# ---- cell-type tiers (Tier 1 = headline claims: run first) --------------------
TIER1 = ["plasma cell", "hepatocyte", "monocyte", "T cell"]
TIER2 = ["B cell", "NK cell", "macrophage", "endothelial cell", "fibroblast", "pneumocyte"]
# best-powered tissue per cell type (from the shared-cell-type survey)
CT_TISSUE = {"hepatocyte":"liver","plasma cell":"spleen","B cell":"spleen","NK cell":"lung",
             "T cell":"lung","macrophage":"lung","monocyte":"lung","endothelial cell":"lung",
             "fibroblast":"lung","pneumocyte":"lung"}

# ============================ DOWNLOAD ========================================
def cmd_download(args):
    man = json.load(open(HERE / "download_manifest.json"))
    def fetch(url, dst, label):
        if dst.exists() and dst.stat().st_size > 1e6:
            print(f"  [skip] {label} exists"); return
        print(f"  downloading {label} ...", flush=True); t=time.time()
        urllib.request.urlretrieve(url, dst)
        print(f"    {dst.stat().st_size/1e6:.0f} MB in {time.time()-t:.0f}s")
    print("h5ad matrices ->", DATA)
    for name, url in man["h5ad"].items(): fetch(url, DATA/name, name)
    print("cisTarget databases ->", DB)
    for name, url in man["cistarget"].items():
        fetch(url, DB/os.path.basename(url), name)
    print("done.")

# ============================ HELPERS =========================================
def load_common_space():
    orth = pd.read_csv(SUP/"ortholog_triples_usable.csv")
    key = {"human":dict(zip(orth.human,orth.human)),
           "mouse":dict(zip(orth.mouse,orth.human)),
           "lemur":dict(zip(orth.lemur,orth.human))}
    e2s = json.load(open(SUP/"ens2sym.json"))              # human-ens -> symbol
    hmap = pd.read_csv(SUP/"celltype_harmonization_map.csv")
    cl2broad = dict(zip(hmap.cl.astype(str), hmap.broad))
    tfs = set(open(SUP/"tfs_human_symbols.txt").read().split())
    return key, e2s, cl2broad, tfs

def celltype_matrix(tissue, species, cell_type, key, e2s, cl2broad, max_cells, seed=0):
    """Return cells x human-SYMBOL expression DataFrame for one cell type."""
    import anndata as ad
    from scipy import sparse
    f = DATA / f"{tissue}_{species}.h5ad"
    if not f.exists(): return None
    a = ad.read_h5ad(f)
    cl = a.obs["cell_type_ontology_term_id"].astype(str).map(cl2broad).fillna("other")
    mask = (cl == cell_type).values
    if mask.sum() < 50: return None
    X = a.raw.X if a.raw is not None else a.X
    genes = np.array((a.raw.var.index if a.raw is not None else a.var.index)).astype(str)
    km = key[species]
    keep = np.array([g in km for g in genes])
    Xc = X[mask][:, keep]
    hsym = [e2s.get(km[g]) for g in genes[keep]]            # -> human symbol
    del a
    Xc = Xc.toarray() if sparse.issparse(Xc) else np.asarray(Xc)
    lib = Xc.sum(1, keepdims=True); lib[lib==0]=1
    df = pd.DataFrame(np.log1p(Xc/lib*1e4), columns=hsym)
    df = df.loc[:, [c for c in df.columns if c]]            # drop unmapped
    df = df.T.groupby(level=0).mean().T                     # collapse dup symbols
    if len(df) > max_cells:
        df = df.sample(max_cells, random_state=seed)
    return df

# ============================ RUN =============================================
def cmd_run(args):
    from arboreto.algo import grnboost2
    from distributed import Client, LocalCluster
    from ctxcore.rnkdb import FeatherRankingDatabase
    from pyscenic.prune import prune2df, df2regulons
    from pyscenic.utils import modules_from_adjacencies
    from pyscenic.aucell import aucell

    key, e2s, cl2broad, tf_syms = load_common_space()
    tf_list = sorted(tf_syms)

    # cisTarget DB (hg38 common space for all species)
    rnk = sorted(glob.glob(str(DB/"hg38*rankings.feather")))
    if not rnk: sys.exit("cisTarget hg38 ranking DB missing — run `download` first.")
    dbs = [FeatherRankingDatabase(fname=rnk[0], name=Path(rnk[0]).stem)]
    motif_tbl = str(next(DB.glob("*hgnc*.tbl")))

    cts = (TIER1 if args.tier == 1 else TIER1 + TIER2)
    summary_path = OUT/"tier4_summary.csv"
    done = set()
    if summary_path.exists():
        done = set(tuple(r) for r in pd.read_csv(summary_path)[["cell_type","species"]].values)

    cluster = LocalCluster(n_workers=args.n_workers, threads_per_worker=1,
                           memory_limit=args.mem_limit, dashboard_address=None)
    client = Client(cluster)
    print(f"dask: {args.n_workers} workers @ {args.mem_limit} | TFs={len(tf_list)} | "
          f"cell types={cts} | species={args.species} | bootstrap={args.bootstrap}")

    rows = []
    for ct in cts:
        tissue = CT_TISSUE[ct]
        for sp in args.species:
            if (ct, sp) in done:
                print(f"[skip] {ct}/{sp} already done"); continue
            t0 = time.time()
            expr = celltype_matrix(tissue, sp, ct, key, e2s, cl2broad, args.max_cells)
            if expr is None or expr.shape[0] < 50:
                print(f"[skip] {ct}/{sp}: too few cells"); continue
            tfs_present = [t for t in tf_list if t in expr.columns]
            # ---- bootstrap GRNBoost2 -> consensus + per-edge recurrence ----
            edge_counts, imp_sum = {}, {}
            for b in range(args.bootstrap):
                sub = expr.sample(frac=0.8, random_state=b) if args.bootstrap > 1 else expr
                adj = grnboost2(sub, tf_names=tfs_present, client_or_address=client,
                                seed=b, verbose=False)
                topk = adj.sort_values("importance", ascending=False).head(len(tfs_present)*50)
                for tf_, tgt, imp in topk[["TF","target","importance"]].itertuples(index=False):
                    edge_counts[(tf_,tgt)] = edge_counts.get((tf_,tgt),0)+1
                    imp_sum[(tf_,tgt)] = imp_sum.get((tf_,tgt),0.0)+imp
                print(f"    {ct}/{sp} boot {b+1}/{args.bootstrap} ({time.time()-t0:.0f}s)", flush=True)
            stab = pd.DataFrame(
                [(tf_,tgt,c/args.bootstrap, imp_sum[(tf_,tgt)]/c)
                 for (tf_,tgt),c in edge_counts.items()],
                columns=["TF","target","recurrence","mean_importance"])
            stab.to_csv(OUT/f"{ct.replace(' ','_')}_{sp}_stability.csv", index=False)
            # consensus adjacency = edges recurring in >= ceil(0.7*B)
            thr = max(1, int(np.ceil(0.7*args.bootstrap)))
            cons = stab[stab.recurrence*args.bootstrap >= thr][["TF","target","mean_importance"]]
            cons = cons.rename(columns={"mean_importance":"importance"})
            cons.to_csv(OUT/f"{ct.replace(' ','_')}_{sp}_adjacencies.tsv", sep="\t", index=False)
            # ---- cisTarget motif pruning ----
            n_reg = 0; n_stable = len(cons)
            try:
                mods = list(modules_from_adjacencies(cons, expr))
                pruned = prune2df(dbs, mods, motif_tbl, client_or_address=client)
                regs = df2regulons(pruned)
                n_reg = len(regs)
                with open(OUT/f"{ct.replace(' ','_')}_{sp}_regulons.gmt","w") as fh:
                    for r in regs:
                        fh.write(f"{r.name}\t{ct}/{sp}\t"+"\t".join(r.gene2weight)+"\n")
                # ---- AUCell ----
                auc = aucell(expr, regs, num_workers=args.n_workers)
                auc.to_csv(OUT/f"aucell_{ct.replace(' ','_')}_{sp}.csv")
            except Exception as e:
                print(f"    [warn] pruning/AUCell {ct}/{sp}: {e}")
            dt = time.time()-t0
            rows.append(dict(cell_type=ct, species=sp, n_cells=expr.shape[0],
                             n_tfs=len(tfs_present), n_stable_edges=n_stable,
                             n_regulons=n_reg, runtime_s=round(dt)))
            pd.DataFrame(rows if not summary_path.exists() else
                         pd.concat([pd.read_csv(summary_path), pd.DataFrame([rows[-1]])]).to_dict("records")
                        ).to_csv(summary_path, index=False)
            print(f"[done] {ct}/{sp}: {n_reg} regulons, {n_stable} stable edges, {dt:.0f}s")
    client.close(); cluster.close()
    print("ALL DONE ->", OUT)

# NOTE (mm10-native alternative): to use the mouse-specific cisTarget DB, keep mouse
# matrices in ENSMUSG->MGI-symbol space (skip the ortholog relabel for species=mouse),
# load the mm10 ranking feather + mgi motif tbl for mouse units, and map regulons back
# to human symbols post hoc for the cross-species comparison. More correct for mouse
# motifs; more moving parts. The common-space default above is what the report uses.

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download")
    r = sub.add_parser("run")
    r.add_argument("--bootstrap", type=int, default=10)
    r.add_argument("--max-cells", type=int, default=2000)
    r.add_argument("--n-workers", type=int, default=11)
    r.add_argument("--mem-limit", default="3GB")
    r.add_argument("--species", nargs="+", default=["human","mouse","lemur"])
    r.add_argument("--tier", type=int, default=2, choices=[1,2],
                   help="1 = Tier-1 headline cell types only; 2 = all (Tier 1 first)")
    a = p.parse_args()
    {"download": cmd_download, "run": cmd_run}[a.cmd](a)
