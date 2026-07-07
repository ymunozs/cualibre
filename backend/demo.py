"""Proyecto de ejemplo (FR-061): entrevista ficticia precargada y codificada,
para aprender el flujo de Cua-libre sin arriesgar datos reales."""

from __future__ import annotations

from .models import Code, Document, Project, Relation, utf16_len

INTERVIEW = """Entrevistadora: ¿Cómo recuerdas tus primeros años enseñando en la escuela rural?

Docente: Llegué con mucho miedo, para ser honesta. La escuela quedaba a tres horas del pueblo y yo no conocía a nadie. Pero los niños me recibieron con una alegría que no esperaba, y eso me cambió todo.

Entrevistadora: ¿Qué papel jugaba la comunidad?

Docente: La comunidad era el corazón de la escuela. Las familias traían leña en invierno, cocinaban para las fiestas. Yo aprendí más de ellas que de cualquier manual de pedagogía.

Entrevistadora: ¿Hubo momentos difíciles?

Docente: Muchos. Cuando cerraron la escuela vecina sentí una pena enorme, una tristeza que todavía me acompaña. Los niños tenían que caminar el doble y algunos simplemente dejaron de venir. Ahí entendí que enseñar también es pelear contra el abandono.

Entrevistadora: ¿Y qué te sostenía?

Docente: El cariño de los niños, sin duda. Y una convicción: que la escuela rural no es una escuela pobre, es otra forma de conocer. El territorio enseña, el río enseña, la huerta enseña. Mi trabajo era tender puentes entre ese saber y el currículum.

Entrevistadora: Si miras hacia atrás, ¿qué aprendiste?

Docente: Que la confianza se construye despacio y se pierde rápido. Que el juego es la forma más seria de aprender. Y que ningún programa reemplaza la conversación cara a cara con un niño que te cuenta su mundo."""


def _anchor(text: str, quote: str) -> tuple[int, int]:
    idx = text.index(quote)
    start = utf16_len(text[:idx])
    return start, start + utf16_len(quote)


def build_example_project() -> Project:
    project = Project(name="Proyecto de ejemplo (demo)")
    doc = Document(filename="entrevista_docente_rural_FICTICIA.txt", text=INTERVIEW)
    project.documents.append(doc)

    anchored = [
        ("Emocional", "miedo inicial", "Llegué con mucho miedo, para ser honesta", "Primer código de la demo: emoción explícita del relato."),
        ("Emocional", "alegría del encuentro", "los niños me recibieron con una alegría que no esperaba", ""),
        ("Relacional", "comunidad sostén", "La comunidad era el corazón de la escuela", "Nótese la metáfora orgánica."),
        ("Descriptivo", "reciprocidad material", "Las familias traían leña en invierno, cocinaban para las fiestas", ""),
        ("Crítico", "cierre y abandono", "enseñar también es pelear contra el abandono", "Tensión política del testimonio."),
        ("Emocional", "pena persistente", "una tristeza que todavía me acompaña", ""),
        ("Teórico", "territorio que enseña", "El territorio enseña, el río enseña, la huerta enseña", "Candidato a categoría central."),
        ("Proceso", "puentes de saberes", "tender puentes entre ese saber y el currículum", ""),
        ("In Vivo", "el juego es serio", "el juego es la forma más seria de aprender", "Código in vivo: palabras textuales de la entrevistada."),
    ]
    for domain, name, quote, memo in anchored:
        start, end = _anchor(INTERVIEW, quote)
        project.codes.append(Code(
            id=project.next_code_id, doc_id=doc.id, domain=domain,
            name=name, quote=quote, start=start, end=end, memo=memo,
        ))
        project.next_code_id += 1

    project.codes.append(Code(
        id=project.next_code_id, doc_id=None, domain="Método",
        name="nota metodológica demo", quote="",
        memo="Este proyecto es ficticio: úsalo para probar la Nube Negra, el arrastre, las relaciones y el reporte sin riesgo.",
    ))
    project.next_code_id += 1

    relations = [
        ("territorio que enseña", "puentes de saberes", "jerarquía"),
        ("comunidad sostén", "alegría del encuentro", "causalidad"),
        ("cierre y abandono", "comunidad sostén", "contradicción"),
    ]
    for source, target, rtype in relations:
        project.relations.append(Relation(
            id=project.next_relation_id, source=source, target=target, type=rtype,
        ))
        project.next_relation_id += 1

    project.nlp_exclusions = ["Entrevistadora", "Docente"]
    return project
