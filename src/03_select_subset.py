import json, re
from gene_scan import scan_trial
from crosswalk import crosswalk
from oncotree import load
S=json.load(open("data/nsclc_recruiting.json")); nodes,by_code=load()
def elig(s): return (s.get("protocolSection",{}).get("eligibilityModule",{}) or {}).get("eligibilityCriteria","") or ""
def nct(s): return s["protocolSection"]["identificationModule"]["nctId"]
def title(s): return s["protocolSection"]["identificationModule"].get("briefTitle","")

ACTIONABLE=["EGFR","ALK","ROS1","KRAS","MET","BRAF","RET"]
DECISIVE=re.compile(r"wild[- ]?type|must not|exclu|negative|without|sensitiz|activating|mutation|mutant|positive|rearrang|fusion|amplif|exon\s*\d|skipping|G12C|G12D|L858|exon 19|T790|V600", re.I)

# score trials by decisive-gate density; require a lung dx crosswalk; keep manageable snippet count per trial
cands=[]
for s in S:
    tc=crosswalk(s, by_code)
    if not tc: continue
    hs=[h for h in scan_trial(elig(s), ACTIONABLE) if not h["therapy_context"]]
    decisive=[h for h in hs if DECISIVE.search(h["snippet"])]
    if not decisive: continue
    # cap snippets per trial to the most decisive 4 to bound classification cost
    decisive=sorted(decisive, key=lambda h: len(DECISIVE.findall(h["snippet"])), reverse=True)[:4]
    genes=sorted({h["biomarker"] for h in decisive})
    cands.append({"nct":nct(s),"title":title(s),"n":len(decisive),"genes":genes,"snips":decisive})

# ensure gene coverage: greedily pick to balance across genes, cap ~150 trials
from collections import Counter
cands.sort(key=lambda c: (-len(c["genes"]), -c["n"]))
picked=[]; gene_ct=Counter(); snip_budget=0
for c in cands:
    picked.append(c); 
    for g in c["genes"]: gene_ct[g]+=1
    snip_budget+=c["n"]
    if len(picked)>=150: break

print(f"Candidate trials with decisive gates: {len(cands)}")
print(f"Selected: {len(picked)} trials, {snip_budget} snippets to classify")
print(f"Gene coverage across selection: {dict(gene_ct)}")
# flatten to classification units
units=[]
for c in picked:
    for h in c["snips"]:
        units.append({"nct":c["nct"],"biomarker":h["biomarker"],"section":h["section"],"snippet":h["snippet"]})
json.dump({"trials":picked,"units":units}, open("data/subset.json","w"), indent=1)
print(f"Total classification units: {len(units)}")
import math
print(f"Batches at 45/batch: {math.ceil(len(units)/45)}")
