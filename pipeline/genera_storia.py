"""Genera automaticamente la buona notizia del giorno per Goodspark.

1. Raccoglie le notizie recenti dai feed RSS in fonti.py
2. Chiede a Claude di scegliere la più bella e verificabile, di leggere
   l'articolo originale e di raccontarla con parole proprie in italiano e in inglese
3. Controlla il risultato e lo aggiunge a docs/storie.json, che l'app scarica

Uso:
    python pipeline/genera_storia.py            # genera e salva
    python pipeline/genera_storia.py --prova    # mostra solo le candidate, senza AI
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic
import feedparser

from fonti import FONTI

RADICE = Path(__file__).resolve().parent.parent
FILE_STORIE = RADICE / "docs" / "storie.json"
MAX_STORIE_ARCHIVIO = 500
ORE_RECENTI = 72
MAX_CANDIDATE_PER_FONTE = 15
PUNTEGGIO_MINIMO = 7

# Identificativi delle categorie: l'app li mostra tradotti nella lingua del telefono
CATEGORIE = [
    "kindness", "community", "environment", "animals", "science",
    "health", "innovation", "culture", "sport", "solidarity",
]
LINGUE = ["it", "en"]

SCHEMA_TESTO = {
    "type": "object",
    "properties": {
        "titolo": {"type": "string"},
        "sottotitolo": {"type": "string"},
        "paragrafi": {"type": "array", "items": {"type": "string"}},
        "luogo": {"type": "string"},
    },
    "required": ["titolo", "sottotitolo", "paragrafi", "luogo"],
    "additionalProperties": False,
}

SCHEMA_STORIA = {
    "type": "object",
    "properties": {
        "trovata": {
            "type": "boolean",
            "description": "false se nessuna candidata è davvero adatta",
        },
        "indice_candidata": {"type": "integer"},
        "it": SCHEMA_TESTO,
        "en": SCHEMA_TESTO,
        "categoria": {"type": "string", "enum": CATEGORIE},
        "emoji": {"type": "string"},
        "punteggio_positivita": {"type": "integer"},
        "motivo_scelta": {"type": "string"},
    },
    "required": [
        "trovata", "indice_candidata", "it", "en", "categoria", "emoji", "punteggio_positivita", "motivo_scelta",
    ],
    "additionalProperties": False,
}

ISTRUZIONI = """Sei la redazione di Goodspark, un'app italiana e internazionale che ogni giorno pubblica UNA storia vera, \
bella e positiva, per ricordare alle persone che nel mondo accadono anche tante cose buone.

Ti verrà data una lista di notizie recenti (titolo, breve estratto, link). Il tuo compito:

1. Scegli la notizia migliore secondo questi criteri, in ordine di importanza:
   - è un fatto vero e verificabile, riportato da una fonte seria;
   - è autenticamente positiva e lascia un sorriso o speranza: gentilezza, solidarietà, \
scoperte, natura che si riprende, comunità che si aiutano, traguardi personali;
   - NON è una storia positiva solo in apparenza dentro una tragedia (guerre, morti, \
disastri, crimini, malattie gravi in primo piano), NON è politica di parte, NON è \
pubblicità di un prodotto o di un'azienda, NON è gossip;
   - preferisci storie con persone concrete; alterna storie italiane e dal resto del mondo.
   Evita storie troppo simili a quelle già pubblicate (te ne darò l'elenco).

2. Usa lo strumento web_fetch per leggere l'articolo originale della notizia scelta, \
così da conoscere bene i fatti. Se l'articolo non si apre, puoi provare un'altra candidata.

3. Racconta la storia CON PAROLE TUE due volte: in italiano (campo "it") e in inglese \
(campo "en"). Le due versioni devono riportare gli stessi fatti, ma ognuna deve suonare \
naturale e scritta direttamente in quella lingua, non tradotta parola per parola. Regole sul diritto d'autore, obbligatorie:
   - non copiare né tradurre frasi dell'articolo: riporta solo i fatti, con struttura, \
stile e frasi completamente originali;
   - non inserire citazioni testuali;
   - non inventare nulla: niente dettagli, nomi, numeri o dichiarazioni che non siano \
nell'articolo.

Stile, per entrambe le lingue: caldo, semplice, sincero, mai sdolcinato o enfatico. \
Titolo breve (massimo 70 caratteri), un sottotitolo di una frase, 3-5 paragrafi brevi \
(in tutto 180-280 parole). Il luogo è la città e/o il paese della storia, scritto nella \
lingua della versione (es. "Monaco di Baviera" / "Munich"). Un solo emoji adatto.

punteggio_positivita va da 1 a 10: quanto la storia è vera, positiva e adatta a tutti. \
Sii severo. Se nessuna candidata merita almeno 7, rispondi con trovata=false e gli altri \
campi vuoti."""


def adesso_italia() -> datetime:
    return datetime.now(ZoneInfo("Europe/Rome"))


def carica_archivio() -> list:
    if FILE_STORIE.exists():
        return json.loads(FILE_STORIE.read_text(encoding="utf-8")).get("storie", [])
    return []


def salva_archivio(storie: list) -> None:
    FILE_STORIE.parent.mkdir(parents=True, exist_ok=True)
    dati = {
        "aggiornato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "storie": storie[:MAX_STORIE_ARCHIVIO],
    }
    FILE_STORIE.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def raccogli_candidate(link_gia_usati: set) -> list:
    limite = datetime.now(timezone.utc) - timedelta(hours=ORE_RECENTI)
    candidate = []
    for fonte in FONTI:
        try:
            feed = feedparser.parse(fonte["url"], agent="GoodsparkBot/1.0")
        except Exception as errore:  # un feed rotto non deve fermare tutto
            print(f"  ! {fonte['nome']}: {errore}")
            continue
        voci = 0
        for voce in feed.entries:
            link = voce.get("link", "")
            if not link or link in link_gia_usati:
                continue
            data = voce.get("published_parsed") or voce.get("updated_parsed")
            if data and datetime(*data[:6], tzinfo=timezone.utc) < limite:
                continue
            estratto = voce.get("summary", "")
            # Gli estratti RSS spesso contengono HTML: teniamo solo il testo, breve
            estratto = " ".join(html.unescape(_senza_tag(estratto)).split())[:400]
            candidate.append({
                "fonte": fonte["nome"],
                "titolo": voce.get("title", "").strip(),
                "estratto": estratto,
                "link": link,
            })
            voci += 1
            if voci >= MAX_CANDIDATE_PER_FONTE:
                break
        print(f"  {fonte['nome']}: {voci} notizie")
    return candidate


def _senza_tag(testo: str) -> str:
    risultato, dentro = [], False
    for carattere in testo:
        if carattere == "<":
            dentro = True
        elif carattere == ">":
            dentro = False
            risultato.append(" ")
        elif not dentro:
            risultato.append(carattere)
    return "".join(risultato)


def scegli_e_scrivi(candidate: list, storie_recenti: list) -> dict:
    client = anthropic.Anthropic()

    elenco = "\n\n".join(
        f"[{i}] {c['titolo']}\nFonte: {c['fonte']}\nEstratto: {c['estratto']}\nLink: {c['link']}"
        for i, c in enumerate(candidate)
    )
    gia_pubblicate = "\n".join(f"- {s['it']['titolo']}" for s in storie_recenti[:30]) or "(nessuna)"
    messaggi = [{
        "role": "user",
        "content": (
            f"Storie già pubblicate di recente:\n{gia_pubblicate}\n\n"
            f"Notizie candidate di oggi:\n\n{elenco}"
        ),
    }]

    # Un turno con web_fetch può fermarsi in "pause_turn": in quel caso si riprende
    for _ in range(5):
        risposta = client.beta.messages.create(
            model="claude-opus-5-5",
            max_tokens=16000,
            system=ISTRUZIONI,
            messages=messaggi,
            tools=[{"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 4}],
            output_config={
                "effort": "high",
                "format": {"type": "json_schema", "schema": SCHEMA_STORIA},
            },
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if risposta.stop_reason != "pause_turn":
            break
        messaggi.append({"role": "assistant", "content": risposta.content})
    else:
        raise RuntimeError("Il modello non ha concluso dopo 5 riprese")

    if risposta.stop_reason == "refusal":
        raise RuntimeError(f"Richiesta rifiutata: {risposta.stop_details}")
    if risposta.stop_reason == "max_tokens":
        raise RuntimeError("Risposta troncata (max_tokens)")

    testo = next(b.text for b in reversed(risposta.content) if b.type == "text")
    return json.loads(testo)


def valida(risultato: dict, candidate: list) -> str | None:
    """Restituisce il motivo per cui la storia va scartata, oppure None se va bene."""
    if not risultato["trovata"]:
        return "nessuna candidata adatta oggi"
    if not 0 <= risultato["indice_candidata"] < len(candidate):
        return "indice candidata non valido"
    if risultato["punteggio_positivita"] < PUNTEGGIO_MINIMO:
        return f"punteggio troppo basso ({risultato['punteggio_positivita']})"
    for lingua in LINGUE:
        testo = risultato[lingua]
        parole = sum(len(p.split()) for p in testo["paragrafi"])
        if not 120 <= parole <= 400:
            return f"lunghezza anomala in '{lingua}' ({parole} parole)"
        if not testo["titolo"].strip():
            return f"titolo vuoto in '{lingua}'"
    return None


def pulisci_testo(testo: dict) -> dict:
    return {
        "titolo": testo["titolo"].strip(),
        "sottotitolo": testo["sottotitolo"].strip(),
        "paragrafi": [p.strip() for p in testo["paragrafi"] if p.strip()],
        "luogo": testo["luogo"].strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prova", action="store_true", help="solo raccolta, senza AI")
    parser.add_argument("--forza", action="store_true", help="genera anche se oggi c'è già")
    args = parser.parse_args()

    oggi = adesso_italia().date().isoformat()
    archivio = carica_archivio()
    if not args.forza and archivio and archivio[0]["data"] == oggi:
        print(f"La storia del {oggi} esiste già, niente da fare.")
        return 0

    print("Raccolgo le notizie...")
    candidate = raccogli_candidate({s["fonte_url"] for s in archivio})
    print(f"Totale candidate: {len(candidate)}")
    if args.prova:
        for c in candidate[:10]:
            print(f"- [{c['fonte']}] {c['titolo']}")
        return 0
    if not candidate:
        print("Nessuna notizia raccolta: oggi resta la storia precedente.")
        return 0

    print("Chiedo a Claude di scegliere e scrivere la storia...")
    risultato = scegli_e_scrivi(candidate, archivio)
    motivo = valida(risultato, candidate)
    if motivo:
        # Meglio non pubblicare che pubblicare qualcosa di sbagliato: l'app
        # continuerà a mostrare l'ultima storia valida.
        print(f"Storia scartata: {motivo}")
        return 0

    scelta = candidate[risultato["indice_candidata"]]
    testi = {lingua: pulisci_testo(risultato[lingua]) for lingua in LINGUE}
    paragrafi = testi["it"]["paragrafi"]
    storia = {
        "id": oggi,
        "data": oggi,
        "categoria": risultato["categoria"],
        "emoji": risultato["emoji"].strip(),
        "fonte_nome": scelta["fonte"],
        "fonte_url": scelta["link"],
        "minuti_lettura": max(1, round(sum(len(p.split()) for p in paragrafi) / 200)),
        **testi,
    }
    archivio = [s for s in archivio if s["id"] != oggi]
    archivio.insert(0, storia)
    salva_archivio(archivio)
    print(f"Pubblicata: {storia['emoji']} {storia['it']['titolo']} / {storia['en']['titolo']}")
    print(f"Motivo: {risultato['motivo_scelta']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
