"""Análisis de frecuencias léxicas con stopwords embebidas (FR-017, research.md D6)."""

from __future__ import annotations

import re
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

_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)


def word_frequencies(
    text: str, lang: str = "es", min_len: int = 4, top: int = 50,
    exclusions: set[str] | None = None,
) -> list[dict]:
    """Frecuencias del corpus: stopwords por idioma + longitud mínima (FR-017)
    + exclusiones del investigador, p. ej. marcas de transcripción (FR-048)."""
    stopwords = STOPWORDS_ES if lang == "es" else STOPWORDS_EN
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
