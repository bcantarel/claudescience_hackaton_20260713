import SwiftUI

struct ContentView: View {
    @StateObject private var store = DataStore()

    // patient inputs
    @State private var dx = "LUAD"
    @State private var ageText = "60"
    @State private var sex = "FEMALE"
    @State private var geneState: [String: String] = ["EGFR": "altered"]
    @State private var sort: SortMode = .relevance
    @State private var hideStale = true

    private var dxOptions: [DxOption] {
        (store.bundle?.dxOptions ?? []).sorted { $0.name < $1.name }
    }
    private var genes: [String] { store.bundle?.genes ?? [] }

    private var rows: [MatchRow] {
        guard let b = store.bundle, let age = Int(ageText) else { return [] }
        return Matcher(bundle: b).run(dx: dx, age: age, sex: sex,
                                      genes: geneState, hideStale: hideStale, sort: sort)
    }

    var body: some View {
        NavigationStack {
            Group {
                if store.bundle == nil {
                    VStack(spacing: 12) {
                        ProgressView()
                        Text(store.loadError ?? "Loading trial data…")
                            .foregroundStyle(.secondary)
                    }
                } else {
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 14) {
                            disclaimer
                            inputCard
                            summaryLine
                            ForEach(rows) { TrialCard(row: $0, patientGenes: geneState) }
                            if rows.isEmpty {
                                Text("No trials matched. Broaden the diagnosis or adjust age.")
                                    .font(.footnote).foregroundStyle(.secondary).padding(.top)
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("ClinicalTrialFinder")
            .navigationBarTitleDisplayMode(.inline)
        }
        .onAppear { if store.bundle == nil { store.load() } }
    }

    private var disclaimer: some View {
        Text("Candidate list for physician review only — not an eligibility determination. Gene matching is at the gene level, not variant level. Always read the cited source sentence and verify on ClinicalTrials.gov.")
            .font(.caption2)
            .foregroundStyle(Color(red: 0.90, green: 0.81, blue: 0.58))
            .padding(10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(red: 0.16, green: 0.14, blue: 0.09))
            .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var inputCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Diagnosis").font(.caption).foregroundStyle(.secondary)
                Spacer()
                Picker("Diagnosis", selection: $dx) {
                    ForEach(dxOptions, id: \.code) { Text($0.name).tag($0.code) }
                }.labelsHidden().pickerStyle(.menu)
            }
            HStack {
                Text("Age").font(.caption).foregroundStyle(.secondary)
                Spacer()
                TextField("Age", text: $ageText)
                    .keyboardType(.numberPad).multilineTextAlignment(.trailing).frame(width: 80)
            }
            HStack {
                Text("Sex").font(.caption).foregroundStyle(.secondary)
                Spacer()
                Picker("Sex", selection: $sex) {
                    Text("Female").tag("FEMALE"); Text("Male").tag("MALE")
                }.labelsHidden().pickerStyle(.segmented).frame(width: 180)
            }
            Text("Gene profile (tap to cycle: — → altered → wild-type)")
                .font(.caption).foregroundStyle(.secondary)
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 6), count: 3), spacing: 6) {
                ForEach(genes, id: \.self) { g in GeneChip(gene: g, state: geneState[g]) { cycle(g) } }
            }
            HStack {
                Text("Sort").font(.caption).foregroundStyle(.secondary)
                Spacer()
                Picker("Sort", selection: $sort) {
                    ForEach(SortMode.allCases) { Text($0.rawValue).tag($0) }
                }.labelsHidden().pickerStyle(.menu)
            }
            Toggle(isOn: $hideStale) {
                Text("Hide likely-stale trials").font(.caption)
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var summaryLine: some View {
        let met = rows.filter { $0.bsig == "MET" }.count
        let notMet = rows.filter { $0.bsig == "NOT_MET" }.count
        let geneDesc = geneState.isEmpty ? "none" :
            geneState.map { "\($0.key)=\($0.value)" }.sorted().joined(separator: ", ")
        return VStack(alignment: .leading, spacing: 2) {
            Text("\(rows.count) candidate trials · \(dx), age \(ageText), \(sex.capitalized)")
                .font(.footnote)
            Text("genes: \(geneDesc)  ·  \(met) biomarker-MET, \(notMet) NOT-MET (surfaced, not excluded)")
                .font(.caption2).foregroundStyle(.secondary)
            Text(store.refreshStatus).font(.caption2).foregroundStyle(.tertiary)
        }
    }

    private func cycle(_ g: String) {
        switch geneState[g] {
        case nil: geneState[g] = "altered"
        case "altered": geneState[g] = "wildtype"
        default: geneState[g] = nil
        }
    }
}

struct GeneChip: View {
    let gene: String
    let state: String?
    let tap: () -> Void
    var body: some View {
        Button(action: tap) {
            VStack(spacing: 1) {
                Text(gene).font(.caption).bold()
                Text(state == "altered" ? "ALTERED" : state == "wildtype" ? "wild-type" : "—")
                    .font(.system(size: 9))
            }
            .frame(maxWidth: .infinity).padding(.vertical, 6)
            .background(bg).foregroundStyle(fg)
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(border, lineWidth: 1))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }.buttonStyle(.plain)
    }
    private var bg: Color {
        state == "altered" ? Color.green.opacity(0.18) :
        state == "wildtype" ? Color.blue.opacity(0.18) : Color(.tertiarySystemBackground)
    }
    private var fg: Color { .primary }
    private var border: Color {
        state == "altered" ? .green : state == "wildtype" ? .blue : Color(.separator)
    }
}

struct TrialCard: View {
    let row: MatchRow
    let patientGenes: [String: String]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                if let urlStr = row.trial.url, let url = URL(string: urlStr) {
                    Link(row.trial.title ?? row.trial.nct, destination: url)
                        .font(.subheadline).bold()
                } else {
                    Text(row.trial.title ?? row.trial.nct).font(.subheadline).bold()
                }
                Spacer()
                Text(row.trial.nct).font(.caption2).monospaced().foregroundStyle(.secondary)
            }
            // detail chips
            FlowChips(items: chips)
            // biomarker rows
            if !row.bios.isEmpty {
                Divider()
                ForEach(row.bios) { b in
                    HStack(alignment: .top, spacing: 8) {
                        Badge(result: b.result)
                        VStack(alignment: .leading, spacing: 2) {
                            (Text(b.gene).bold() + Text(" — \(b.why)"))
                                .font(.caption)
                            if !b.section.isEmpty {
                                Text("[\(b.section)] conf via classifier")
                                    .font(.system(size: 9)).foregroundStyle(.tertiary)
                            }
                            if !b.cite.isEmpty {
                                Text("“\(b.cite)”")
                                    .font(.caption2).italic().foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var chips: [String] {
        var c = ["dx: \(row.dxRelation) via \(row.dxBasis)",
                 "age \(row.ageLo)–\(row.ageHi.map(String.init) ?? "no cap")",
                 "sex \(row.trial.sex ?? "ALL")"]
        if let p = row.trial.phase, !p.isEmpty { c.append(p.joined(separator: "/")) }
        if let n = row.trial.enroll { c.append("n=\(n)") }
        if let s = row.trial.start { c.append("started \(s)") }
        if let u = row.trial.lastUpdate { c.append("updated \(u)") }
        if row.trial.stale == true, let w = row.trial.staleWhy { c.append("⚠ \(w)") }
        return c
    }
}

struct Badge: View {
    let result: BioResult
    var body: some View {
        Text(result.label)
            .font(.system(size: 10)).bold()
            .padding(.horizontal, 6).padding(.vertical, 2)
            .background(color.opacity(0.18))
            .foregroundStyle(color)
            .overlay(RoundedRectangle(cornerRadius: 5).stroke(color, lineWidth: 1))
            .clipShape(RoundedRectangle(cornerRadius: 5))
    }
    private var color: Color {
        switch result { case .met: return .green; case .notMet: return .red; case .unknown: return .orange }
    }
}

// Simple wrapping chip row.
struct FlowChips: View {
    let items: [String]
    var body: some View {
        FlexLayout(spacing: 6, lineSpacing: 6) {
            ForEach(items, id: \.self) { t in
                Text(t)
                    .font(.system(size: 11))
                    .padding(.horizontal, 7).padding(.vertical, 3)
                    .background(Color(.tertiarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 6))
            }
        }
    }
}

// Minimal flow layout (wraps children onto multiple lines).
struct FlexLayout: Layout {
    var spacing: CGFloat = 6
    var lineSpacing: CGFloat = 6

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxW = proposal.width ?? .infinity
        var x: CGFloat = 0, y: CGFloat = 0, lineH: CGFloat = 0
        for sv in subviews {
            let s = sv.sizeThatFits(.unspecified)
            if x + s.width > maxW && x > 0 { x = 0; y += lineH + lineSpacing; lineH = 0 }
            x += s.width + spacing
            lineH = max(lineH, s.height)
        }
        return CGSize(width: maxW == .infinity ? x : maxW, height: y + lineH)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let maxW = bounds.width
        var x: CGFloat = bounds.minX, y: CGFloat = bounds.minY, lineH: CGFloat = 0
        for sv in subviews {
            let s = sv.sizeThatFits(.unspecified)
            if x + s.width > bounds.minX + maxW && x > bounds.minX {
                x = bounds.minX; y += lineH + lineSpacing; lineH = 0
            }
            sv.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(s))
            x += s.width + spacing
            lineH = max(lineH, s.height)
        }
    }
}

#Preview { ContentView() }
