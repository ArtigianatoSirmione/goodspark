import SwiftUI

/// Mostra una storia completa: copertina colorata, testo e fonte.
struct StoriaView: View {
    @Environment(Archivio.self) private var archivio
    let storia: Storia
    var etichetta: String? = nil
    /// Le altre buone notizie del giorno, mostrate in fondo alla storia principale
    var altre: [Storia] = []

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                copertina
                testo
                if !altre.isEmpty {
                    altreStorie
                }
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
            Illustrazione(storia: storia)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            // Leggera ombra in basso perché data e categoria restino leggibili sull'illustrazione
            LinearGradient(colors: [.clear, .black.opacity(0.35)], startPoint: .center, endPoint: .bottom)
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

    private var altreStorie: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Altre buone notizie di oggi")
                .font(.system(.title3, design: .serif, weight: .bold))
            ForEach(altre) { altra in
                NavigationLink(value: altra) { SchedaStoria(storia: altra) }
                    .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 20)
        .padding(.bottom, 110)
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

/// Una storia secondaria in formato scheda: illustrazione, area e titolo.
struct SchedaStoria: View {
    let storia: Storia

    var body: some View {
        HStack(spacing: 14) {
            Illustrazione(storia: storia, dimensioneEmoji: 40)
                .frame(width: 92, height: 92)
                .clipShape(RoundedRectangle(cornerRadius: 16))
            VStack(alignment: .leading, spacing: 6) {
                Label(Storia.nomeArea(storia.areaEffettiva), systemImage: Storia.iconaArea(storia.areaEffettiva))
                    .font(.caption.weight(.bold))
                    .textCase(.uppercase)
                    .foregroundStyle(storia.colori.last ?? .accentColor)
                Text(storia.titolo)
                    .font(.system(.headline, design: .serif))
                    .foregroundStyle(.primary)
                    .lineLimit(3)
                    .multilineTextAlignment(.leading)
                Text(storia.luogo)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
            Spacer(minLength: 0)
            Image(systemName: "chevron.right")
                .font(.footnote.weight(.semibold))
                .foregroundStyle(.tertiary)
        }
        .padding(12)
        .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 20))
        .contentShape(RoundedRectangle(cornerRadius: 20))
    }
}
