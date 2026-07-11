import json, glob, re
from collections import Counter
need=json.load(open("data/units_need.json"))
full=json.load(open("data/units_full.json"))
old=json.load(open("data/gene_cache.json"))

# load new results, align to need (batches of 50)
B=50; res={}
for f in sorted(glob.glob("data/exp/result_*.json")):
    b=int(re.search(r"result_(\d+)",f).group(1))
    for o in json.load(open(f)): res[(b,o["i"])]=o
newmap={}
bad=0
for idx,u in enumerate(need):
    b=idx//B; i=idx%B
    r=res.get((b,i)) or {"direction":"NOT_A_REQUIREMENT","confidence":"low","cited_span":""}
    span=r.get("cited_span","")
    exact = span and span in u["snippet"]
    if span and not exact: bad+=1
    newmap[f"{u['nct']}|{u['biomarker']}"]={"direction":r["direction"],"confidence":r.get("confidence","medium"),
        "cited_span": span if exact else u["snippet"],"section":u["section"],"span_verified":bool(exact)}

# assemble final cache over ALL full pairs: prefer new result, else reuse old cache
cache={}
missing=0
for u in full:
    key=f"{u['nct']}|{u['biomarker']}"
    if key in newmap: cache[key]=newmap[key]
    elif key in old: cache[key]=old[key]
    else: missing+=1
json.dump(cache, open("data/gene_cache_full.json","w"), indent=1)
print(f"Full cache entries: {len(cache)}  (new classified: {len(newmap)}, reused old: {len(cache)-len(newmap)}, missing: {missing})")
print(f"new cited_span non-exact (fell back): {bad}/{len(need)}")
print("Direction dist:", dict(Counter(v['direction'] for v in cache.values())))
print("Confidence dist:", dict(Counter(v['confidence'] for v in cache.values())))
