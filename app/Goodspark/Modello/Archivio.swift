import Foundation
import Observation

/// Scarica le storie, le tiene in cache per l'uso offline e gestisce i preferiti.
@MainActor
@Observable
final class Archivio {
    private(set) var storie: [Storia] = []
    private(set) var preferiti: Set<String>
    private(set) var erroreRete = false

    private let chiavePreferiti = "preferiti"
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    private var fileCache: URL {
        URL.applicationSupportDirectory.appending(path: "storie.json")
    }

    init() {
        preferiti = Set(UserDefaults.standard.stringArray(forKey: chiavePreferiti) ?? [])
        storie = caricaDaCache() ?? caricaEsempi()
    }

    var storiaDiOggi: Storia? { storie.first }

    var storiePreferite: [Storia] { storie.filter { preferiti.contains($0.id) } }

    func aggiorna() async {
        do {
            var richiesta = URLRequest(url: Configurazione.urlStorie)
            richiesta.cachePolicy = .reloadIgnoringLocalCacheData
            let (dati, risposta) = try await URLSession.shared.data(for: richiesta)
            guard (risposta as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
            let archivio = try decoder.decode(ArchivioStorie.self, from: dati)
            guard !archivio.storie.isEmpty else { return }
            storie = archivio.storie
            erroreRete = false
            try? FileManager.default.createDirectory(at: fileCache.deletingLastPathComponent(), withIntermediateDirectories: true)
            try? dati.write(to: fileCache, options: .atomic)
        } catch {
            erroreRete = true
        }
    }

    func èPreferita(_ storia: Storia) -> Bool { preferiti.contains(storia.id) }

    func cambiaPreferita(_ storia: Storia) {
        if preferiti.contains(storia.id) {
            preferiti.remove(storia.id)
        } else {
            preferiti.insert(storia.id)
        }
        UserDefaults.standard.set(Array(preferiti), forKey: chiavePreferiti)
    }

    private func caricaDaCache() -> [Storia]? {
        guard let dati = try? Data(contentsOf: fileCache),
              let archivio = try? decoder.decode(ArchivioStorie.self, from: dati),
              !archivio.storie.isEmpty else { return nil }
        return archivio.storie
    }

    private func caricaEsempi() -> [Storia] {
        guard let url = Bundle.main.url(forResource: "esempi", withExtension: "json"),
              let dati = try? Data(contentsOf: url),
              let archivio = try? decoder.decode(ArchivioStorie.self, from: dati) else { return [] }
        return archivio.storie
    }
}
