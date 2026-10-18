# Goodspark

Un'app per iPhone, in italiano e in inglese, che ogni giorno mostra una storia vera e positiva, scelta e scritta in automatico.

## Come funziona

```
ogni mattina (GitHub Actions, gratis)
  └─ pipeline/genera_storia.py
       1. legge le notizie recenti da fonti affidabili (pipeline/fonti.py)
       2. Claude sceglie la più bella, legge l'articolo e la racconta con parole proprie in italiano e in inglese
       3. controlli automatici: positività ≥ 7/10, lunghezza giusta, niente doppioni
       4. salva in docs/storie.json  →  pubblicato su GitHub Pages
                                          ↓
                                  l'app lo scarica
```

Se un giorno nessuna notizia supera i controlli, non viene pubblicato nulla e l'app continua a mostrare l'ultima storia valida.

## Cartelle

- `pipeline/`: il programma che genera la storia
- `.github/workflows/`: l'automazione giornaliera
- `docs/storie.json`: l'archivio delle storie, che l'app legge
- `app/`: l'app iOS (apri `app/Goodspark.xcodeproj` con Xcode)

## Messa in funzione (una volta sola)

1. **Installa Xcode** dal Mac App Store (è gratuito).
2. **Crea un repository GitHub** chiamato `goodspark` e caricaci questa cartella.
3. **Chiave Anthropic**: creala su console.anthropic.com, poi su GitHub vai in
   Settings → Secrets and variables → Actions → New repository secret,
   con nome `ANTHROPIC_API_KEY`.
4. **GitHub Pages**: in Settings → Pages scegli "Deploy from a branch", branch `main`, cartella `/docs`.
5. **Prima storia**: in Actions → "Storia del giorno" → Run workflow.
6. L'app legge le storie da `https://artigianatosirmione.github.io/goodspark/storie.json` (vedi `app/Goodspark/Modello/Configurazione.swift`).

Costo stimato dell'AI: qualche centesimo al giorno.

## Provare la pipeline sul Mac

```bash
pip install -r pipeline/requirements.txt
python pipeline/genera_storia.py --prova    # solo raccolta notizie, gratis
python pipeline/genera_storia.py            # genera davvero (serve ANTHROPIC_API_KEY)
```
