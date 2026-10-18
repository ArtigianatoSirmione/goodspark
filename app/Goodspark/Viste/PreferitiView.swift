import SwiftUI

struct PreferitiView: View {
    @Environment(Archivio.self) private var archivio

    var body: some View {
        NavigationStack {
            List(archivio.storiePreferite) { storia in
                NavigationLink(value: storia) { RigaStoria(storia: storia) }
                    .swipeActions {
                        Button("Togli", systemImage: "heart.slash", role: .destructive) {
                            archivio.cambiaPreferita(storia)
                        }
                    }
            }
            .navigationTitle("Preferiti")
            .navigationDestination(for: Storia.self) { StoriaView(storia: $0, etichetta: $0.dataLeggibile) }
            .overlay {
                if archivio.storiePreferite.isEmpty {
                    ContentUnavailableView(
                        "Ancora nessun preferito",
                        systemImage: "heart",
                        description: Text("Tocca il cuore su una storia per ritrovarla qui quando ti serve un sorriso.")
                    )
                }
            }
        }
    }
}
