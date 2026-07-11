#!/usr/bin/env python3
"""
Stage 1a — GTEx expression matrix assembly & normalization (recount3).
Input:  per-tissue recount3 gene_sums files (G026), GTEx sample metadata.
Output: wgcna_input.pkl (14,000 genes x N samples, log2 CPM), sample_meta.csv.

Recipe (identical recipe reused for mouse & every Bgee species):
  1. Subsample MAX_PER_TISSUE=120 samples/tissue (rng seed 0) to balance tissues.
  2. Assemble raw base-coverage counts (int64 -- recount3 sums exceed int32).
  3. CPM = counts / library_size * 1e6  ->  log2(cpm + 1).
  4. Expression filter: keep genes with logCPM > 1 in >= 20% of samples.
  5. Select top 14,000 genes by variance as the WGCNA input.
"""
import numpy as np, pandas as pd, pickle
MAX_PER_TISSUE, TOPN, RNG = 120, 14000, 0

def normalize(counts):                      # counts: genes x samples (raw)
    libsize = counts.sum(axis=0)
    cpm = counts / libsize * 1e6
    logcpm = np.log2(cpm + 1)
    expressed = (logcpm > 1).mean(axis=1) >= 0.20
    logcpm = logcpm.loc[expressed]
    top = logcpm.var(axis=1).nlargest(TOPN).index
    return logcpm.loc[top]

# NOTE: recount3 download + per-tissue subsampling code omitted for brevity;
# see README for the recount3 S3 path pattern. This documents the transform.
if __name__ == "__main__":
    counts = pickle.load(open("counts_raw.pkl", "rb"))     # genes x samples, int64
    wg = normalize(counts)
    wg.index = [g.split('.')[0] for g in wg.index]          # strip Ensembl version
    wg = wg[~wg.index.duplicated()]
    pickle.dump(wg, open("wgcna_input.pkl", "wb"))
    print("WGCNA input:", wg.shape)
