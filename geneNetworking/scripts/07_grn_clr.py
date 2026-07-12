#!/usr/bin/env python3
"""
B2 third GRN method -- CLR (Context Likelihood of Relatedness, Faith et al. 2007).

NOTE: the integrated plan named ARACNE or PIDC; CLR was substituted as the
information-theoretic complement (single vectorized MI z-score pass, no per-triplet
DPI loop) for tractability in the local sandbox. All three MI methods differ only
in how they prune indirect edges; the rank-product ensemble is robust to the choice.

Computes binned mutual information (10 equal-frequency bins) between every TF and
target, then the CLR statistic sqrt(z_tf^2 + z_tg^2) from background-corrected MI.
Keeps the top-30 regulators per target so the edge structure matches GENIE3 /
GRNBoost2 for rank-product ensembling (see 08_grn_ensemble step in README section 3).

Inputs (workspace):
  wgcna_input.pkl            genes x samples, log2 CPM (from 01_normalize_matrix.py)
  phaseB_gene_TF_module.csv  columns: ensembl_gene, module, is_TF, symbol
Output:
  clr_edges.parquet          columns: TF, target, clr_score  (211,020 edges)
"""
import numpy as np, pandas as pd, pickle

NBINS, TOPK = 10, 30

def discretize(a, nbins=NBINS):
    """Equal-frequency (rank) binning -- robust to skewed logCPM. a: samples x genes."""
    r = pd.DataFrame(a).rank(method="first").values
    return np.floor((r - 1) / len(a) * nbins).astype(np.int8).clip(0, nbins - 1)

def entropy(D):
    n = D.shape[0]
    out = np.zeros(D.shape[1])
    for j in range(D.shape[1]):
        c = np.bincount(D[:, j], minlength=NBINS) / n
        c = c[c > 0]
        out[j] = -(c * np.log(c)).sum()
    return out

def mutual_information(Dtf, Dtg):
    """MI between every TF (cols of Dtf) and every target (cols of Dtg)."""
    n, nTF, nTG = Dtf.shape[0], Dtf.shape[1], Dtg.shape[1]
    MI = np.zeros((nTF, nTG), dtype=np.float32)
    for i in range(nTF):
        tfcol = Dtf[:, i]
        joint = np.zeros((NBINS, NBINS, nTG), dtype=np.float32)
        for b in range(NBINS):
            mask = tfcol == b
            if not mask.any():
                continue
            sub = Dtg[mask]
            for tb in range(NBINS):
                joint[b, tb] = (sub == tb).sum(0)
        joint /= n
        ptf = joint.sum(1)          # NBINS x nTG
        ptg = joint.sum(0)          # NBINS x nTG
        with np.errstate(divide="ignore", invalid="ignore"):
            denom = ptf[:, None, :] * ptg[None, :, :]
            ratio = np.where((joint > 0) & (denom > 0), joint / denom, 1.0)
            MI[i] = np.where(joint > 0, joint * np.log(ratio), 0.0).sum((0, 1))
    return MI

def clr_statistic(MI):
    """CLR (Faith 2007): combine z-scores of MI vs each node's own MI background."""
    z_tf = np.clip((MI - MI.mean(1, keepdims=True)) / (MI.std(1, keepdims=True) + 1e-9), 0, None)
    z_tg = np.clip((MI - MI.mean(0, keepdims=True)) / (MI.std(0, keepdims=True) + 1e-9), 0, None)
    return np.sqrt(z_tf**2 + z_tg**2)

def main():
    wg = pickle.load(open("wgcna_input.pkl", "rb"))       # genes x samples
    gm = pd.read_csv("phaseB_gene_TF_module.csv")
    tf_ids  = gm[gm.is_TF].ensembl_gene.tolist()
    targets = gm[gm.module != "grey"].ensembl_gene.tolist()
    X = wg.T                                               # samples x genes
    Dtf = discretize(X[tf_ids].values)
    Dtg = discretize(X[targets].values)
    MI  = mutual_information(Dtf, Dtg)
    CLR = clr_statistic(MI)

    tf_arr, tg_arr, tf_set = np.array(tf_ids), np.array(targets), set(tf_ids)
    rows = []
    for j, tg in enumerate(tg_arr):
        col = CLR[:, j].copy()
        if tg in tf_set:                                   # exclude self-edge
            si = np.where(tf_arr == tg)[0]
            if len(si):
                col[si[0]] = -1
        idx = np.argsort(col)[::-1][:TOPK]
        rows += [(tf_arr[i], tg, float(col[i])) for i in idx if col[i] > 0]
    pd.DataFrame(rows, columns=["TF", "target", "clr_score"]).to_parquet("clr_edges.parquet")

if __name__ == "__main__":
    main()
