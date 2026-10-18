"""Genera automaticamente le buone notizie del giorno per Goodspark.

1. Raccoglie le notizie recenti dai feed RSS in fonti.py
2. Chiede a Claude di scegliere una storia per ciascuna area (Persone, Pianeta,
   Scoperte), di leggere gli articoli originali e di raccontarle con parole
   proprie in italiano e in inglese, indicando quale sarà la storia del giorno
3. Controlla il risultato, disegna le illustrazioni e aggiorna docs/storie.json,
   che l'app scarica

Uso:
    python pipeline/genera_storia.py            # genera e salva
    python pipeline/genera_storia.py --prova    # mostra solo le candidate, senza AI
    python pipeline/genera_storia.py --forza    # rigenera le storie di oggi
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
from illustrazione import crea_illustrazione

RADICE = Path(__file__).resolve().parent.parent
FILE_STORIE = RADICE / "docs" / "storie.json"
CARTELLA_IMMAGINI = RADICE / "docs" / "immagini"
MAX_STORIE_ARCHIVIO = 1000
ORE_RECENTI = 72
MAX_CANDIDATE_PER_FONTE = 15
PUNTEGGIO_MINIMO = 7
# Goodspark pubblica solo storie davvero speciali: questa è l'asticella più importante
BELLEZZA_MINIMA = 8

# Le tre aree dell'app e le categorie che contengono.
# Gli identificativi restano in inglese: l'app li mostra tradotti nella lingua del telefono.
AREE = {
    "people": ["kindness", "community", "solidarity", "sport"],
    "planet": ["environment", "animals"],
    "discoveries": ["science", "health", "innovation", "culture"],
}
CATEGORIE = [c for categorie in AREE.values() for c in categorie]
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
        "area": {"type": "string", "enum": list(AREE)},
        "indice_candidata": {"type": "integer"},
        "categoria": {"type": "string", "enum": CATEGORIE},
        "emoji": {"type": "string"},
        "punteggio_positivita": {"type": "integer"},
        "punteggio_bellezza": {"type": "integer"},
        "it": SCHEMA_TESTO,
        "en": SCHEMA_TESTO,
    },
    "required": [
        "area", "indice_candidata", "categoria", "emoji", "punteggio_positivita", "punteggio_bellezza", "it", "en",
    ],
    "additionalProperties": False,
}

SCHEMA_RISPOSTA = {
    "type": "object",
    "properties": {
        "storie": {"type": "array", "items": SCHEMA_STORIA},
        "area_principale": {"type": "string", "enum": list(AREE)},
        "motivo_scelta": {"type": "string"},
    },
    "required": ["storie", "area_principale", "motivo_scelta"],
    "additionalProperties": False,
}

ISTRUZIONI = """Sei la redazione di Goodspark, un'app italiana e internazionale che ogni giorno \
pubblica poche storie vere, belle e positive, per ricordare alle persone che nel mondo \
accadono anche tante cose buone.

Ogni giorno l'app ha tre aree, con una storia ciascuna:
- "people" (Persone): gentilezza, comunità, solidarietà, sport e traguardi personali;
- "planet" (Pianeta): ambiente, natura, animali;
- "discoveries" (Scoperte): scienza, salute, innovazione, cultura.
Una delle tre diventa la "storia del giorno", mostrata in grande: scegli la più bella e \
toccante e indica la sua area in area_principale.

Ti verrà data una lista di notizie recenti (titolo, breve estratto, link). Il tuo compito:

Goodspark pubblica solo storie VERAMENTE BELLE: storie che emozionano, che restano in \
mente, che verrebbe voglia di raccontare a qualcuno a cena. Un gesto straordinario di una \
persona comune, un'impresa che sembra impossibile, la natura che sorprende, una scoperta \
che fa sognare. NON vanno bene notizie corrette ma ordinarie: annunci istituzionali, \
leggi, convegni, bandi, dati economici, inaugurazioni, premi aziendali, dibattiti, \
iniziative generiche descritte senza persone né momenti concreti.

1. Per ogni area scegli la notizia migliore secondo questi criteri, in ordine di importanza:
   - è un fatto vero e verificabile, riportato da una fonte seria;
   - è autenticamente positiva e lascia un sorriso, commozione, meraviglia o speranza;
   - è evocativa: ha un protagonista, un'immagine forte, un momento che si può quasi vedere;
   - NON è una storia positiva solo in apparenza dentro una tragedia (guerre, morti, \
disastri, crimini, malattie gravi in primo piano), NON è politica di parte, NON è \
pubblicità di un prodotto o di un'azienda, NON è gossip;
   - preferisci storie con persone concrete; alterna storie italiane e dal resto del mondo.
   Evita storie troppo simili a quelle già pubblicate (te ne darò l'elenco) e non usare la \
stessa notizia per due aree. Se per un'area nessuna candidata è davvero adatta, salta \
quell'area: meglio due storie belle che tre mediocri.

2. Usa lo strumento web_fetch per leggere l'articolo originale di ogni notizia scelta, \
così da conoscere bene i fatti. Se un articolo non si apre, puoi provare un'altra candidata.

3. Racconta ogni storia CON PAROLE TUE due volte: in italiano (campo "it") e in inglese \
(campo "en"). Le due versioni devono riportare gli stessi fatti, ma ognuna deve suonare \
naturale e scritta direttamente in quella lingua, non tradotta parola per parola. \
Regole sul diritto d'autore, obbligatorie:
   - non copiare né tradurre frasi dell'articolo: riporta solo i fatti, con struttura, \
stile e frasi completamente originali;
   - non inserire citazioni testuali;
   - non inventare nulla: niente dettagli, nomi, numeri o dichiarazioni che non siano \
nell'articolo.

Stile, per entrambe le lingue: caldo, semplice, sincero e evocativo, mai sdolcinato o \
enfatico. Apri con una scena o un'immagine concreta che porti il lettore lì, poi racconta \
cosa è successo e perché conta, e chiudi con una frase che lasci qualcosa. Usa solo \
dettagli presenti nell'articolo: l'emozione nasce dai fatti, non dagli aggettivi. \
Titolo breve (massimo 70 caratteri), un sottotitolo di una frase, 3-5 paragrafi brevi \
(in tutto 180-280 parole). Il luogo è la città e/o il paese della storia, scritto nella \
lingua della versione (es. "Monaco di Baviera" / "Munich"). Un solo emoji adatto. \
La categoria deve appartenere all'area della storia.

punteggio_positivita va da 1 a 10: quanto la storia è vera, positiva e adatta a tutti. \
punteggio_bellezza va da 1 a 10: quanto è emozionante, evocativa e memorabile (10 = una \
storia che commuove e si racconta agli amici; 5 = una notizia corretta ma che si dimentica). \
Sii molto severo: non proporre storie con positività sotto 7 o bellezza sotto 8. È normale \
e giusto che in certi giorni un'area resti vuota."""


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
    gia_pubblicate = "\n".join(f"- {s['it']['titolo']}" for s in storie_recenti[:60]) or "(nessuna)"
    messaggi = [{
        "role": "user",
        "content": (
            f"Storie già pubblicate di recente:\n{gia_pubblicate}\n\n"
            f"Notizie candidate di oggi:\n\n{elenco}"
        ),
    }]

    # Un turno con web_fetch può fermarsi in "pause_turn": in quel caso si riprende
    for _ in range(5):
        with client.beta.messages.stream(
            model="claude-opus-5-5",
            max_tokens=64000,
            system=ISTRUZIONI,
            messages=messaggi,
            tools=[{"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 8}],
            output_config={
                "effort": "high",
                "format": {"type": "json_schema", "schema": SCHEMA_RISPOSTA},
            },
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            risposta = stream.get_final_message()
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


def motivo_scarto(storia: dict, candidate: list, indici_usati: set) -> str | None:
    """Restituisce il motivo per cui la storia va scartata, oppure None se va bene."""
    if not 0 <= storia["indice_candidata"] < len(candidate):
        return "indice candidata non valido"
    if storia["indice_candidata"] in indici_usati:
        return "notizia già usata per un'altra area"
    if storia["categoria"] not in AREE[storia["area"]]:
        return f"categoria '{storia['categoria']}' fuori dall'area '{storia['area']}'"
    if storia["punteggio_positivita"] < PUNTEGGIO_MINIMO:
        return f"positività troppo bassa ({storia['punteggio_positivita']})"
    if storia["punteggio_bellezza"] < BELLEZZA_MINIMA:
        return f"non abbastanza bella ({storia['punteggio_bellezza']})"
    for lingua in LINGUE:
        testo = storia[lingua]
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


def storie_valide(risultato: dict, candidate: list, oggi: str) -> list:
    """Le storie che superano i controlli, con la storia del giorno per prima."""
    valide, indici_usati, aree_usate = [], set(), set()
    for proposta in risultato["storie"]:
        if proposta["area"] in aree_usate:
            continue
        motivo = motivo_scarto(proposta, candidate, indici_usati)
        if motivo:
            print(f"  Scartata ({proposta['area']}): {motivo}")
            continue
        indici_usati.add(proposta["indice_candidata"])
        aree_usate.add(proposta["area"])
        scelta = candidate[proposta["indice_candidata"]]
        testi = {lingua: pulisci_testo(proposta[lingua]) for lingua in LINGUE}
        parole = sum(len(p.split()) for p in testi["it"]["paragrafi"])
        valide.append({
            "id": f"{oggi}-{proposta['area']}",
            "data": oggi,
            "area": proposta["area"],
            "principale": False,
            "categoria": proposta["categoria"],
            "emoji": proposta["emoji"].strip(),
            "fonte_nome": scelta["fonte"],
            "fonte_url": scelta["link"],
            "minuti_lettura": max(1, round(parole / 200)),
            **testi,
        })
    if valide:
        # La storia del giorno è quella scelta da Claude, se è stata accettata
        principale = next((s for s in valide if s["area"] == risultato["area_principale"]), valide[0])
        principale["principale"] = True
        valide.sort(key=lambda s: not s["principale"])
    return valide


def aggiungi_illustrazioni(archivio: list, oggi: str) -> None:
    for storia in archivio:
        if storia["data"] != oggi or storia.get("immagine"):
            continue
        print(f"Disegno l'illustrazione di '{storia['it']['titolo']}'...")
        immagine = crea_illustrazione(storia, CARTELLA_IMMAGINI)
        if immagine:
            storia["immagine"] = immagine
            salva_archivio(archivio)
            print(f"  Illustrazione salvata: {immagine}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prova", action="store_true", help="solo raccolta, senza AI")
    parser.add_argument("--forza", action="store_true", help="rigenera le storie di oggi")
    args = parser.parse_args()

    oggi = adesso_italia().date().isoformat()
    archivio = carica_archivio()
    gia_oggi = any(s["data"] == oggi for s in archivio)

    if gia_oggi and not args.forza:
        if not args.prova:
            print(f"Le storie del {oggi} esistono già: completo le illustrazioni mancanti.")
            aggiungi_illustrazioni(archivio, oggi)
        return 0
    if args.forza:
        archivio = [s for s in archivio if s["data"] != oggi]

    print("Raccolgo le notizie...")
    candidate = raccogli_candidate({s["fonte_url"] for s in archivio})
    print(f"Totale candidate: {len(candidate)}")
    if args.prova:
        for c in candidate[:10]:
            print(f"- [{c['fonte']}] {c['titolo']}")
        return 0
    if not candidate:
        print("Nessuna notizia raccolta: oggi restano le storie precedenti.")
        return 0

    print("Chiedo a Claude di scegliere e scrivere le storie...")
    risultato = scegli_e_scrivi(candidate, archivio)
    nuove = storie_valide(risultato, candidate, oggi)
    if not nuove:
        # Meglio non pubblicare che pubblicare qualcosa di sbagliato: l'app
        # continuerà a mostrare le ultime storie valide.
        print("Nessuna storia ha superato i controlli.")
        return 0

    archivio = nuove + archivio
    salva_archivio(archivio)
    for storia in nuove:
        segno = "★" if storia["principale"] else "·"
        print(f"{segno} [{storia['area']}] {storia['emoji']} {storia['it']['titolo']}")
    print(f"Motivo: {risultato['motivo_scelta']}")
    aggiungi_illustrazioni(archivio, oggi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
