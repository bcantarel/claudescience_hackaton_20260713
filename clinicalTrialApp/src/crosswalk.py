"""Diagnosis crosswalk: CT.gov trial -> OncoTree lung-branch code(s).
Strategy (per build plan): MeSH-ID map first, condition-name regex fallback,
measure unmatched before adding anything heavier."""
import re, json
from oncotree import load, ancestors

# --- MeSH ID -> OncoTree code (curated, lung branch). MeSH lung granularity
# stops at NSCLC/SCLC/Lung; there is no MeSH term for LUAD/LUSC. ---
MESH_TO_OT = {
    "D002289": "NSCLC",   # Carcinoma, Non-Small-Cell Lung
    "D008175": "LUNG",    # Lung Neoplasms
    "D008171": "LUNG",    # Lung Diseases (weak, but lung)
    "D055752": "SCLC",    # Small Cell Lung Carcinoma
    "D018288": "SCLC",    # Carcinoma, Small Cell (occasionally)
    "D002282": "LUCA",    # Carcinoid tumor (rare)
    "D000077192":"LUAD",  # Adenocarcinoma of Lung (if present)
}

# --- Condition-name regex fallback -> OncoTree code. Order matters (specific first). ---
def name_to_code(name):
    """Token-presence mapping of a free-text condition name -> OncoTree code (or None).
    Order = specific first. Handles word-order variants like 'Lung Non-Small Cell Carcinoma'."""
    t=name.lower()
    has_lung = bool(re.search(r"\blung\b|pulmonary", t))
    if re.search(r"adenocarcinoma", t) and has_lung: return "LUAD"
    if re.search(r"squamous", t) and has_lung: return "LUSC"
    if re.search(r"non[- ]?small[- ]?cell", t) and has_lung: return "NSCLC"
    if re.search(r"nsclc", t): return "NSCLC"
    if re.search(r"small[- ]?cell", t) and has_lung and not re.search(r"non[- ]?small", t): return "SCLC"
    if re.search(r"sclc", t): return "SCLC"
    if has_lung and re.search(r"cancer|carcinoma|neoplasm|tumou?r|malignan|nodule", t): return "LUNG"
    return None

def trial_signals(study):
    conds = (study.get("protocolSection",{}).get("conditionsModule",{}) or {}).get("conditions",[]) or []
    meshes = (study.get("derivedSection",{}).get("conditionBrowseModule",{}) or {}).get("meshes",[]) or []
    return conds, meshes

def crosswalk(study, by_code):
    """Return dict: {ot_code: [reasons]} of lung-branch OncoTree codes for this trial."""
    conds, meshes = trial_signals(study)
    out = {}
    for m in meshes:
        code = MESH_TO_OT.get(m.get("id"))
        if code and code in by_code:
            out.setdefault(code,[]).append(f"MeSH:{m['id']}({m['term']})")
    for name in conds:
        code=name_to_code(name)
        if code and code in by_code:
            out.setdefault(code,[]).append(f"cond:'{name}'")
    return out

if __name__=="__main__":
    S=json.load(open("data/nsclc_recruiting.json")); nodes,by_code=load()
    N=len(S)
    from collections import Counter
    cov_mesh=0; cov_any=0; codes_ct=Counter(); no_match=[]
    lungset={c for c in by_code if 'LUNG' in ancestors(c,by_code)}
    for s in S:
        conds,meshes=trial_signals(s)
        # mesh-only
        mesh_codes={MESH_TO_OT.get(m.get('id')) for m in meshes}
        mesh_codes={c for c in mesh_codes if c}
        full=crosswalk(s,by_code)
        if mesh_codes: cov_mesh+=1
        if full: cov_any+=1
        else: no_match.append(s)
        for c in full: codes_ct[c]+=1
    print(f"Trials: {N}")
    print(f"  covered by MeSH map alone:      {cov_mesh}/{N} ({100*cov_mesh//N}%)")
    print(f"  covered by MeSH + name fallback:{cov_any}/{N} ({100*cov_any//N}%)")
    print(f"  UNMATCHED (no lung OT code):    {len(no_match)}/{N} ({100*len(no_match)//N}%)")
    print("\n  OncoTree codes assigned (trial-level):")
    for c,n in codes_ct.most_common(): print(f"    {c:8s} {n}")
    print("\n  Sample of UNMATCHED trials (condition names):")
    for s in no_match[:12]:
        conds,_=trial_signals(s)
        nct=s['protocolSection']['identificationModule']['nctId']
        print(f"    {nct}: {conds[:3]}")
