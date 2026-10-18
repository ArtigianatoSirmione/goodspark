import SwiftUI

/// Il testo di una storia in una lingua.
struct TestoStoria: Codable, Hashable {
    let titolo: String
    let sottotitolo: String
    let paragrafi: [String]
    let luogo: String
}

struct Storia: Codable, Identifiable, Hashable {
    let id: String
    let data: String
    let categoria: String
    let emoji: String
    let fonteNome: String
    let fonteUrl: String
    let minutiLettura: Int
    let it: TestoStoria
    let en: TestoStoria

    /// Il testo nella lingua dell'app: italiano se il telefono è in italiano, altrimenti inglese.
    var testo: TestoStoria { Bundle.main.preferredLocalizations.first == "it" ? it : en }

    var titolo: String { testo.titolo }
    var sottotitolo: String { testo.sottotitolo }
    var paragrafi: [String] { testo.paragrafi }
    var luogo: String { testo.luogo }

    var dataLeggibile: String {
        let lettore = DateFormatter()
        lettore.dateFormat = "yyyy-MM-dd"
        lettore.locale = Locale(identifier: "en_US_POSIX")
        guard let giorno = lettore.date(from: data) else { return data }
        return giorno.formatted(.dateTime.day().month(.wide).year())
    }

    var urlFonte: URL? { URL(string: fonteUrl) }

    var testoDaCondividere: String {
        "\(emoji) \(titolo)\n\n\(sottotitolo)\n\n\(String(localized: "Scoperta su Goodspark"))"
    }

    var nomeCategoria: String { Storia.nomeCategoria(categoria) }

    var colori: [Color] { Storia.coloriCategoria[categoria] ?? [.orange, .pink] }

    static func nomeCategoria(_ id: String) -> String {
        switch id {
        case "kindness": String(localized: "Gentilezza")
        case "community": String(localized: "Comunità")
        case "environment": String(localized: "Ambiente")
        case "animals": String(localized: "Animali")
        case "science": String(localized: "Scienza")
        case "health": String(localized: "Salute")
        case "innovation": String(localized: "Innovazione")
        case "culture": String(localized: "Cultura")
        case "sport": String(localized: "Sport")
        case "solidarity": String(localized: "Solidarietà")
        default: id.capitalized
        }
    }

    static let coloriCategoria: [String: [Color]] = [
        "kindness": [Color(red: 1.00, green: 0.62, blue: 0.48), Color(red: 0.98, green: 0.40, blue: 0.55)],
        "community": [Color(red: 1.00, green: 0.75, blue: 0.35), Color(red: 0.98, green: 0.50, blue: 0.30)],
        "environment": [Color(red: 0.45, green: 0.82, blue: 0.55), Color(red: 0.18, green: 0.60, blue: 0.50)],
        "animals": [Color(red: 0.95, green: 0.78, blue: 0.40), Color(red: 0.70, green: 0.50, blue: 0.30)],
        "science": [Color(red: 0.45, green: 0.65, blue: 1.00), Color(red: 0.40, green: 0.35, blue: 0.90)],
        "health": [Color(red: 0.40, green: 0.85, blue: 0.85), Color(red: 0.25, green: 0.55, blue: 0.85)],
        "innovation": [Color(red: 0.60, green: 0.50, blue: 1.00), Color(red: 0.85, green: 0.40, blue: 0.85)],
        "culture": [Color(red: 0.90, green: 0.55, blue: 0.75), Color(red: 0.55, green: 0.35, blue: 0.75)],
        "sport": [Color(red: 1.00, green: 0.55, blue: 0.30), Color(red: 0.90, green: 0.30, blue: 0.30)],
        "solidarity": [Color(red: 1.00, green: 0.55, blue: 0.60), Color(red: 0.85, green: 0.35, blue: 0.65)],
    ]
}

struct ArchivioStorie: Codable {
    let aggiornato: String?
    let storie: [Storia]
}
