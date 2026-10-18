import SwiftUI

struct ImpostazioniView: View {
    @AppStorage("promemoriaAttivo") private var promemoriaAttivo = false
    @AppStorage("promemoriaOra") private var ora = 8
    @AppStorage("promemoriaMinuti") private var minuti = 0
    @State private var permessoNegato = false

    private var orario: Binding<Date> {
        Binding {
            Calendar.current.date(from: DateComponents(hour: ora, minute: minuti)) ?? .now
        } set: { nuovo in
            let componenti = Calendar.current.dateComponents([.hour, .minute], from: nuovo)
            ora = componenti.hour ?? 8
            minuti = componenti.minute ?? 0
        }
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Toggle("Promemoria giornaliero", isOn: $promemoriaAttivo)
                    if promemoriaAttivo {
                        DatePicker("Orario", selection: orario, displayedComponents: .hourAndMinute)
                    }
                } header: {
                    Text("Notifiche")
                } footer: {
                    if permessoNegato {
                        Text("Le notifiche sono disattivate: puoi attivarle da Impostazioni › Notifiche.")
                    } else {
                        Text("Ogni giorno ti ricordiamo che c'è una nuova buona notizia.")
                    }
                }

                Section("Come nascono le storie") {
                    Text("Ogni mattina selezioniamo una notizia vera e positiva da fonti giornalistiche affidabili e la raccontiamo con parole nostre, con l'aiuto dell'intelligenza artificiale. In fondo a ogni storia trovi sempre il link all'articolo originale.")
                        .font(.callout)
                }

                Section {
                    LabeledContent("Versione", value: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0")
                }
            }
            .navigationTitle("Impostazioni")
            .onChange(of: promemoriaAttivo) { aggiornaPromemoria() }
            .onChange(of: ora) { aggiornaPromemoria() }
            .onChange(of: minuti) { aggiornaPromemoria() }
        }
    }

    private func aggiornaPromemoria() {
        guard promemoriaAttivo else {
            Promemoria.disattiva()
            return
        }
        Task {
            let riuscito = await Promemoria.attiva(ora: ora, minuti: minuti)
            permessoNegato = !riuscito
            if !riuscito { promemoriaAttivo = false }
        }
    }
}
