#!/usr/bin/env python3
"""
B2 GRN ensemble -- rank-product aggregation of the three methods.
Combines GENIE3 + GRNBoost2 + CLR edge lists (each top-30 regulators/target)
into a consensus network, per the plan's Step 4 Expected Output
("ranked TF-target edge list with ensemble score, rank product across methods").

Inputs:  genie3_edges.parquet (weight), grnboost2_edges.parquet (gb_weight),
         clr_edges.parquet (clr_score)
Output:  phaseB_GRN_ensemble.parquet -- the FULL outer-joined edge table with
         per-method ranks + rank_product + ensemble_rank, annotated with
         TF/target symbol, target module, and n_methods (# methods supporting
         each edge). No rows are filtered out; downstream analysis selects the
         consensus set with `df[df.n_methods >= 2]` (edges supported by >=2
         methods = the high-confidence subset used for the sanity gate).
"""
import numpy as np, pandas as pd

def main():
    g3 = pd.read_parquet("genie3_edges.parquet").rename(columns={"weight": "genie3"})
    gb = pd.read_parquet("grnboost2_edges.parquet").rename(columns={"gb_weight": "grnboost2"})
    cl = pd.read_parquet("clr_edges.parquet").rename(columns={"clr_score": "clr"})
    m = (g3.merge(gb, on=["TF", "target"], how="outer")
           .merge(cl, on=["TF", "target"], how="outer"))
    # rank each method (higher score = rank 1); missing edges get worst rank
    for c in ["genie3", "grnboost2", "clr"]:
        r = m[c].rank(ascending=False, method="average")
        m[c + "_rank"] = r.fillna(r.max() + 1)
    m["rank_product"] = (m[["genie3_rank", "grnboost2_rank", "clr_rank"]].prod(axis=1)) ** (1/3)
    m["ensemble_rank"] = m["rank_product"].rank(method="min").astype(int)
    m["n_methods"] = m[["genie3", "grnboost2", "clr"]].notna().sum(axis=1)

    gm = pd.read_csv("phaseB_gene_TF_module.csv")
    sym = gm.dropna(subset=["symbol"]).set_index("ensembl_gene").symbol.to_dict()
    mod = gm.set_index("ensembl_gene").module.to_dict()
    m["TF_sym"] = m.TF.map(sym); m["target_sym"] = m.target.map(sym).fillna(m.target)
    m["target_module"] = m.target.map(mod)
    m.sort_values("rank_product").to_parquet("phaseB_GRN_ensemble.parquet")

if __name__ == "__main__":
    main()
