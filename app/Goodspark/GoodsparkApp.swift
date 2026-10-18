import SwiftUI

@main
struct GoodsparkApp: App {
    @State private var archivio = Archivio()

    var body: some Scene {
        WindowGroup {
            SchermataPrincipale()
                .environment(archivio)
                .task { await archivio.aggiorna() }
        }
    }
}

struct SchermataPrincipale: View {
    var body: some View {
        TabView {
            OggiView()
                .tabItem { Label("Oggi", systemImage: "sparkles") }
            ArchivioView()
                .tabItem { Label("Archivio", systemImage: "books.vertical.fill") }
            PreferitiView()
                .tabItem { Label("Preferiti", systemImage: "heart.fill") }
            ImpostazioniView()
                .tabItem { Label("Impostazioni", systemImage: "gearshape.fill") }
        }
        .tint(Color.accentColor)
    }
}
