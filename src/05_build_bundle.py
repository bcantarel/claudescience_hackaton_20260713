import json
from datetime import date, datetime
from oncotree import load, ancestors
from crosswalk import crosswalk
S=json.load(open("data/nsclc_recruiting.json")); nodes,by_code=load()
cache=json.load(open("data/gene_cache_full.json"))
TODAY=date(2026,7,8)
def g(s,*p):
    c=s
    for k in p:
        c=c.get(k) if isinstance(c,dict) else None
        if c is None: return None
    return c
def parse(d):
    if not d: return None
    for fmt in ("%Y-%m-%d","%Y-%m"):
        try: return datetime.strptime(d,fmt).date()
        except: pass
    return None

def keep(s):
    if g(s,"protocolSection","designModule","studyType")!="INTERVENTIONAL": return False
    cc=parse(g(s,"protocolSection","statusModule","completionDateStruct","date"))
    if cc and cc<TODAY: return False
    return True

trials=[]
n_stale=0
for s in S:
    if not keep(s): continue
    ps=s["protocolSection"]; elig=ps.get("eligibilityModule",{}) or {}
    nct=g(ps,"identificationModule","nctId")
    pc=g(ps,"statusModule","primaryCompletionDateStruct","date")
    cc=g(ps,"statusModule","completionDateStruct","date")
    lu=g(ps,"statusModule","lastUpdatePostDateStruct","date")
    pcd=parse(pc); lud=parse(lu)
    stale_reasons=[]
    if pcd and pcd<TODAY: stale_reasons.append("primary completion date passed")
    if lud and (TODAY-lud).days>365: stale_reasons.append(f"not updated in {(TODAY-lud).days//30} months")
    if stale_reasons: n_stale+=1
    tc=crosswalk(s, by_code)
    trials.append({
        "nct":nct,"title":g(ps,"identificationModule","briefTitle"),
        "status":g(ps,"statusModule","overallStatus"),
        "minAge":elig.get("minimumAge"),"maxAge":elig.get("maximumAge"),"sex":elig.get("sex","ALL"),
        "phase":(g(ps,"designModule","phases") or ["NA"]),
        "enroll":g(ps,"designModule","enrollmentInfo","count"),
        "start":pc and g(ps,"statusModule","startDateStruct","date"),
        "primaryComp":pc,"comp":cc,"lastUpdate":lu,
        "dxCodes":sorted(tc.keys()),
        "stale": bool(stale_reasons), "staleWhy": "; ".join(stale_reasons),
        "url":f"https://clinicaltrials.gov/study/{nct}",
    })

lung=[c for c in by_code if 'LUNG' in ancestors(c,by_code)]
anc_map={c:ancestors(c,by_code) for c in lung}
dx_options=sorted([{"code":c,"name":by_code[c]["name"]} for c in lung], key=lambda x:x["name"])
bundle={
  "generated":"2026-07-08","today":"2026-07-08",
  "version":"oncotree_2025_10_03 / CT.gov v2",
  "filterNote":"Interventional studies only; studies whose overall completion date has already passed are excluded. Observational studies and completed studies are omitted.",
  "counts":{"searchable":len(trials),"stale":n_stale},
  "trials":trials,"ancestors":anc_map,"dxOptions":dx_options,"geneCache":cache,
  "genes":["EGFR","ALK","ROS1","KRAS","MET","BRAF","RET","ERBB2","NTRK","NRG1"],
}
json.dump(bundle, open("data/bundle_full.json","w"))
import os
print(f"searchable trials: {len(trials)}  flagged stale: {n_stale}  gene-cache: {len(cache)}")
print(f"bundle size: {os.path.getsize('data/bundle_full.json')//1024} KB")
