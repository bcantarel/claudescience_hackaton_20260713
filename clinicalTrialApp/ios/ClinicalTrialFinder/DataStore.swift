import Foundation

// Hybrid data source: load the embedded bundle immediately (offline, no PHI leaves
// the device), then try to fetch a newer bundle from a static remote (public trial
// data only) and swap it in if available. Falls back silently to embedded.

@MainActor
final class DataStore: ObservableObject {
    @Published var bundle: AppBundle?
    @Published var loadError: String?
    @Published var refreshStatus: String = ""

    // Static hosting of the same bundle the app ships with. Public trial data only —
    // no patient information is ever sent. Update this to your CDN / Pages URL.
    private let remoteURL = URL(string:
        "https://raw.githubusercontent.com/bcantarel/claudescience_hackaton_20260713/main/clinicalTrialApp/src/data/bundle_full.json")

    func load() {
        if let b = Self.loadEmbedded() {
            bundle = b
            refreshStatus = "Bundled data (\(b.trials.count) trials)"
        } else {
            loadError = "Could not load embedded trial data."
        }
        Task { await refresh() }
    }

    static func loadEmbedded() -> AppBundle? {
        guard let url = Bundle.main.url(forResource: "bundle_full", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(AppBundle.self, from: data)
    }

    func refresh() async {
        guard let remoteURL else { return }
        do {
            let (data, resp) = try await URLSession.shared.data(from: remoteURL)
            guard (resp as? HTTPURLResponse)?.statusCode == 200 else {
                refreshStatus = bundle.map { "Bundled data (\($0.trials.count) trials)" } ?? refreshStatus
                return
            }
            let fresh = try JSONDecoder().decode(AppBundle.self, from: data)
            bundle = fresh
            refreshStatus = "Refreshed from remote (\(fresh.trials.count) trials)"
        } catch {
            refreshStatus = bundle.map { "Offline — bundled data (\($0.trials.count) trials)" } ?? "Offline"
        }
    }
}
