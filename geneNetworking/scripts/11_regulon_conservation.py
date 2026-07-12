#!/usr/bin/env python3
"""
Tier 1 (T1.3) -- regulon conservation synthesis. Ties four layers together:
module preservation (Zsummary), phylogenetic signal (Blomberg K), TF-family
composition, and direct TF-regulator sub-network preservation.

Two tests:
  1. Family composition -- fraction of fast-evolving C2H2/KRAB zinc-finger TFs
     per module vs Blomberg K / conservation (module-level proxy; n=17, suggestive).
  2. Regulator sub-network preservation -- for each module, edge-pattern
     preservation (human GTEx -> ortholog-aligned mouse) of the TF-regulator
     sub-block vs the full module. Result: the regulatory backbone preserves
     >= the module bulk (Wilcoxon p=0.06); liver M21 HNF core 0.94 vs 0.53.

Inputs (workspace): wgcna_input.pkl, mouse_in_humanspace.pkl,
  stage1_gene_modules.csv, phaseB_TF_annotation_table.csv, phaseA_phylo_signal.csv
Outputs: regulon_subnetwork_preservation.csv, regulon_family_composition.csv
"""
import numpy as np, pandas as pd, pickle
from scipy.stats import spearmanr, wilcoxon

# Exact family names (no loose substring matching -- avoids folding
# "GATA-type ZF" / "Zinc finger (other)" / "Nuclear factor I" into the wrong bucket).
ZNF_FAMS = {"C2H2 zinc finger"}                 # KRAB/C2H2, the fast-evolving family
CLASSICAL_FAMS = {"Homeodomain", "bHLH", "bZIP", "Nuclear receptor", "Forkhead",
                  "ETS", "HMG box", "Winged-helix (other)", "SMAD", "T-box",
                  "GATA-type ZF", "MADS box", "bHSH/AP2", "Rel/NF-kB", "Runt",
                  "Nuclear factor I"}
def famclass(f):
    if pd.isna(f): return "other"
    if f in ZNF_FAMS: return "ZNF"
    if f in CLASSICAL_FAMS: return "classical"
    return "other"   # incl. "Zinc finger (other)", "Other/unclassified"

def edge_preservation(H, M, genes):
    g = [x for x in genes if x in H.index and x in M.index]
    if len(g) < 5: return np.nan, len(g)
    ch, cm = np.corrcoef(H.loc[g].values), np.corrcoef(M.loc[g].values)
    iu = np.triu_indices(len(g), 1)
    return np.corrcoef(ch[iu], cm[iu])[0, 1], len(g)

def main():
    hs = pickle.load(open("wgcna_input.pkl", "rb"))
    mm = pickle.load(open("mouse_in_humanspace.pkl", "rb"))
    common = [g for g in hs.index if g in set(mm.index)]
    H, M = hs.loc[common], mm.loc[common]
    gm = pd.read_csv("stage1_gene_modules.csv"); gm.columns = ["ensembl_gene", "module"]
    mod = gm.set_index("ensembl_gene").module.to_dict()
    tf = pd.read_csv("phaseB_TF_annotation_table.csv"); tfset = set(tf.ensembl_gene)
    tf["famclass"] = tf.TF_family.map(famclass)

    rows = []
    for m in sorted(set(mod.values()) - {"grey"}, key=lambda x: int(x[1:])):
        genes = [g for g, mm_ in mod.items() if mm_ == m]
        tfg = [g for g in genes if g in tfset]
        rf, nf = edge_preservation(H, M, genes[:400])
        rt, nt = edge_preservation(H, M, tfg)
        rows.append(dict(module=m, n_full=nf, n_tf=nt, pres_full=rf, pres_tf=rt,
                         tf_minus_full=(rt - rf) if not (np.isnan(rt) or np.isnan(rf)) else np.nan))
    R = pd.DataFrame(rows)
    R.to_csv("regulon_subnetwork_preservation.csv", index=False)
    V = R.dropna(subset=["pres_tf", "pres_full"])
    print("mean full=%.3f  mean TF=%.3f  Wilcoxon p=%.4f"
          % (V.pres_full.mean(), V.pres_tf.mean(), wilcoxon(V.pres_tf, V.pres_full)[1]))
    # family composition
    comp = (tf[tf.module != "grey"].groupby("module")
            .agg(n_TF=("symbol", "size"),
                 frac_ZNF=("famclass", lambda s: (s == "ZNF").mean())).reset_index())
    comp.to_csv("regulon_family_composition.csv", index=False)

if __name__ == "__main__":
    main()
