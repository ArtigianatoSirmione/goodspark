import SwiftUI

/// Mostra una storia completa: copertina colorata, testo e fonte.
struct StoriaView: View {
    @Environment(Archivio.self) private var archivio
    let storia: Storia
    var etichetta: String? = nil

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                copertina
                testo
            }
        }
        .ignoresSafeArea(edges: .top)
        .toolbar {
            ToolbarItemGroup {
                Button {
                    withAnimation(.spring) { archivio.cambiaPreferita(storia) }
                } label: {
                    Image(systemName: archivio.èPreferita(storia) ? "heart.fill" : "heart")
                        .contentTransition(.symbolEffect(.replace))
                }
                .accessibilityLabel(archivio.èPreferita(storia) ? Text("Togli dai preferiti") : Text("Aggiungi ai preferiti"))
                if let url = storia.urlFonte {
                    ShareLink(item: url, message: Text(storia.testoDaCondividere))
                } else {
                    ShareLink(item: storia.testoDaCondividere)
                }
            }
        }
    }

    private var copertina: some View {
        ZStack(alignment: .bottomLeading) {
            LinearGradient(colors: storia.colori, startPoint: .topLeading, endPoint: .bottomTrailing)
            Text(storia.emoji)
                .font(.system(size: 120))
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding(.bottom, 40)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 6) {
                if let etichetta {
                    Text(etichetta.uppercased())
                        .font(.caption.weight(.bold))
                        .tracking(1.2)
                        .foregroundStyle(.white.opacity(0.9))
                }
                Text(storia.nomeCategoria)
                    .font(.footnote.weight(.semibold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(.white.opacity(0.25), in: Capsule())
                    .foregroundStyle(.white)
            }
            .padding(20)
        }
        .frame(height: 340)
    }

    private var testo: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(storia.titolo)
                .font(.system(.title, design: .serif, weight: .bold))
            Text(storia.sottotitolo)
                .font(.title3)
                .foregroundStyle(.secondary)
            HStack(spacing: 14) {
                Label(storia.luogo, systemImage: "mappin.and.ellipse")
                Label("\(storia.minutiLettura) min", systemImage: "clock")
            }
            .font(.footnote)
            .foregroundStyle(.secondary)

            Divider()

            ForEach(Array(storia.paragrafi.enumerated()), id: \.offset) { _, paragrafo in
                Text(paragrafo)
                    .font(.system(.body, design: .serif))
                    .lineSpacing(5)
            }

            fonte
        }
        .padding(20)
        .padding(.bottom, 30)
    }

    private var fonte: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Fonte")
                .font(.caption.weight(.bold))
                .foregroundStyle(.secondary)
            if let url = storia.urlFonte {
                Link(destination: url) {
                    Label("Leggi l'articolo originale su \(storia.fonteNome)", systemImage: "arrow.up.right.square")
                        .font(.subheadline.weight(.medium))
                }
            } else {
                Text(storia.fonteNome).font(.subheadline)
            }
            Text("Storia raccontata con parole nostre a partire dai fatti riportati dalla fonte, con l'aiuto dell'intelligenza artificiale.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 14))
        .padding(.top, 10)
    }
}
