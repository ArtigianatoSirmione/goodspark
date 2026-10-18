import SwiftUI

struct OggiView: View {
    @Environment(Archivio.self) private var archivio

    var body: some View {
        NavigationStack {
            Group {
                if let storia = archivio.storiaDiOggi {
                    StoriaView(storia: storia, etichetta: storia.dataLeggibile)
                        .refreshable { await archivio.aggiorna() }
                } else {
                    ContentUnavailableView {
                        Label("Nessuna storia, per ora", systemImage: "sun.horizon")
                    } description: {
                        Text("Controlla la connessione: la buona notizia di oggi arriverà presto.")
                    } actions: {
                        Button("Riprova") { Task { await archivio.aggiorna() } }
                            .buttonStyle(.borderedProminent)
                    }
                }
            }
        }
    }
}
