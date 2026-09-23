"""Análisis de frecuencias léxicas con stopwords embebidas (FR-017, research.md D6)."""

from __future__ import annotations

import re
import threading
from collections import Counter

STOPWORDS_ES = frozenset("""
a acá ahí al algo alguna algunas alguno algunos allá allí ambos ante antes aquel aquella
aquellas aquello aquellos aquí arriba así atrás aun aunque bajo bastante bien cada casi
cierta ciertas cierto ciertos como cómo con conmigo conseguimos conseguir contigo contra
cual cuál cuales cuando cuándo cuanta cuanto de dejar del demás demasiada demasiadas
demasiado demasiados dentro desde donde dónde dos el él ella ellas ello ellos en encima
entonces entre era erais éramos eran eres es esa esas ese eso esos esta está estaba
estabais estaban estabas estad estada estadas estado estados estamos estando estar
estaremos estará estarán estarás estaré estaréis estaría estaríais estaríamos estarían
estarías estas estás este estemos esto estos estoy estuve estuviera estuvierais
estuvieran estuvieras estuvieron estuviese estuvieseis estuviesen estuvieses estuvimos
estuviste estuvisteis estuvo fin fue fuera fuerais fueran fueras fueron fuese fueseis
fuesen fueses fui fuimos fuiste fuisteis ha habida habidas habido habidos habiendo
habremos habrá habrán habrás habré habréis habría habríais habríamos habrían habrías
habéis había habíais habíamos habían habías han has hasta hay haya hayamos hayan hayas
hayáis he hemos hice hicieron hizo hoy hube hubiera hubierais hubieran hubieras hubieron
hubiese hubieseis hubiesen hubieses hubimos hubiste hubisteis hubo la las le les lo los
luego más me menos mi mientras mis mucha muchas mucho muchos muy mí mía mías mío míos
nada ni no nos nosotras nosotros nuestra nuestras nuestro nuestros nunca o os otra otras
otro otros para pero poca pocas poco pocos podemos poder podría podrían puede pueden
pues que qué quien quién quienes se sea seamos sean seas segun según ser seremos será
serán serás seré seréis sería seríais seríamos serían serías si sido siempre siendo sin
sobre sois solamente solo somos son soy su sus suya suyas suyo suyos sí también tan
tanta tantas tanto tantos te tenemos tener tenga tengo tenida tenidas tenido tenidos
teniendo tenéis tenía teníais teníamos tenían tenías ti tiempo tiene tienen toda todas
todavía todo todos trabajan trabajar tras tu tus tuve tuviera tuvierais tuvieran
tuvieras tuvieron tuviese tuvieseis tuviesen tuvieses tuvimos tuviste tuvisteis tuvo
tuya tuyas tuyo tuyos tú un una unas uno unos usa usan usar usted ustedes va vamos van
varias varios vaya verdad vez vosotras vosotros voy vuestra vuestras vuestro vuestros y
ya yo él éramos ésta éstas éste éstos última últimas último últimos
""".split())

STOPWORDS_EN = frozenset("""
a about above after again against all am an and any are aren't as at be because been
before being below between both but by can can't cannot could couldn't did didn't do
does doesn't doing don't down during each few for from further had hadn't has hasn't
have haven't having he he'd he'll he's her here here's hers herself him himself his how
how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most
mustn't my myself no nor not of off on once only or other ought our ours ourselves out
over own same shan't she she'd she'll she's should shouldn't so some such than that
that's the their theirs them themselves then there there's these they they'd they'll
they're they've this those through to too under until up very was wasn't we we'd we'll
we're we've were weren't what what's when when's where where's which while who who's
whom why why's with won't would wouldn't you you'd you'll you're you've your yours
yourself yourselves
""".split())

# Portugués (corpus de colegas de Brasil): frecuencias, foco gramatical y sentimiento.
STOPWORDS_PT = frozenset("""
a à ao aos aquela aquelas aquele aqueles aquilo as às até com como da das de dela
delas dele deles depois do dos e é ela elas ele eles em entre era eram essa essas
esse esses esta está estamos estão estas estava estavam este esteja estejam estes
esteve estive estivemos estiveram eu foi fomos for foram fosse fossem fui há isso
isto já lhe lhes mais mas me mesmo meu meus minha minhas muito na não nas nem no
nos nós nossa nossas nosso nossos num numa o os ou para pela pelas pelo pelos por
qual quando que quem se seja sejam sem ser será serão seu seus só sua suas também
te tem têm temos tenho teu teus tinha tinham tu tua tuas um uma umas uns você vocês
vos ainda assim aqui ali lá então porque pois sobre tudo todo toda todos todas
cada coisa outra outro outras outros tão bem vai vou ter fazer faz fez sim né tá
aí daí gente pra pro coisas estar sendo sido havia houve
""".split())

STOPWORDS = {"es": STOPWORDS_ES, "en": STOPWORDS_EN, "pt": STOPWORDS_PT}


def detect_language(text: str) -> str:
    """Idioma probable de un corpus (es/en/pt) por sus palabras vacías más
    distintivas. Solo propone el valor inicial del selector: el investigador
    puede cambiarlo cuando quiera."""
    words = _WORD_RE.findall(text[:30000].lower())
    scores = {lang: sum(1 for w in words if w in STOPWORDS[lang] - shared)
              for lang, shared in (("es", STOPWORDS_EN | STOPWORDS_PT),
                                   ("en", STOPWORDS_ES | STOPWORDS_PT),
                                   ("pt", STOPWORDS_ES | STOPWORDS_EN))}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "es"

_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)

# ---- Foco gramatical con spaCy (FR-058) ----
# Los modelos pequeños es/en viajan dentro de los instaladores (decisión del
# investigador 2026-07-07: engordar instaladores a cambio de POS offline).
# El análisis por documento se calcula una vez y se reutiliza (analysis.py).

POS_LANGS = ("es", "en", "pt")
POS_MAP = {"verb": {"VERB"}, "noun": {"NOUN", "PROPN"}, "adj": {"ADJ"}}
MODEL_LOCK = threading.RLock()  # spaCy no garantiza uso concurrente del mismo modelo
_NLP_CACHE: dict = {}


def _get_model(lang: str):
    with MODEL_LOCK:
        if lang not in _NLP_CACHE:
            import en_core_web_sm, es_core_news_sm, pt_core_news_sm  # noqa: PLC0415

            module = {"es": es_core_news_sm, "en": en_core_web_sm, "pt": pt_core_news_sm}[lang]
            model = module.load(exclude=["parser", "ner"])
            model.max_length = 2_000_000
            _NLP_CACHE[lang] = model
        return _NLP_CACHE[lang]


def _kwic_entry(doc, start: int, end: int, window: int, offsets) -> dict:
    """Entrada de concordancia. start/end llegan en puntos de código (Python)
    y salen en unidades UTF-16, que es como cuenta el Canvas (JS)."""
    text = doc.text
    before = text[max(0, start - window):start].replace("\n", " ")
    after = text[end:end + window].replace("\n", " ")
    return {
        "doc_id": doc.id,
        "filename": doc.filename,
        "start": offsets.to_utf16(start),
        "end": offsets.to_utf16(end),
        "before": before,
        "match": text[start:end],
        "after": after,
    }


def kwic_occurrences(
    documents, query: str, lang: str = "es", pos: str = "all",
    window: int = 60, limit: int = 300,
) -> list[dict]:
    """Concordancias (Keyword In Context) de una palabra o lema en el corpus.

    En modo 'all' busca coincidencias literales (insensible a mayúsculas).
    En modo verb/noun/adj busca por LEMA (así "cantar" también encuentra
    "cantó" y "cantaba" en su forma real, con offsets exactos para saltar
    al Canvas — FR-063)."""
    from . import analysis

    query_norm = query.strip().lower()
    if not query_norm:
        return []
    results: list[dict] = []
    if pos == "all":
        pattern = re.compile(r"\b" + re.escape(query_norm) + r"\b", re.IGNORECASE)
        for doc in documents:
            offsets = analysis.OffsetMap(doc.text)
            for m in pattern.finditer(doc.text):
                if len(results) >= limit:
                    return results
                results.append(_kwic_entry(doc, m.start(), m.end(), window, offsets))
    else:
        for doc in documents:
            offsets = analysis.OffsetMap(doc.text)
            for start, end, key, lemma, word in analysis.get(doc.text, lang)["pos"]:
                if len(results) >= limit:
                    return results
                if key == pos and (lemma == query_norm or word == query_norm):
                    results.append(_kwic_entry(doc, start, end, window, offsets))
    return results


def pos_counts(
    analyses, pos: str, lang: str, min_len: int = 4, top: int = 50,
    exclusions: set[str] | None = None,
) -> list[dict]:
    """Frecuencias de lemas de una categoría gramatical sobre análisis ya
    calculados. 'cantó' y 'cantaba' cuentan como 'cantar'."""
    stopwords = STOPWORDS.get(lang, STOPWORDS_ES)
    excluded = {w.lower() for w in (exclusions or set())}
    counter: Counter = Counter()
    for data in analyses:
        for _start, _end, key, lemma, word in data["pos"]:
            if key != pos:
                continue
            if (len(lemma) < min_len or lemma in stopwords or word in stopwords
                    or lemma in excluded or word in excluded):
                continue
            counter[lemma] += 1
    return [{"word": w, "count": c} for w, c in counter.most_common(top)]


def pos_frequencies(
    text: str, lang: str, pos: str, min_len: int = 4, top: int = 50,
    exclusions: set[str] | None = None,
) -> list[dict]:
    """Frecuencias por categoría gramatical de un texto suelto."""
    from . import analysis

    return pos_counts([analysis.get(text, lang)], pos, lang, min_len, top, exclusions)


def word_frequencies(
    text: str, lang: str = "es", min_len: int = 4, top: int = 50,
    exclusions: set[str] | None = None,
) -> list[dict]:
    """Frecuencias del corpus: stopwords por idioma + longitud mínima (FR-017)
    + exclusiones del investigador, p. ej. marcas de transcripción (FR-048)."""
    stopwords = STOPWORDS.get(lang, STOPWORDS_ES)
    excluded = {w.lower() for w in (exclusions or set())}
    words = _WORD_RE.findall(text.lower())
    filtered = (
        w for w in words
        if len(w) >= min_len and w not in stopwords and w not in excluded
        and not w.isdigit()
    )
    return [
        {"word": word, "count": count}
        for word, count in Counter(filtered).most_common(top)
    ]
