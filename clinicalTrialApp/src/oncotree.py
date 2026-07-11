"""OncoTree loader + ancestor-walk lookup. Version pinned: oncotree_2025_10_03."""
import json, os

_DIR=os.path.dirname(os.path.abspath(__file__))
FLAT=os.path.join(_DIR,"data","oncotree_flat.json")

def load():
    nodes=json.load(open(FLAT))
    by_code={n["code"]:n for n in nodes}
    return nodes, by_code

def ancestors(code, by_code):
    """Return [self, parent, ... , tissue-root] codes. Stops at TISSUE/None/cycle."""
    chain=[]; seen=set(); cur=code
    while cur and cur in by_code and cur not in seen:
        seen.add(cur); chain.append(cur)
        p=by_code[cur].get("parent")
        if not p or p=="TISSUE": break
        cur=p
    return chain

def lineage_names(code, by_code):
    return [(c, by_code[c]["name"]) for c in ancestors(code, by_code)]

def build_ancestor_index(by_code):
    """code -> list of ancestor codes (self first, root last)."""
    return {c: ancestors(c, by_code) for c in by_code}

if __name__=="__main__":
    nodes, by_code = load()
    print(f"{len(nodes)} nodes; codes incl. lung?")
    for c in ["LUAD","LUSC","NSCLC","LUNG","NSCLCPD","LCLC"]:
        if c in by_code:
            n=by_code[c]
            refs=n.get("externalReferences",{})
            print(f"\n{c}: {n['name']}  (mainType={n.get('mainType')}, level={n.get('level')})")
            print("  refs:", {k:v for k,v in refs.items()})
            print("  lineage:", " -> ".join(f"{c2}({nm})" for c2,nm in lineage_names(c,by_code)))
        else:
            print(f"\n{c}: NOT FOUND")
    idx=build_ancestor_index(by_code)
    json.dump(idx, open(os.path.join(_DIR,"data","oncotree_ancestors.json"),"w"))
    print(f"\nAncestor index built: {len(idx)} entries -> data/oncotree_ancestors.json")
