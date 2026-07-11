import Foundation

// Codable models for the embedded/remote bundle. Only the fields the app uses
// are declared; JSONDecoder ignores the rest. Mirrors src/05_build_bundle.py output.

struct AppBundle: Decodable {
    let version: String?
    let counts: Counts?
    let trials: [Trial]
    let ancestors: [String: [String]]
    let dxOptions: [DxOption]
    let geneCache: [String: GeneEntry]
    let genes: [String]
}

struct Counts: Decodable {
    let searchable: Int?
    let stale: Int?
}

struct DxOption: Decodable, Hashable {
    let code: String
    let name: String
}

struct Trial: Decodable, Identifiable {
    var id: String { nct }
    let nct: String
    let title: String?
    let status: String?
    let minAge: String?
    let maxAge: String?
    let sex: String?
    let phase: [String]?
    let enroll: Int?
    let start: String?
    let primaryComp: String?
    let lastUpdate: String?
    let dxCodes: [String]
    let stale: Bool?
    let staleWhy: String?
    let url: String?
    let elig: String?
}

struct GeneEntry: Decodable {
    let direction: String
    let confidence: String?
    let cited_span: String?
    let section: String?
}
