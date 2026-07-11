import json, re
from collections import Counter

S = json.load(open("data/nsclc_recruiting.json"))
N = len(S)
print(f"=== {N} recruiting NSCLC trials ===\n")

def g(s,*path):
    cur=s
    for p in path:
        if cur is None: return None
        cur=cur.get(p) if isinstance(cur,dict) else None
    return cur

# ---------- STRUCTURED: age / sex / status ----------
sex=Counter(); minage=Counter(); maxage=Counter(); stdages=Counter()
has_min=has_max=0
for s in S:
    e=g(s,"protocolSection","eligibilityModule") or {}
    sex[e.get("sex")]+=1
    if e.get("minimumAge"): has_min+=1
    if e.get("maximumAge"): has_max+=1
    minage[e.get("minimumAge")]+=1
    maxage[e.get("maximumAge")]+=1
    for a in (e.get("stdAges") or []): stdages[a]+=1
print("SEX:", dict(sex))
print(f"minimumAge present: {has_min}/{N} ({100*has_min//N}%)  maximumAge present: {has_max}/{N}")
print("top minimumAge:", minage.most_common(6))
print("top maximumAge:", maxage.most_common(5))
print("stdAges:", dict(stdages))

# ---------- CONDITIONS + MeSH ----------
print("\n=== CONDITIONS / MeSH ===")
cond_names=Counter()
has_mesh_cond=0; mesh_terms=Counter()
nsclc_specific_mesh=0
for s in S:
    conds=g(s,"protocolSection","conditionsModule","conditions") or []
    for c in conds: cond_names[c.lower()]+=1
    meshes=g(s,"derivedSection","conditionBrowseModule","meshes") or []
    if meshes: has_mesh_cond+=1
    terms=[m.get("term","") for m in meshes]
    for t in terms: mesh_terms[t]+=1
print(f"trials with >=1 condition MeSH term: {has_mesh_cond}/{N} ({100*has_mesh_cond//N}%)")
print("\nTop 15 raw condition names (free text):")
for c,n in cond_names.most_common(15): print(f"  {n:4d}  {c}")
print("\nTop 15 derived MeSH condition terms:")
for t,n in mesh_terms.most_common(15): print(f"  {n:4d}  {t}")

# how specific is MeSH? check presence of NSCLC-specific vs generic
nsclc_mesh=sum(n for t,n in mesh_terms.items() if "non-small" in t.lower() or "carcinoma, non" in t.lower())
generic_lung=sum(n for t,n in mesh_terms.items() if "lung" in t.lower())
print(f"\nMeSH term occurrences containing 'non-small': {nsclc_mesh}")
print(f"MeSH term occurrences containing 'lung': {generic_lung}")

# per-trial: does trial have a NSCLC-specific mesh term at all?
trial_has_nsclc_mesh=0; trial_has_only_generic=0; trial_no_lung_mesh=0
for s in S:
    meshes=g(s,"derivedSection","conditionBrowseModule","meshes") or []
    terms=[m.get("term","").lower() for m in meshes]
    if any("non-small" in t for t in terms): trial_has_nsclc_mesh+=1
    elif any("lung" in t for t in terms): trial_has_only_generic+=1
    elif not any("lung" in t for t in terms): trial_no_lung_mesh+=1
print(f"\nPer-trial MeSH specificity:")
print(f"  has NSCLC-specific MeSH term: {trial_has_nsclc_mesh}/{N} ({100*trial_has_nsclc_mesh//N}%)")
print(f"  only generic lung MeSH (no NSCLC term): {trial_has_only_generic}/{N}")
print(f"  no lung MeSH term at all: {trial_no_lung_mesh}/{N}")
