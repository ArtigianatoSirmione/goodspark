import SwiftUI

struct ArchivioView: View {
    @Environment(Archivio.self) private var archivio
    @State private var ricerca = ""
    @State private var categoria: String?

    private var categorie: [String] {
        Array(Set(archivio.storie.map(\.categoria))).sorted()
    }

    private var storieFiltrate: [Storia] {
        archivio.storie.filter { storia in
            (categoria == nil || storia.categoria == categoria) &&
            (ricerca.isEmpty
                || storia.titolo.localizedCaseInsensitiveContains(ricerca)
                || storia.luogo.localizedCaseInsensitiveContains(ricerca)
                || storia.sottotitolo.localizedCaseInsensitiveContains(ricerca))
        }
    }

    var body: some View {
        NavigationStack {
            List {
                if categorie.count > 1 {
                    filtri
                        .listRowInsets(EdgeInsets())
                        .listRowBackground(Color.clear)
                }
                ForEach(storieFiltrate) { storia in
                    NavigationLink(value: storia) { RigaStoria(storia: storia) }
                }
            }
            .navigationTitle("Archivio")
            .searchable(text: $ricerca, prompt: "Cerca una storia o un luogo")
            .navigationDestination(for: Storia.self) { StoriaView(storia: $0, etichetta: $0.dataLeggibile) }
            .refreshable { await archivio.aggiorna() }
            .overlay {
                if storieFiltrate.isEmpty {
                    ContentUnavailableView.search
                }
            }
        }
    }

    private var filtri: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                Chip(testo: String(localized: "Tutte"), selezionato: categoria == nil) { categoria = nil }
                ForEach(categorie, id: \.self) { nome in
                    Chip(testo: Storia.nomeCategoria(nome), selezionato: categoria == nome) { categoria = nome }
                }
            }
            .padding(.horizontal, 4)
            .padding(.vertical, 6)
        }
    }
}

private struct Chip: View {
    let testo: String
    let selezionato: Bool
    let azione: () -> Void

    var body: some View {
        Button(action: azione) {
            Text(verbatim: testo)
                .font(.subheadline.weight(.medium))
                .padding(.horizontal, 14)
                .padding(.vertical, 7)
                .background(selezionato ? Color.accentColor : Color.secondary.opacity(0.15), in: Capsule())
                .foregroundStyle(selezionato ? .white : .primary)
        }
        .buttonStyle(.plain)
    }
}

struct RigaStoria: View {
    let storia: Storia

    var body: some View {
        HStack(spacing: 14) {
            Text(storia.emoji)
                .font(.title)
                .frame(width: 56, height: 56)
                .background(
                    LinearGradient(colors: storia.colori, startPoint: .topLeading, endPoint: .bottomTrailing),
                    in: RoundedRectangle(cornerRadius: 14)
                )
            VStack(alignment: .leading, spacing: 4) {
                Text(storia.titolo)
                    .font(.headline)
                    .lineLimit(2)
                Text("\(storia.dataLeggibile) · \(storia.luogo)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
        .padding(.vertical, 4)
    }
}
