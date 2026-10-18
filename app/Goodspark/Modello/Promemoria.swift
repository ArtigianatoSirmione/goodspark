import Foundation
import UserNotifications

/// Promemoria giornaliero locale: "La buona notizia di oggi è pronta".
enum Promemoria {
    private static let identificativo = "goodspark-del-giorno"

    static func attiva(ora: Int, minuti: Int) async -> Bool {
        let centro = UNUserNotificationCenter.current()
        let concesso = (try? await centro.requestAuthorization(options: [.alert, .sound, .badge])) ?? false
        guard concesso else { return false }

        let contenuto = UNMutableNotificationContent()
        contenuto.title = String(localized: "La buona notizia di oggi ✨")
        contenuto.body = String(localized: "C'è una nuova storia bella che ti aspetta.")
        contenuto.sound = .default

        var orario = DateComponents()
        orario.hour = ora
        orario.minute = minuti
        let richiesta = UNNotificationRequest(
            identifier: identificativo,
            content: contenuto,
            trigger: UNCalendarNotificationTrigger(dateMatching: orario, repeats: true)
        )
        centro.removePendingNotificationRequests(withIdentifiers: [identificativo])
        do {
            try await centro.add(richiesta)
            return true
        } catch {
            return false
        }
    }

    static func disattiva() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [identificativo])
    }
}
