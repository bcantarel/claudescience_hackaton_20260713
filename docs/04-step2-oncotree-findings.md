# Step 2 — OncoTree load + ancestor-walk lookup

**Version pinned:** `oncotree_2025_10_03` · **Source:** OncoTree API, no key. Cached `oncotree_flat.json` (897 nodes) + `oncotree_ancestors.json`. Module: `oncotree.py`.

Bottom line: OncoTree loaded cleanly, the hierarchy is well-formed, and the ancestor walk does exactly what the matcher needs — patient LUAD resolves to `LUAD → NSCLC → LUNG`.

## What OncoTree gives you
897 tumor-type nodes with `code`, `name`, `mainType`, `parent` (single-parent tree), `level`, `tissue`, `externalReferences`. 6 levels deep. Single-parent → unambiguous ancestor walk.

**External references are UMLS + NCI only** — no ICD-O/ICD-10/SNOMED in the payload. 77% have a UMLS CUI, 74% an NCI code. Confirms: no direct ICD-10/SNOMED map; UMLS is the only bridge, which is why the MVP accepts OncoTree input only.

## Ancestor walk — verified on the lung branch
`ancestors(code)` = [self, parent, …, tissue-level]. LUAD → NSCLC → LUNG; LUSC → NSCLC → LUNG; 18-node NSCLC subtree all resolve up through NSCLC. Walking *up* from NSCLC stops at LUNG without pulling in small-cell.

## The crosswalk gap (closed in step 3)
CT.gov tags diagnosis with **MeSH** (with a stable MeSH ID); OncoTree keys on **UMLS/NCI**.
- Name strings do NOT match directly (MeSH "Carcinoma, Non-Small-Cell Lung" vs OncoTree "Non-Small Cell Lung Cancer").
- The clean join is via UMLS (both map to C0007131) — but that needs the UMLS Metathesaurus license.
- MVP path: start with name/synonym matching, measure unmatched rate, add UMLS only if needed. For the lung branch this is a ~dozen-signal mapping problem, not an ontology-alignment project.
