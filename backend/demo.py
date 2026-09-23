"""Proyecto de ejemplo (FR-061): entrevista ficticia precargada y codificada,
para aprender el flujo de Cua-libre sin arriesgar datos reales.

Existe en los tres idiomas de la interfaz: la entrevista, los códigos y los
memos cambian; las claves de categoría y de relación son siempre las mismas."""

from __future__ import annotations

from .i18n import current
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


INTERVIEW_EN = """Interviewer: How do you remember your first years teaching at the rural school?

Teacher: I arrived feeling very frightened, to be honest. The school was three hours from the village and I didn't know anyone. But the children welcomed me with a joy I hadn't expected, and that changed everything for me.

Interviewer: What role did the community play?

Teacher: The community was the heart of the school. Families brought firewood in winter and cooked for the celebrations. I learnt more from them than from any teaching manual.

Interviewer: Were there difficult moments?

Teacher: Many. When they closed the neighbouring school I felt enormous grief, a sadness that is still with me. The children had to walk twice as far and some simply stopped coming. That was when I understood that teaching is also fighting against abandonment.

Interviewer: And what kept you going?

Teacher: The children's affection, without a doubt. And a conviction: that a rural school is not a poor school, it is another way of knowing. The land teaches, the river teaches, the vegetable garden teaches. My job was to build bridges between that knowledge and the curriculum.

Interviewer: Looking back, what did you learn?

Teacher: That trust is built slowly and lost quickly. That play is the most serious way of learning. And that no programme replaces a face-to-face conversation with a child who tells you about their world."""

INTERVIEW_PT = """Entrevistadora: Como você se lembra dos seus primeiros anos ensinando na escola rural?

Professora: Cheguei com muito medo, para ser sincera. A escola ficava a três horas da cidade e eu não conhecia ninguém. Mas as crianças me receberam com uma alegria que eu não esperava, e isso mudou tudo para mim.

Entrevistadora: Que papel a comunidade tinha?

Professora: A comunidade era o coração da escola. As famílias traziam lenha no inverno, cozinhavam para as festas. Aprendi mais com elas do que com qualquer manual de pedagogia.

Entrevistadora: Houve momentos difíceis?

Professora: Muitos. Quando fecharam a escola vizinha senti uma dor enorme, uma tristeza que ainda me acompanha. As crianças tinham que caminhar o dobro e algumas simplesmente deixaram de vir. Ali entendi que ensinar também é lutar contra o abandono.

Entrevistadora: E o que te sustentava?

Professora: O carinho das crianças, sem dúvida. E uma convicção: que a escola rural não é uma escola pobre, é outra forma de conhecer. O território ensina, o rio ensina, a horta ensina. Meu trabalho era construir pontes entre esse saber e o currículo.

Entrevistadora: Olhando para trás, o que você aprendeu?

Professora: Que a confiança se constrói devagar e se perde rápido. Que brincar é a forma mais séria de aprender. E que nenhum programa substitui a conversa cara a cara com uma criança que te conta o mundo dela."""

# Por idioma: nombre del proyecto, archivo, entrevista, códigos anclados
# (categoría, nombre, cita literal, memo), código manual, relaciones y
# exclusiones NLP (las marcas de hablante).
DEMOS = {
    "es": {
        "project": "Proyecto de ejemplo (demo)",
        "filename": "entrevista_docente_rural_FICTICIA.txt",
        "text": INTERVIEW,
        "anchored": [
            ("Emocional", "miedo inicial", "Llegué con mucho miedo, para ser honesta", "Primer código de la demo: emoción explícita del relato."),
            ("Emocional", "alegría del encuentro", "los niños me recibieron con una alegría que no esperaba", ""),
            ("Relacional", "comunidad sostén", "La comunidad era el corazón de la escuela", "Nótese la metáfora orgánica."),
            ("Descriptivo", "reciprocidad material", "Las familias traían leña en invierno, cocinaban para las fiestas", ""),
            ("Crítico", "cierre y abandono", "enseñar también es pelear contra el abandono", "Tensión política del testimonio."),
            ("Emocional", "pena persistente", "una tristeza que todavía me acompaña", ""),
            ("Teórico", "territorio que enseña", "El territorio enseña, el río enseña, la huerta enseña", "Candidato a categoría central."),
            ("Proceso", "puentes de saberes", "tender puentes entre ese saber y el currículum", ""),
            ("In Vivo", "el juego es serio", "el juego es la forma más seria de aprender", "Código in vivo: palabras textuales de la entrevistada."),
        ],
        "manual": ("nota metodológica demo", "Este proyecto es ficticio: úsalo para probar la Nube Negra, el arrastre, las relaciones y el reporte sin riesgo."),
        "relations": [
            ("territorio que enseña", "puentes de saberes", "jerarquía"),
            ("comunidad sostén", "alegría del encuentro", "causalidad"),
            ("cierre y abandono", "comunidad sostén", "contradicción"),
        ],
        "exclusions": ["Entrevistadora", "Docente"],
    },
    "en": {
        "project": "Example project (demo)",
        "filename": "rural_teacher_interview_FICTIONAL.txt",
        "text": INTERVIEW_EN,
        "anchored": [
            ("Emocional", "initial fear", "I arrived feeling very frightened, to be honest", "First code in the demo: an explicit emotion in the account."),
            ("Emocional", "joy of the encounter", "the children welcomed me with a joy I hadn't expected", ""),
            ("Relacional", "community as support", "The community was the heart of the school", "Note the organic metaphor."),
            ("Descriptivo", "material reciprocity", "Families brought firewood in winter and cooked for the celebrations", ""),
            ("Crítico", "closure and abandonment", "teaching is also fighting against abandonment", "The political tension in the testimony."),
            ("Emocional", "lingering grief", "a sadness that is still with me", ""),
            ("Teórico", "the land that teaches", "The land teaches, the river teaches, the vegetable garden teaches", "Candidate for a core category."),
            ("Proceso", "bridges between knowledges", "build bridges between that knowledge and the curriculum", ""),
            ("In Vivo", "play is serious", "play is the most serious way of learning", "In vivo code: the interviewee's own words."),
        ],
        "manual": ("demo methodological note", "This project is fictional: use it to try out the Black Cloud, drag and drop, relationships and the report without any risk."),
        "relations": [
            ("the land that teaches", "bridges between knowledges", "jerarquía"),
            ("community as support", "joy of the encounter", "causalidad"),
            ("closure and abandonment", "community as support", "contradicción"),
        ],
        "exclusions": ["Interviewer", "Teacher"],
    },
    "pt": {
        "project": "Projeto de exemplo (demo)",
        "filename": "entrevista_professora_rural_FICTICIA.txt",
        "text": INTERVIEW_PT,
        "anchored": [
            ("Emocional", "medo inicial", "Cheguei com muito medo, para ser sincera", "Primeiro código da demo: emoção explícita no relato."),
            ("Emocional", "alegria do encontro", "as crianças me receberam com uma alegria que eu não esperava", ""),
            ("Relacional", "comunidade que sustenta", "A comunidade era o coração da escola", "Observe a metáfora orgânica."),
            ("Descriptivo", "reciprocidade material", "As famílias traziam lenha no inverno, cozinhavam para as festas", ""),
            ("Crítico", "fechamento e abandono", "ensinar também é lutar contra o abandono", "Tensão política do depoimento."),
            ("Emocional", "dor persistente", "uma tristeza que ainda me acompanha", ""),
            ("Teórico", "território que ensina", "O território ensina, o rio ensina, a horta ensina", "Candidato a categoria central."),
            ("Proceso", "pontes entre saberes", "construir pontes entre esse saber e o currículo", ""),
            ("In Vivo", "brincar é sério", "brincar é a forma mais séria de aprender", "Código in vivo: palavras textuais da entrevistada."),
        ],
        "manual": ("nota metodológica da demo", "Este projeto é fictício: use-o para testar a Nuvem Negra, o arrastar, as relações e o relatório sem risco."),
        "relations": [
            ("território que ensina", "pontes entre saberes", "jerarquía"),
            ("comunidade que sustenta", "alegria do encontro", "causalidad"),
            ("fechamento e abandono", "comunidade que sustenta", "contradicción"),
        ],
        "exclusions": ["Entrevistadora", "Professora"],
    },
}


def _anchor(text: str, quote: str) -> tuple[int, int]:
    idx = text.index(quote)
    start = utf16_len(text[:idx])
    return start, start + utf16_len(quote)


def build_example_project(lang: str | None = None) -> Project:
    demo = DEMOS.get(lang or current(), DEMOS["es"])
    text = demo["text"]
    project = Project(name=demo["project"])
    doc = Document(filename=demo["filename"], text=text)
    project.documents.append(doc)

    for domain, name, quote, memo in demo["anchored"]:
        start, end = _anchor(text, quote)
        project.codes.append(Code(
            id=project.next_code_id, doc_id=doc.id, domain=domain,
            name=name, quote=quote, start=start, end=end, memo=memo,
        ))
        project.next_code_id += 1

    manual_name, manual_memo = demo["manual"]
    project.codes.append(Code(
        id=project.next_code_id, doc_id=None, domain="Método",
        name=manual_name, quote="", memo=manual_memo,
    ))
    project.next_code_id += 1

    for source, target, rtype in demo["relations"]:
        project.relations.append(Relation(
            id=project.next_relation_id, source=source, target=target, type=rtype,
        ))
        project.next_relation_id += 1

    project.nlp_exclusions = list(demo["exclusions"])
    return project
