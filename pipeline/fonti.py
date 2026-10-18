"""Fonti RSS da cui la pipeline raccoglie le notizie candidate.

Si possono aggiungere o togliere fonti liberamente: se un feed non risponde
viene semplicemente saltato.
"""

FONTI = [
    # Italiane
    {"nome": "Italia che Cambia", "url": "https://www.italiachecambia.org/feed/"},
    {"nome": "Vita", "url": "https://www.vita.it/feed/"},
    {"nome": "ANSA", "url": "https://www.ansa.it/sito/ansait_rss.xml"},
    {"nome": "ANSA Scienza", "url": "https://www.ansa.it/canale_scienza_tecnica/notizie/scienzaetecnica_rss.xml"},
    {"nome": "ANSA Ambiente", "url": "https://www.ansa.it/canale_ambiente/notizie/ambiente_rss.xml"},
    # Internazionali dedicate alle buone notizie
    {"nome": "Good News Network", "url": "https://www.goodnewsnetwork.org/feed/"},
    {"nome": "Positive News", "url": "https://www.positive.news/feed/"},
    {"nome": "Reasons to be Cheerful", "url": "https://reasonstobecheerful.world/feed/"},
    {"nome": "The Optimist Daily", "url": "https://www.optimistdaily.com/feed/"},
]
