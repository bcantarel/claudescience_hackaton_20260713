"""Deterministic extraction of ECOG max + lab thresholds from eligibility text.
Conservative: only records a value when phrasing is unambiguous."""
import json, re
from datetime import date, datetime
S=json.load(open("data/nsclc_recruiting.json"))
def g(s,*p):
    c=s
    for k in p:
        c=c.get(k) if isinstance(c,dict) else None
        if c is None: return None
    return c
def parse(d):
    if not d: return None
    for f in ("%Y-%m-%d","%Y-%m"):
        try: return datetime.strptime(d,f).date()
        except: pass
    return None
TODAY=date(2026,7,8)
def keep(s):
    if g(s,"protocolSection","designModule","studyType")!="INTERVENTIONAL": return False
    cc=parse(g(s,"protocolSection","statusModule","completionDateStruct","date"))
    if cc and cc<TODAY: return False
    return True
trials=[s for s in S if keep(s)]
def elig(s): return (g(s,"protocolSection","eligibilityModule","eligibilityCriteria") or "")
def nct(s): return s["protocolSection"]["identificationModule"]["nctId"]

# ---- ECOG max: find max allowed value 0..4 ----
def ecog_max(t):
    best=None; cite=None
    # range like "0-1", "0 to 2", "0 or 1"
    for m in re.finditer(r"ECOG[^.\n]{0,45}?([0-4])\s*(?:-|to|–|or|,|/|~)\s*([0-4])", t, re.I):
        v=max(int(m.group(1)),int(m.group(2)))
        if best is None or v<best: best=v; cite=m.group(0).strip()  # take the tightest? no—take as stated
        best=v; cite=m.group(0).strip(); break
    if best is None:
        m=re.search(r"ECOG[^.\n]{0,30}?(?:performance status|PS|score)?[^.\n\d]{0,18}?(?:of|:|≤|<=|<|=)?\s*([0-4])(?![0-9])", t, re.I)
        if m: best=int(m.group(1)); cite=m.group(0).strip()
    return best, cite

# ---- lab thresholds ----
# counts (patient must be >= threshold): ANC, platelets, hemoglobin
# upper limits (patient must be <=): creatinine, bilirubin, AST/ALT (often xULN)
def num_near(t, kw, window=60):
    m=re.search(kw, t, re.I)
    if not m: return None,None
    seg=t[m.start():m.end()+window]
    return seg, m

def parse_ge(seg):  # >= threshold value
    m=re.search(r"(?:≥|>=|greater than or equal to|at least|>)\s*([\d.,]+)\s*(?:×|x)?\s*(10\^?9?/?L|/[uµ]?L|g/dL|g/L|cells)?", seg, re.I)
    if m:
        try: return float(m.group(1).replace(',','')), m.group(0).strip()
        except: return None,None
    return None,None
def parse_le(seg):  # <= threshold (value or xULN)
    m=re.search(r"(?:≤|<=|less than or equal to|not exceed|<)\s*([\d.]+)\s*(×|x)?\s*(ULN|upper limit)?", seg, re.I)
    if m:
        uln = bool(m.group(3))
        try: return (float(m.group(1)), uln), m.group(0).strip()
        except: return None,None
    return None,None

out={}
cov={"ecog":0,"anc":0,"plt":0,"hgb":0,"cr":0,"bili":0,"astalt":0}
for s in trials:
    t=elig(s); rec={}
    em,ec=ecog_max(t)
    if em is not None: rec["ecogMax"]=em; rec["ecogCite"]=ec; cov["ecog"]+=1
    labs={}
    seg,_=num_near(t, r"neutrophil|\bANC\b"); 
    if seg:
        v,c=parse_ge(seg)
        if v: labs["anc"]={"op":">=","val":v,"cite":c}; cov["anc"]+=1
    seg,_=num_near(t, r"platelet")
    if seg:
        v,c=parse_ge(seg)
        if v: labs["plt"]={"op":">=","val":v,"cite":c}; cov["plt"]+=1
    seg,_=num_near(t, r"h[ae]moglobin|\bHgb\b")
    if seg:
        v,c=parse_ge(seg)
        if v: labs["hgb"]={"op":">=","val":v,"cite":c}; cov["hgb"]+=1
    seg,_=num_near(t, r"creatinine(?! clearance)")
    if seg:
        v,c=parse_le(seg)
        if v: labs["cr"]={"op":"<=","val":v[0],"uln":v[1],"cite":c}; cov["cr"]+=1
    seg,_=num_near(t, r"bilirubin")
    if seg:
        v,c=parse_le(seg)
        if v: labs["bili"]={"op":"<=","val":v[0],"uln":v[1],"cite":c}; cov["bili"]+=1
    seg,_=num_near(t, r"\bAST\b|\bALT\b|transaminase|aminotransferase")
    if seg:
        v,c=parse_le(seg)
        if v: labs["astalt"]={"op":"<=","val":v[0],"uln":v[1],"cite":c}; cov["astalt"]+=1
    if labs: rec["labs"]=labs
    if rec: out[nct(s)]=rec
json.dump(out, open("data/criteria_regex.json","w"), indent=1)
N=len(trials)
print(f"Extracted over {N} interventional trials:")
for k,v in cov.items(): print(f"  {k:8s}: {v} ({100*v//N}%)")
# sample
import itertools
print("\nSamples:")
for n in list(out)[:4]:
    print(f"  {n}: ecogMax={out[n].get('ecogMax')} labs={ {k:v['val'] for k,v in out[n].get('labs',{}).items()} }")
