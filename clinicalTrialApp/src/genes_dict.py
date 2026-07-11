"""NSCLC-weighted gene / biomarker dictionary with synonyms.
Gene-level only (no variant parsing) per MVP scope. Symbols matched with
word boundaries, case-insensitive. 'aliases' includes protein/legacy names."""

# canonical symbol -> {aliases:[...], is_gene:bool}
PANEL = {
    "EGFR":  {"aliases":["EGFR","ERBB1","HER1"], "is_gene":True},
    "ALK":   {"aliases":["ALK"], "is_gene":True},
    "ROS1":  {"aliases":["ROS1","ROS-1"], "is_gene":True},
    "KRAS":  {"aliases":["KRAS"], "is_gene":True},
    "MET":   {"aliases":["MET","c-MET","cMET","c-Met","METex14"], "is_gene":True, "case_sensitive":True},
    "BRAF":  {"aliases":["BRAF"], "is_gene":True},
    "RET":   {"aliases":["RET"], "is_gene":True, "case_sensitive":True},
    "ERBB2": {"aliases":["ERBB2","HER2","HER-2","HER2/neu"], "is_gene":True},
    "NTRK":  {"aliases":["NTRK","NTRK1","NTRK2","NTRK3","TRK","TRKA","TRKB","TRKC"], "is_gene":True},
    "NRG1":  {"aliases":["NRG1"], "is_gene":True},
    "KRASG12C":{"aliases":["G12C"], "is_gene":True},  # common variant-as-gate; still gene-level KRAS
    # non-gene biomarkers commonly gating NSCLC trials
    "PDL1":  {"aliases":["PD-L1","PDL1","PD L1","CD274"], "is_gene":False},
    "TMB":   {"aliases":["TMB","tumor mutational burden","tumour mutational burden"], "is_gene":False},
    "MSI":   {"aliases":["MSI","MSI-H","microsatellite instability"], "is_gene":False},
}

import re
def _compile(aliases, case_sensitive=False):
    parts=sorted((re.escape(a) for a in aliases), key=len, reverse=True)
    flags=0 if case_sensitive else re.I
    return re.compile(r"(?<![A-Za-z0-9])(?:"+"|".join(parts)+r")(?![A-Za-z0-9])", flags)

PATTERNS = {sym:_compile(v["aliases"], v.get("case_sensitive",False)) for sym,v in PANEL.items()}
GENE_SYMBOLS = [s for s,v in PANEL.items() if v["is_gene"]]

# therapy-phrase filter (step-1 finding): GENE followed by -TKI/inhibitor/etc = prior therapy, not biomarker
THERAPY_RX = re.compile(r"(EGFR|ALK|ROS1|MET|RET|BRAF|HER2|NTRK)[\s/-]*(TKI|inhibitor|targeted|directed|mab|antibody|blocker)", re.I)

if __name__=="__main__":
    print(f"{len(PANEL)} biomarkers; {len(GENE_SYMBOLS)} genes")
    for s,v in PANEL.items(): print(f"  {s:9s} gene={v['is_gene']}  aliases={v['aliases']}")
