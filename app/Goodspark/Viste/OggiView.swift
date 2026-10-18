import SwiftUI

struct OggiView: View {
    @Environment(Archivio.self) private var archivio

    var body: some View {
        NavigationStack {
            Group {
                if let storia = archivio.storiaDiOggi {
                    StoriaView(storia: storia, etichetta: storia.dataLeggibile, altre: archivio.altreDiOggi)
                        .refreshable { await archivio.aggiorna() }
                        .navigationDestination(for: Storia.self) { StoriaView(storia: $0, etichetta: $0.dataLeggibile) }
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
