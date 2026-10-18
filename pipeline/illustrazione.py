"""Disegna un'illustrazione stilizzata su misura per la storia del giorno.

Claude disegna la scena come SVG (grafica vettoriale), che viene poi convertita
in PNG con rsvg-convert così l'app può mostrarla come una normale immagine.
Se qualcosa va storto la storia resta comunque pubblicata: l'app mostrerà
la copertina colorata con l'emoji.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import anthropic

LARGHEZZA, ALTEZZA = 1200, 800
MAX_CARATTERI_SVG = 150_000

SCHEMA_SVG = {
    "type": "object",
    "properties": {"svg": {"type": "string"}},
    "required": ["svg"],
    "additionalProperties": False,
}

ISTRUZIONI = f"""Sei l'illustratore di Goodspark, un'app che ogni giorno racconta una storia \
vera e positiva. Disegna la copertina della storia come un unico file SVG.

Stile, sempre uguale per dare un'identità all'app:
- illustrazione piatta e stilizzata, forme semplici e morbide, come un poster moderno;
- palette calda e luminosa (pesca, corallo, rosa, giallo sole, verdi e azzurri tenui), \
con al massimo un paio di sfumature delicate (linearGradient/radialGradient);
- una scena chiara che rappresenti il cuore della storia (es. un bosco per una storia \
sul bosco, un piccolo aereo nel cielo per un volo), con un cielo o uno sfondo pieno;
- persone, se servono, solo come sagome stilizzate senza tratti del viso; niente loghi.

Regole tecniche obbligatorie:
- <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGHEZZA} {ALTEZZA}" \
width="{LARGHEZZA}" height="{ALTEZZA}">;
- lo sfondo copre tutta l'area; il soggetto principale sta nella metà superiore, perché \
in basso l'app sovrappone data e categoria;
- nessun testo, nessun <text>, nessuno <script>, nessuna immagine o link esterni, \
nessun filtro o animazione;
- meno di 120 elementi in tutto, codice compatto."""


def _svg_sicuro(svg: str) -> bool:
    minuscolo = svg.lower()
    vietati = ("<script", "<text", "<image", "<foreignobject", "href=\"http", "href='http", "javascript:")
    return (
        minuscolo.lstrip().startswith("<svg")
        and minuscolo.rstrip().endswith("</svg>")
        and len(svg) <= MAX_CARATTERI_SVG
        and not any(v in minuscolo for v in vietati)
    )


def disegna_svg(storia: dict) -> str | None:
    testo = storia["en"]
    richiesta = (
        f"Storia di oggi ({storia['categoria']}, {testo['luogo']}):\n"
        f"Titolo: {testo['titolo']}\n{testo['sottotitolo']}\n\n" + "\n\n".join(testo["paragrafi"])
    )
    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model="claude-opus-5-5",
        max_tokens=64000,
        system=ISTRUZIONI,
        messages=[{"role": "user", "content": richiesta}],
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": SCHEMA_SVG},
        },
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        risposta = stream.get_final_message()

    if risposta.stop_reason in ("refusal", "max_tokens"):
        print(f"  ! illustrazione non generata ({risposta.stop_reason})")
        return None
    testo_json = next(b.text for b in reversed(risposta.content) if b.type == "text")
    svg = json.loads(testo_json)["svg"].strip()
    # A volte il modello racchiude il codice in un blocco markdown
    svg = re.sub(r"^```(?:svg|xml)?\s*|\s*```$", "", svg)
    if not _svg_sicuro(svg):
        print("  ! illustrazione scartata: SVG non valido o non sicuro")
        return None
    return svg


def crea_illustrazione(storia: dict, cartella: Path) -> str | None:
    """Genera docs/immagini/<id>.png e restituisce il percorso relativo, o None."""
    convertitore = shutil.which("rsvg-convert")
    if not convertitore:
        print("  ! rsvg-convert non disponibile: salto l'illustrazione")
        return None
    try:
        svg = disegna_svg(storia)
    except anthropic.APIError as errore:
        print(f"  ! errore durante il disegno: {errore}")
        return None
    if not svg:
        return None

    cartella.mkdir(parents=True, exist_ok=True)
    file_svg = cartella / f"{storia['id']}.svg"
    file_png = cartella / f"{storia['id']}.png"
    file_svg.write_text(svg, encoding="utf-8")
    esito = subprocess.run(
        [convertitore, "-w", str(LARGHEZZA), "-h", str(ALTEZZA), "-o", str(file_png), str(file_svg)],
        capture_output=True, text=True,
    )
    if esito.returncode != 0 or not file_png.exists() or file_png.stat().st_size < 2000:
        print(f"  ! conversione fallita: {esito.stderr.strip()[:200]}")
        file_png.unlink(missing_ok=True)
        return None
    return f"immagini/{file_png.name}"
