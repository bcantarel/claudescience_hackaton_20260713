"""Deterministic gene scan + snippet extraction for a trial's eligibilityCriteria.
Query-time, only for the patient's genes. Produces sentence-level snippets with
therapy-phrase mentions filtered out. No classification here (that's the LLM step)."""
import re
from genes_dict import PATTERNS, THERAPY_RX, PANEL

_SENT = re.compile(r"(?<=[.;\n])\s+")
_EXC_HDR = re.compile(r"exclusion\s+criteria", re.I)
_INC_HDR = re.compile(r"inclusion\s+criteria", re.I)

def split_sentences_with_section(text):
    """Yield (sentence, section) where section in {'inclusion','exclusion','unknown'}.
    97% of CT.gov blobs carry Inclusion/Exclusion headers; we track which region a
    sentence falls in so the classifier gets deterministic section context."""
    # find the exclusion header offset (first one)
    m=_EXC_HDR.search(text)
    exc_start = m.start() if m else None
    mi=_INC_HDR.search(text)
    has_inc = mi is not None
    out=[]
    offset=0
    for chunk in text.split("\n"):
        chunk_start=offset
        for s in _SENT.split(chunk):
            s2=s.strip(" -*•\t")
            if s2:
                pos=chunk_start
                if exc_start is not None and pos>=exc_start: sec="exclusion"
                elif has_inc: sec="inclusion"
                else: sec="unknown"
                out.append((s2, sec))
        offset+=len(chunk)+1
    return out

def scan_trial(elig_text, patient_biomarkers):
    """patient_biomarkers: list of canonical symbols (e.g. ['EGFR','KRAS']).
    Returns list of {biomarker, matched, snippet, therapy_context, section}."""
    hits=[]
    sents=split_sentences_with_section(elig_text)
    for sym in patient_biomarkers:
        pat=PATTERNS.get(sym)
        if not pat: continue
        for sent, section in sents:
            for m in pat.finditer(sent):
                therapy = bool(THERAPY_RX.search(sent[max(0,m.start()-3):m.end()+12]))
                hits.append({
                    "biomarker": sym,
                    "matched": sent[m.start():m.end()],
                    "snippet": sent[:400],
                    "therapy_context": therapy,
                    "section": section,
                })
                break  # one snippet per sentence per gene
    return hits

if __name__=="__main__":
    import json
    from genes_dict import PATTERNS as P
    S=json.load(open("data/nsclc_recruiting.json"))
    def elig(s): return (s.get("protocolSection",{}).get("eligibilityModule",{}) or {}).get("eligibilityCriteria","") or ""
    # re-check MET cleanliness
    met=0; badmet=0
    for s in S:
        for h in scan_trial(elig(s), ["MET"]):
            met+=1
            if not re.search(r"MET|c-Met|amplif|exon|skip", h["matched"]+h["snippet"]): badmet+=1
    print(f"MET snippets now: {met}, obviously-bad: {badmet}")
    # snippet volume for a broad-panel patient
    from collections import Counter
    panel=["EGFR","ALK","ROS1","KRAS","MET","BRAF","RET","ERBB2","NTRK"]
    vol=[]; therapy_frac=Counter()
    for s in S:
        hs=scan_trial(elig(s), panel)
        if hs: vol.append(len(hs))
        for h in hs: therapy_frac["therapy" if h["therapy_context"] else "biomarker"]+=1
    import statistics
    trials_with=len(vol)
    print(f"Trials with >=1 panel-gene snippet: {trials_with}/{len(S)}")
    print(f"Snippets per such trial: median={statistics.median(vol):.0f} mean={statistics.mean(vol):.1f} max={max(vol)}")
    print(f"Snippet therapy vs biomarker context: {dict(therapy_frac)}")
