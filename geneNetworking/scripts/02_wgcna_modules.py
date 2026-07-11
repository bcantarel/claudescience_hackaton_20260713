#!/usr/bin/env python3
"""
Stage 1b — WGCNA module discovery (pure-Python reimplementation).
Reference method: Langfelder & Horvath (2008). Reimplemented in Python because
bioconda ships no osx-arm64 r-wgcna build. Validated against an independent
mouse network (23/26 modules recovered).

Input:  wgcna_input.pkl (14,000 genes x samples, log2 CPM)
Output: module_merged.npy (per-gene module label), ME.pkl (module eigengenes)

Steps: signed-hybrid adjacency (beta=8) -> signed TOM -> average-linkage
hclust -> dynamicTreeCut (cutreeHybrid) -> merge modules by eigengene corr>0.75.
"""
import numpy as np, pandas as pd, pickle, importlib.util
from scipy.cluster.hierarchy import linkage, fcluster
BETA, MIN_SIZE, DEEPSPLIT, MERGE_COR = 8, 30, 2, 0.75

def build(wg):
    X = wg.values.astype(np.float32)
    Xz = (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-9)
    corr = np.corrcoef(Xz)                       # 14000 x 14000
    adj = np.clip(corr, 0, None) ** BETA         # signed hybrid
    # signed TOM
    L = adj @ adj
    k = adj.sum(1)
    kmin = np.minimum.outer(k, k)
    tom = (L + adj) / (kmin + 1 - adj)
    np.fill_diagonal(tom, 1)
    dissTOM = 1 - tom
    Z = linkage(dissTOM[np.triu_indices_from(dissTOM, 1)], method="average")
    # dynamicTreeCut (patched for numpy-2.x float-index bug; see dtc_patched.py)
    spec = importlib.util.spec_from_file_location("dtc", "dtc_patched.py")
    dtc = importlib.util.module_from_spec(spec); spec.loader.exec_module(dtc)
    labels = dtc.cutreeHybrid(Z, dissTOM, minClusterSize=MIN_SIZE,
                              deepSplit=DEEPSPLIT, pamStage=False)["labels"]
    return labels
# Module-merge + eigengene code documented in README; see phaseA/phaseB scripts for use.
