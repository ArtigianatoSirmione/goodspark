import SwiftUI

/// L'illustrazione su misura della storia; finché non è scaricata (o se manca)
/// mostra la sfumatura della categoria con l'emoji.
struct Illustrazione: View {
    let storia: Storia
    var dimensioneEmoji: CGFloat = 120

    var body: some View {
        ZStack {
            LinearGradient(colors: storia.colori, startPoint: .topLeading, endPoint: .bottomTrailing)
            if let url = storia.urlImmagine {
                AsyncImage(url: url, transaction: Transaction(animation: .easeOut(duration: 0.3))) { fase in
                    if let immagine = fase.image {
                        immagine.resizable().scaledToFill()
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

    private var emoji: some View {
        Text(storia.emoji).font(.system(size: dimensioneEmoji))
    }
}
