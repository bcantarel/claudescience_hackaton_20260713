#!/usr/bin/env python3
"""
Tier 1 -- module functional annotation (GO/KEGG enrichment ONLY).
Over-representation analysis of each WGCNA module's gene set against GO:BP,
KEGG and Reactome via the g:Profiler REST API, using the 14,000-gene network
as the custom background and g:SCS multiple-testing correction (FDR<0.05).

SCOPE NOTE: this is the functional-enrichment line-item of the uploaded plan's
Step 9, NOT Step 9 itself. Plan Step 9 is "Regulatory Module Discovery via
Matrix Factorization" (consensus NMF k=10-40 / LDA on the TF-target matrix to
DISCOVER new regulatory-program modules, with module-to-clade enrichment and
top-20-module heatmaps). That matrix-factorization discovery is NOT done here --
it is deferred to the future-directions plan (F6). Here we only annotate the
already-defined WGCNA co-expression modules with enriched GO/KEGG/Reactome terms.

Input:  stage1_gene_modules.csv (ensembl_gene, module)
Output: module_functional_annotation.csv (top-5 terms + best term per module),
        module_enrichment_full.csv (all significant terms, all modules).
"""
import json, urllib.request, pandas as pd

def gprofiler(sets, background):
    payload = {"organism": "hsapiens", "query": sets,
               "sources": ["GO:BP", "KEGG", "REAC"], "user_threshold": 0.05,
               "significance_threshold_method": "g_SCS", "no_evidences": True,
               "domain_scope": "custom", "background": background, "ordered": False}
    req = urllib.request.Request("https://biit.cs.ut.ee/gprofiler/api/gost/profile/",
        data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())["result"]

def main():
    gm = pd.read_csv("stage1_gene_modules.csv"); gm.columns = ["ensembl_gene", "module"]
    mods = sorted([m for m in gm.module.unique() if m != "grey"], key=lambda x: int(x[1:]))
    sets = {m: gm[gm.module == m].ensembl_gene.tolist() for m in mods}
    df = pd.DataFrame(gprofiler(sets, gm.ensembl_gene.tolist()))
    (df[["query", "source", "native", "name", "p_value", "term_size", "intersection_size"]]
       .rename(columns={"query": "module"}).sort_values(["module", "p_value"])
       .to_csv("module_enrichment_full.csv", index=False))
    rows = []
    for m in mods:
        sub = df[df["query"] == m].sort_values("p_value")
        top5 = "; ".join(f"{r['name']} ({r.source},p={r.p_value:.0e})" for _, r in sub.head(5).iterrows())
        b = sub.iloc[0]
        rows.append(dict(module=m, n_enriched=len(sub), best_term=b["name"],
                         best_source=b.source, best_p=b.p_value, top5_terms=top5))
    pd.DataFrame(rows).to_csv("module_functional_annotation.csv", index=False)

if __name__ == "__main__":
    main()
