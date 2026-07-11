import Foundation

// Port of the web tool's matcher (matcher.py / the HTML JS). Deterministic:
// OncoTree ancestor walk-up for diagnosis, age/sex filter, three-valued gene
// mapping. Never emits an overall eligible/ineligible verdict.

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

struct MatchRow: Identifiable {
    let id = UUID()
    let trial: Trial
    let dxRelation: String
    let dxBasis: String
    let ageLo: Int
    let ageHi: Int?        // nil = no upper cap
    let bios: [BioBasis]
    let bsig: String       // MET / NOT_MET / UNKNOWN / NA
}

enum SortMode: String, CaseIterable, Identifiable {
    case relevance = "Biomarker relevance"
    case startDesc = "Start date — newest"
    case startAsc = "Start date — oldest"
    case updatedDesc = "Recently updated"
    var id: String { rawValue }
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

    func run(dx: String, age: Int, sex: String, genes: [String: String],
             hideStale: Bool, sort: SortMode) -> [MatchRow] {
        var rows: [MatchRow] = []
        for t in bundle.trials {
            guard let (rel, basis) = dxRelation(patient: dx, trialCodes: t.dxCodes) else { continue }
            if hideStale && (t.stale ?? false) { continue }
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

            var bsig = "NA"
            if bios.contains(where: { $0.result == .met }) { bsig = "MET" }
            else if bios.contains(where: { $0.result == .notMet }) { bsig = "NOT_MET" }
            else if !bios.isEmpty { bsig = "UNKNOWN" }

            rows.append(MatchRow(trial: t, dxRelation: rel, dxBasis: basis,
                                 ageLo: lo, ageHi: hiRaw, bios: bios, bsig: bsig))
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
