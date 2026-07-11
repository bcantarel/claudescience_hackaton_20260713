import Foundation

// Port of the web tool's matcher (matcher.py / the HTML JS). Deterministic:
// OncoTree ancestor walk-up for diagnosis, age/sex filter, three-valued gene +
// clinical-criteria mapping. Never emits an overall eligible/ineligible verdict.

enum BioResult: String {
    case met = "MET"
    case notMet = "NOT_MET"
    case unknown = "UNKNOWN"
    var label: String { rawValue.replacingOccurrences(of: "_", with: " ") }
}

struct BioBasis: Identifiable {
    let id = UUID()
    let gene: String
    let result: BioResult
    let why: String
    let direction: String
    let cite: String
    let section: String
}

struct CritBasis: Identifiable {
    let id = UUID()
    let key: String
    let result: BioResult
    let why: String
    let cite: String
}

struct MatchRow: Identifiable {
    let id = UUID()
    let trial: Trial
    let dxRelation: String
    let dxBasis: String
    let ageLo: Int
    let ageHi: Int?        // nil = no upper cap
    let bios: [BioBasis]
    let crits: [CritBasis]
    let bsig: String       // MET / NOT_MET / UNKNOWN / NA
}

enum SortMode: String, CaseIterable, Identifiable {
    case relevance = "Biomarker relevance"
    case startDesc = "Start date — newest"
    case startAsc = "Start date — oldest"
    case updatedDesc = "Recently updated"
    var id: String { rawValue }
}

// Lab definitions (order + comparison direction). "ge" = patient must be >= threshold.
struct LabDef: Identifiable {
    let key: String, label: String, unit: String, dir: String
    var id: String { key }
}
let LAB_DEFS: [LabDef] = [
    .init(key: "anc",    label: "ANC",        unit: "×10⁹/L", dir: "ge"),
    .init(key: "plt",    label: "Platelets",  unit: "×10⁹/L", dir: "ge"),
    .init(key: "hgb",    label: "Hemoglobin", unit: "g/dL",   dir: "ge"),
    .init(key: "cr",     label: "Creatinine", unit: "mg/dL",  dir: "le"),
    .init(key: "bili",   label: "Bilirubin",  unit: "mg/dL",  dir: "le"),
    .init(key: "astalt", label: "AST/ALT",    unit: "×ULN",   dir: "le"),
]

// Patient-entered clinical criteria (all optional).
struct PatientCriteria {
    var ecog: String = ""          // "" or "0"..."4"
    var priorTx: String = ""       // "" / "naive" / "pretreated"
    var brainMets: Bool = false
    var priorIO: Bool = false
    var labs: [String: Double] = [:]   // key -> value
    var isEmpty: Bool {
        ecog.isEmpty && priorTx.isEmpty && !brainMets && !priorIO && labs.isEmpty
    }
}

struct Matcher {
    let bundle: AppBundle

    func ancestors(_ code: String) -> [String] { bundle.ancestors[code] ?? [code] }

    func dxRelation(patient: String, trialCodes: [String]) -> (String, String)? {
        let anc = Set(ancestors(patient))
        if trialCodes.contains(patient) { return ("exact", patient) }
        for tc in trialCodes where anc.contains(tc) { return ("broader", tc) }
        for tc in trialCodes where Set(ancestors(tc)).contains(patient) { return ("narrower", tc) }
        return nil
    }

    func parseAge(_ s: String?) -> Int? {
        guard let s = s else { return nil }
        let digits = s.prefix { $0.isNumber }
        return Int(digits)
    }

    func mapBio(_ direction: String, hasAlt: Bool?) -> (BioResult, String) {
        if direction == "NOT_A_REQUIREMENT" { return (.unknown, "mentioned but not an enrollment gate") }
        guard let hasAlt = hasAlt else { return (.unknown, "trial gates on this gene; status not entered") }
        switch direction {
        case "ALTERED_REQUIRED":    return (hasAlt ? .met : .notMet, "trial requires an alteration")
        case "WILD_TYPE_REQUIRED":  return (hasAlt ? .notMet : .met, "trial requires wild-type")
        case "ALTERATION_EXCLUDED": return (hasAlt ? .notMet : .met, "alteration is exclusionary")
        default:                    return (.unknown, "unclassified")
        }
    }

    // Port of critResults() from the web tool.
    func critResults(_ t: Trial, _ pc: PatientCriteria) -> [CritBasis] {
        let c = bundle.criteriaCache?[t.nct]
        var out: [CritBasis] = []

        if !pc.ecog.isEmpty {
            if let maxE = c?.ecogMax, let pv = Int(pc.ecog) {
                out.append(CritBasis(key: "ECOG",
                    result: pv <= maxE ? .met : .notMet,
                    why: "trial allows ECOG ≤ \(maxE); patient \(pc.ecog)",
                    cite: c?.ecogCite ?? ""))
            } else {
                out.append(CritBasis(key: "ECOG", result: .unknown,
                    why: "ECOG limit not found in criteria", cite: ""))
            }
        }
        if pc.brainMets {
            switch c?.brainMets {
            case "excluded":
                out.append(CritBasis(key: "Brain/CNS mets", result: .notMet,
                    why: "active brain/CNS metastases excluded", cite: c?.brainCite ?? ""))
            case "allowed_if_treated":
                out.append(CritBasis(key: "Brain/CNS mets", result: .met,
                    why: "treated/stable brain mets allowed — verify patient meets the specifics",
                    cite: c?.brainCite ?? ""))
            default:
                out.append(CritBasis(key: "Brain/CNS mets", result: .unknown,
                    why: "brain-mets rule not specified", cite: ""))
            }
        }
        if pc.priorIO {
            if c?.priorIO == "excluded" {
                out.append(CritBasis(key: "Prior immunotherapy", result: .notMet,
                    why: "prior immunotherapy not permitted", cite: c?.ioCite ?? ""))
            } else {
                out.append(CritBasis(key: "Prior immunotherapy", result: .unknown,
                    why: "prior-immunotherapy rule not specified", cite: ""))
            }
        }
        if !pc.priorTx.isEmpty {
            switch c?.priorTx {
            case "naive_required":
                out.append(CritBasis(key: "Prior treatment",
                    result: pc.priorTx == "naive" ? .met : .notMet,
                    why: "trial requires treatment-naive", cite: c?.txCite ?? ""))
            case "pretreated_required":
                out.append(CritBasis(key: "Prior treatment",
                    result: pc.priorTx == "pretreated" ? .met : .notMet,
                    why: "trial requires prior therapy", cite: c?.txCite ?? ""))
            default:
                out.append(CritBasis(key: "Prior treatment", result: .unknown,
                    why: "line-of-therapy not specified", cite: ""))
            }
        }
        for def in LAB_DEFS {
            guard let pv = pc.labs[def.key] else { continue }
            guard let lab = c?.labs?[def.key] else {
                out.append(CritBasis(key: def.label, result: .unknown,
                    why: "no \(def.label) threshold found", cite: ""))
                continue
            }
            let ok = def.dir == "ge" ? (pv >= lab.val) : (pv <= lab.val)
            let ulnStr = (lab.uln ?? false) ? "×ULN" : ""
            out.append(CritBasis(key: def.label, result: ok ? .met : .notMet,
                why: "trial \(lab.op) \(clean(lab.val))\(ulnStr); patient \(clean(pv)) — verify units",
                cite: lab.cite ?? ""))
        }
        return out
    }

    private func clean(_ d: Double) -> String {
        d == d.rounded() ? String(Int(d)) : String(d)
    }

    func run(dx: String, age: Int, sex: String, genes: [String: String],
             pc: PatientCriteria, hideStale: Bool, hideFails: Bool,
             startAfter: String, sort: SortMode) -> [MatchRow] {
        var rows: [MatchRow] = []
        for t in bundle.trials {
            guard let (rel, basis) = dxRelation(patient: dx, trialCodes: t.dxCodes) else { continue }
            if hideStale && (t.stale ?? false) { continue }
            if !startAfter.isEmpty {
                let yr = String((t.start ?? "").prefix(4))
                if yr.isEmpty || yr < startAfter { continue }
            }
            let lo = parseAge(t.minAge) ?? 0
            let hiRaw = parseAge(t.maxAge)
            let hi = hiRaw ?? 200
            if !(age >= lo && age <= hi) { continue }
            let ts = t.sex ?? "ALL"
            if !(ts == "ALL" || ts == sex) { continue }

            var bios: [BioBasis] = []
            for (g, status) in genes {
                guard let c = bundle.geneCache["\(t.nct)|\(g)"] else { continue }
                let hasAlt: Bool? = status == "altered" ? true : (status == "wildtype" ? false : nil)
                let (res, why) = mapBio(c.direction, hasAlt: hasAlt)
                bios.append(BioBasis(gene: g, result: res, why: why,
                                     direction: c.direction, cite: c.cited_span ?? "",
                                     section: c.section ?? ""))
            }
            bios.sort { rankBio($0.result) < rankBio($1.result) }

            let crits = critResults(t, pc)
            if hideFails && crits.contains(where: { $0.result == .notMet }) { continue }

            var bsig = "NA"
            if bios.contains(where: { $0.result == .met }) { bsig = "MET" }
            else if bios.contains(where: { $0.result == .notMet }) { bsig = "NOT_MET" }
            else if !bios.isEmpty { bsig = "UNKNOWN" }

            rows.append(MatchRow(trial: t, dxRelation: rel, dxBasis: basis,
                                 ageLo: lo, ageHi: hiRaw, bios: bios, crits: crits, bsig: bsig))
        }

        let rank = ["MET": 0, "UNKNOWN": 1, "NA": 2, "NOT_MET": 3]
        switch sort {
        case .relevance:
            rows.sort {
                let a = rank[$0.bsig] ?? 2, b = rank[$1.bsig] ?? 2
                if a != b { return a < b }
                return ($0.dxRelation == "exact" ? 0 : 1) < ($1.dxRelation == "exact" ? 0 : 1)
            }
        case .startDesc:   rows.sort { ($0.trial.start ?? "") > ($1.trial.start ?? "") }
        case .startAsc:    rows.sort { ($0.trial.start ?? "") < ($1.trial.start ?? "") }
        case .updatedDesc: rows.sort { ($0.trial.lastUpdate ?? "") > ($1.trial.lastUpdate ?? "") }
        }
        return rows
    }

    private func rankBio(_ r: BioResult) -> Int {
        switch r { case .met: return 0; case .unknown: return 1; case .notMet: return 2 }
    }
}
