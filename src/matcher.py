"""Step-3 matcher: diagnosis (hierarchical, walk-up) + age/sex/status filters.
Returns a shortlist with per-dimension basis. NEVER emits eligible/ineligible."""
import re, json
from oncotree import load, ancestors
from crosswalk import crosswalk

def parse_age(s):
    if not s: return None
    m=re.match(r"(\d+)", s)
    return int(m.group(1)) if m else None

def diagnosis_relation(patient_code, trial_codes, by_code):
    """Return (match:bool, relation:str, basis_code:str|None)."""
    pat_anc=ancestors(patient_code, by_code)          # [self, parent, ... root]
    pat_anc_set=set(pat_anc)
    best=None
    for tc in trial_codes:
        if tc==patient_code: return True,"exact",tc
        if tc in pat_anc_set:                          # trial broader than patient (walk up)
            best=best or ("broader",tc)
        elif patient_code in ancestors(tc,by_code):    # trial narrower than patient
            best=best or ("narrower",tc)
    if best: return True,best[0],best[1]
    return False,"none",None

def age_ok(elig, age):
    lo=parse_age(elig.get("minimumAge")); hi=parse_age(elig.get("maximumAge"))
    lo = 0 if lo is None else lo
    hi = 200 if hi is None else hi   # absent max = NO CAP (step-1 trap)
    return lo<=age<=hi, lo, (None if elig.get("maximumAge") in (None,"") else hi)

def sex_ok(elig, sex):
    ts=elig.get("sex","ALL")
    return (ts=="ALL" or ts==sex), ts

def match_patient(patient, studies, by_code):
    """patient={'oncotree','age','sex'}. Returns list of hits with basis."""
    hits=[]
    for s in studies:
        ps=s["protocolSection"]; elig=ps.get("eligibilityModule",{}) or {}
        tc=crosswalk(s, by_code)                         # {code:[reasons]}
        dmatch,rel,basis=diagnosis_relation(patient["oncotree"], list(tc.keys()), by_code)
        if not dmatch: continue
        a_ok,lo,hi=age_ok(elig, patient["age"])
        s_ok,tsex=sex_ok(elig, patient["sex"])
        if not (a_ok and s_ok): 
            continue
        hits.append({
            "nct": ps["identificationModule"]["nctId"],
            "title": ps["identificationModule"].get("briefTitle","")[:70],
            "dx_relation": rel, "dx_basis_code": basis,
            "dx_basis": tc.get(basis,[None])[0] if basis else None,
            "age_range": f"{lo}-{hi if hi else 'no cap'}",
            "sex": tsex,
        })
    return hits

if __name__=="__main__":
    S=json.load(open("data/nsclc_recruiting.json")); nodes,by_code=load()
    patients=[
        {"name":"LUAD, 62F","oncotree":"LUAD","age":62,"sex":"FEMALE"},
        {"name":"LUSC, 71M","oncotree":"LUSC","age":71,"sex":"MALE"},
        {"name":"NSCLC NOS, 45M","oncotree":"NSCLC","age":45,"sex":"MALE"},
        {"name":"LUAD, 82F (age edge)","oncotree":"LUAD","age":82,"sex":"FEMALE"},
        {"name":"LUAD, 15 (peds)","oncotree":"LUAD","age":15,"sex":"MALE"},
    ]
    from collections import Counter
    for p in patients:
        hits=match_patient(p,S,by_code)
        rels=Counter(h["dx_relation"] for h in hits)
        print(f"\n=== {p['name']}: {len(hits)} trials ===  dx_relation={dict(rels)}")
        for h in hits[:3]:
            print(f"   {h['nct']} [{h['dx_relation']} via {h['dx_basis_code']}] age {h['age_range']} sex {h['sex']}")
            print(f"      {h['title']}")
