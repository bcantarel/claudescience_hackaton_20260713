"""LLM snippet classifier — swappable interface.
Classifies a (biomarker, snippet) into the trial's REQUIREMENT DIRECTION, then
maps to a three-valued result against the patient's gene status.

The LLM call is abstracted: classify_snippet(biomarker, snippet, llm) where `llm`
is any callable(prompt)->json-string. In production this is a Claude API call;
in the prototype we drive it with a subagent. Deterministic mapping lives here."""

DIRECTIONS = ["ALTERED_REQUIRED","WILD_TYPE_REQUIRED","ALTERATION_EXCLUDED","NOT_A_REQUIREMENT"]

SCHEMA = {
  "type":"object",
  "properties":{
    "direction":{"enum":DIRECTIONS},
    "confidence":{"enum":["high","medium","low"]},
    "cited_span":{"type":"string","description":"exact substring justifying the call"},
  },
  "required":["direction","confidence","cited_span"],
}

PROMPT = """You classify a single clinical-trial eligibility SNIPPET for one biomarker.
Decide what the trial REQUIRES about this biomarker for enrollment. Output JSON only.

biomarker: {biomarker}
snippet: ""\"{snippet}""\"

direction = one of:
- ALTERED_REQUIRED: trial requires the patient to HAVE an alteration in this biomarker
  (e.g. "documented EGFR sensitizing mutation", "ALK-positive", "MET exon 14 skipping").
- WILD_TYPE_REQUIRED: trial requires the patient to NOT have an alteration / be wild-type
  (e.g. "no EGFR or ALK genomic aberrations", "EGFR wild-type").
- ALTERATION_EXCLUDED: an alteration in this biomarker is an EXCLUSION criterion
  (e.g. "must not harbor EGFR sensitizing mutations", "excluded if ALK rearrangement").
- NOT_A_REQUIREMENT: the mention is NOT an enrollment gate for this biomarker — e.g. it
  describes PRIOR THERAPY ("progression after EGFR-TKI"), says testing is optional
  ("EGFR testing not required"), or is background/context.

Rules:
- WILD_TYPE_REQUIRED and ALTERATION_EXCLUDED are close; use EXCLUDED only when the snippet
  frames the alteration as an exclusion. When a trial lists "no EGFR/ALK/ROS1" as an
  inclusion condition, that is WILD_TYPE_REQUIRED.
- If the snippet only mentions a drug/therapy targeting the gene, it's NOT_A_REQUIREMENT.
- cited_span must be an exact substring of the snippet.
Output exactly: {{"direction": "...", "confidence":"high|medium|low", "cited_span":"..."}}"""

def map_to_patient(direction, patient_has_alteration):
    """Three-valued result: MET / NOT_MET / UNKNOWN.
    patient_has_alteration: True (patient lists this gene as altered),
    False (patient tested wild-type), None (unknown/not tested)."""
    if direction=="NOT_A_REQUIREMENT":
        return "UNKNOWN","biomarker mentioned but not an enrollment gate"
    if patient_has_alteration is None:
        return "UNKNOWN","trial gates on this biomarker; patient status not provided"
    if direction=="ALTERED_REQUIRED":
        return ("MET" if patient_has_alteration else "NOT_MET"), "trial requires alteration"
    if direction=="WILD_TYPE_REQUIRED":
        return ("NOT_MET" if patient_has_alteration else "MET"), "trial requires wild-type"
    if direction=="ALTERATION_EXCLUDED":
        return ("NOT_MET" if patient_has_alteration else "MET"), "alteration is exclusionary"
    return "UNKNOWN","unclassified"

def build_prompt(biomarker, snippet):
    return PROMPT.format(biomarker=biomarker, snippet=snippet.replace('"',"'"))

if __name__=="__main__":
    # truth-table sanity check of the deterministic mapping
    for d in DIRECTIONS:
        for ph in (True, False, None):
            print(f"{d:22s} patient_altered={str(ph):5s} -> {map_to_patient(d,ph)}")
