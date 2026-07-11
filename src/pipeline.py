"""End-to-end: patient -> diagnosis+structured shortlist (step 3) -> gene layer (step 4).
Produces per-trial per-dimension basis with three-valued biomarker results and citations.
The LLM classifier is injected; here we run deterministic scan and mark snippets that
NEED classification. NEVER emits an overall eligible/ineligible verdict."""
import json
from oncotree import load
from matcher import match_patient
from gene_scan import scan_trial
from classifier import build_prompt, map_to_patient

def build_candidates(patient, studies, by_code):
    """patient: {oncotree, age, sex, biomarkers:{SYM:'altered'|'wildtype'|None}}"""
    shortlist = match_patient(patient, studies, by_code)
    by_nct = {s["protocolSection"]["identificationModule"]["nctId"]: s for s in studies}
    pt_genes = list(patient.get("biomarkers",{}).keys())
    out=[]
    for hit in shortlist:
        s = by_nct[hit["nct"]]
        elig = (s["protocolSection"].get("eligibilityModule",{}) or {}).get("eligibilityCriteria","")
        snippets = scan_trial(elig, pt_genes)
        # collapse to biomarker-gating snippets (drop pure therapy mentions for the gate decision,
        # but keep count of them for transparency)
        gating = [h for h in snippets if not h["therapy_context"]]
        hit["biomarker_snippets"] = gating
        hit["n_therapy_mentions"] = sum(1 for h in snippets if h["therapy_context"])
        hit["needs_llm"] = len(gating)  # number of classifier calls this trial requires
        out.append(hit)
    return out

if __name__=="__main__":
    S=json.load(open("data/nsclc_recruiting.json")); nodes,by_code=load()
    # Real-ish patient: EGFR-mutant LUAD, 64F
    patient={"oncotree":"LUAD","age":64,"sex":"FEMALE",
             "biomarkers":{"EGFR":"altered"}}
    cands=build_candidates(patient,S,by_code)
    from collections import Counter
    tot=len(cands)
    with_snip=[c for c in cands if c["needs_llm"]>0]
    calls=sum(c["needs_llm"] for c in cands)
    print(f"Patient: EGFR-altered LUAD, 64F")
    print(f"  step-3 shortlist (dx+age+sex): {tot} trials")
    print(f"  trials with >=1 EGFR gating snippet (need LLM): {len(with_snip)}")
    print(f"  total classifier calls needed: {calls}  (avg {calls/max(1,len(with_snip)):.1f}/trial)")
    secs=Counter(h['section'] for c in cands for h in c['biomarker_snippets'])
    print(f"  gating-snippet sections: {dict(secs)}")
    print("\n  Example gating snippets (first 6):")
    n=0
    for c in with_snip:
        for h in c["biomarker_snippets"]:
            print(f"   {c['nct']} [{h['section']}] {h['biomarker']}: {h['snippet'][:130]}")
            n+=1
            if n>=6: break
        if n>=6: break
    json.dump(cands, open("data/candidates_egfr_luad.json","w"), indent=1)
