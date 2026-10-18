import SwiftUI

/// L'illustrazione su misura della storia; finché non è scaricata (o se manca)
/// mostra la sfumatura della categoria con l'emoji.
struct Illustrazione: View {
    /// Larghezza / altezza delle illustrazioni generate (1200 × 1000)
    static let proporzione: CGFloat = 1.2

    let storia: Storia
    var dimensioneEmoji: CGFloat = 120
    /// Solo per la copertina: lo spazio in alto occupato da orologio e pulsanti.
    /// L'illustrazione intera sta sotto, e la fascia in alto mostra una sua versione sfocata.
    var spazioSopra: CGFloat? = nil

    var body: some View {
        // La sfumatura decide le dimensioni; il contenuto sta in overlay così non allarga la pagina.
        LinearGradient(colors: storia.colori, startPoint: .topLeading, endPoint: .bottomTrailing)
            .overlay {
                if let url = storia.urlImmagine {
                    AsyncImage(url: url, transaction: Transaction(animation: .easeOut(duration: 0.3))) { fase in
                        if let immagine = fase.image {
                            if spazioSopra != nil {
                                copertina(immagine)
                            } else {
                                immagine.resizable().scaledToFill()
                            }
                        } else {
                            emoji
                        }
                    }
                } else {
                    emoji
                }
            }
            .clipped()
            .accessibilityHidden(true)
    }

    private func copertina(_ immagine: Image) -> some View {
        // Entrambi i livelli in overlay: lo sfondo sfocato non deve ingrandire l'immagine nitida
        Color.clear
            .overlay(alignment: .top) {
                immagine.resizable().scaledToFill().blur(radius: 30)
            }
            .overlay(alignment: .bottom) {
                immagine.resizable().aspectRatio(Self.proporzione, contentMode: .fit)
                    // Bordo superiore sfumato: nessuno stacco netto con la fascia sfocata
                    .mask(LinearGradient(stops: [.init(color: .clear, location: 0), .init(color: .black, location: 0.12)],
                                         startPoint: .top, endPoint: .bottom))
            }
            .clipped()
    }

    private var emoji: some View {
        Text(storia.emoji)
            .font(.system(size: dimensioneEmoji))
            .padding(.top, spazioSopra ?? 0)
    }
}
