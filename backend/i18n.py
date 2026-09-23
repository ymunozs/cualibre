"""Idioma de la interfaz para los mensajes que produce el backend.

Tres idiomas: español latinoamericano (es, idioma fuente), inglés británico (en)
y portugués de Brasil (pt). El frontend envía el idioma elegido en la cabecera
X-Cua-Lang (o en el parámetro ?ui= para descargas directas); un middleware lo
deja en un ContextVar para que endpoints, validadores y exportadores lo lean
sin tener que pasarlo de mano en mano.

Los datos del investigador NUNCA se traducen: las claves de las Categorías
Básicas ("Emocional"…) y de los tipos de relación ("jerarquía"…) se guardan
siempre igual, así un proyecto abre idéntico en cualquier idioma. Solo cambia
cómo se muestran.
"""

from __future__ import annotations

from contextvars import ContextVar

LANGS = ("es", "en", "pt")
DEFAULT_LANG = "es"

_current: ContextVar[str] = ContextVar("cua_ui_lang", default=DEFAULT_LANG)


def normalize(value: str | None) -> str:
    """'pt-BR' → 'pt', 'en-GB' → 'en'; cualquier otra cosa → español."""
    if not value:
        return DEFAULT_LANG
    code = value.strip().lower()[:2]
    return code if code in LANGS else DEFAULT_LANG


def set_lang(value: str | None):
    return _current.set(normalize(value))


def reset_lang(token) -> None:
    _current.reset(token)


def current() -> str:
    return _current.get()


MESSAGES: dict[str, dict[str, str]] = {
    # ----- Proyectos -----
    "project_not_found": {
        "es": "Proyecto no encontrado",
        "en": "Project not found",
        "pt": "Projeto não encontrado",
    },
    "default_project_name": {
        "es": "Mi proyecto",
        "en": "My project",
        "pt": "Meu projeto",
    },
    "reset_needs_confirm": {
        "es": "El reinicio requiere confirmación explícita",
        "en": "Resetting requires explicit confirmation",
        "pt": "A reinicialização exige confirmação explícita",
    },
    "delete_project_needs_confirm": {
        "es": "Eliminar un proyecto requiere confirmación explícita",
        "en": "Deleting a project requires explicit confirmation",
        "pt": "Excluir um projeto exige confirmação explícita",
    },
    "restore_needs_confirm": {
        "es": "Restaurar requiere confirmación explícita",
        "en": "Restoring requires explicit confirmation",
        "pt": "A restauração exige confirmação explícita",
    },
    "snapshot_not_found": {
        "es": "Respaldo no encontrado",
        "en": "Backup not found",
        "pt": "Cópia de segurança não encontrada",
    },
    "import_invalid": {
        "es": "El archivo no es un proyecto de Cua-libre válido (usa un respaldo .zip o un proyecto .json)",
        "en": "This file is not a valid Cua-libre project (use a .zip backup or a .json project)",
        "pt": "O arquivo não é um projeto válido do Cua-libre (use um backup .zip ou um projeto .json)",
    },
    "imported_suffix": {
        "es": "(importado)",
        "en": "(imported)",
        "pt": "(importado)",
    },
    # ----- Documentos -----
    "default_document_name": {
        "es": "documento",
        "en": "document",
        "pt": "documento",
    },
    "document_not_found": {
        "es": "Documento no encontrado",
        "en": "Document not found",
        "pt": "Documento não encontrado",
    },
    "document_has_codes": {
        "es": "El documento tiene {n} código(s) asociado(s) que se perderán. "
              "Repite la operación con confirmación para eliminarlos.",
        "en": "This document has {n} code(s) attached that will be lost. "
              "Repeat the operation with confirmation to delete them.",
        "pt": "O documento tem {n} código(s) associado(s) que serão perdidos. "
              "Repita a operação com confirmação para excluí-los.",
    },
    "unsupported_file": {
        "es": "Tipo de archivo no soportado: .{ext}. Usa PDF, DOCX o TXT",
        "en": "Unsupported file type: .{ext}. Use PDF, DOCX or TXT",
        "pt": "Tipo de arquivo não suportado: .{ext}. Use PDF, DOCX ou TXT",
    },
    "unreadable_file": {
        "es": "No se pudo leer «{filename}»: archivo dañado o ilegible",
        "en": "Could not read “{filename}”: the file is damaged or unreadable",
        "pt": "Não foi possível ler “{filename}”: arquivo danificado ou ilegível",
    },
    "no_text": {
        "es": "«{filename}» no contiene texto extraíble (¿PDF escaneado sin capa de texto?)",
        "en": "“{filename}” contains no extractable text (a scanned PDF without a text layer?)",
        "pt": "“{filename}” não contém texto extraível (PDF digitalizado sem camada de texto?)",
    },
    "no_text_no_ocr": {
        "es": "«{filename}» no contiene texto extraíble y este equipo no tiene OCR disponible",
        "en": "“{filename}” contains no extractable text and OCR is not available on this computer",
        "pt": "“{filename}” não contém texto extraível e este computador não tem OCR disponível",
    },
    "ocr_failed": {
        "es": "El OCR no pudo leer «{filename}»: {error}",
        "en": "OCR could not read “{filename}”: {error}",
        "pt": "O OCR não conseguiu ler “{filename}”: {error}",
    },
    # ----- Códigos y categorías -----
    "invalid_domain": {
        "es": "Categoría inválida: «{name}»",
        "en": "Invalid category: “{name}”",
        "pt": "Categoria inválida: “{name}”",
    },
    "code_document_missing": {
        "es": "El documento del código no existe en este proyecto",
        "en": "The code's document does not exist in this project",
        "pt": "O documento do código não existe neste projeto",
    },
    "offsets_out_of_range": {
        "es": "Offsets fuera del rango del documento",
        "en": "Offsets fall outside the document",
        "pt": "Posições fora do intervalo do documento",
    },
    "code_not_found": {
        "es": "Código no encontrado",
        "en": "Code not found",
        "pt": "Código não encontrado",
    },
    "no_codes_named": {
        "es": "No hay códigos llamados «{name}»",
        "en": "There are no codes called “{name}”",
        "pt": "Não há códigos chamados “{name}”",
    },
    "no_code_named": {
        "es": "No existe un código llamado «{name}»",
        "en": "No code called “{name}” exists",
        "pt": "Não existe um código chamado “{name}”",
    },
    "relation_exists": {
        "es": "Esa relación ya existe",
        "en": "That relationship already exists",
        "pt": "Essa relação já existe",
    },
    "relation_not_found": {
        "es": "Relación no encontrada",
        "en": "Relationship not found",
        "pt": "Relação não encontrada",
    },
    "category_exists": {
        "es": "Ya existe una categoría llamada «{name}»",
        "en": "A category called “{name}” already exists",
        "pt": "Já existe uma categoria chamada “{name}”",
    },
    "custom_category_not_found": {
        "es": "Categoría personalizada no encontrada",
        "en": "Custom category not found",
        "pt": "Categoria personalizada não encontrada",
    },
    "custom_category_in_use": {
        "es": "{n} código(s) usan la categoría «{name}». Repite la operación con "
              "confirmación: conservarán el nombre pero quedarán sin color propio.",
        "en": "{n} code(s) use the category “{name}”. Repeat the operation with "
              "confirmation: they will keep the name but lose their colour.",
        "pt": "{n} código(s) usam a categoria “{name}”. Repita a operação com "
              "confirmação: manterão o nome, mas ficarão sem cor própria.",
    },
    # ----- Validación (models.py) -----
    "project_name_empty": {
        "es": "El nombre del proyecto no puede estar vacío",
        "en": "The project name cannot be empty",
        "pt": "O nome do projeto não pode ficar vazio",
    },
    "domain_empty": {
        "es": "La categoría no puede estar vacía",
        "en": "The category cannot be empty",
        "pt": "A categoria não pode ficar vazia",
    },
    "code_name_empty": {
        "es": "El nombre del código no puede estar vacío",
        "en": "The code name cannot be empty",
        "pt": "O nome do código não pode ficar vazio",
    },
    "manual_no_offsets": {
        "es": "Un código manual no puede llevar offsets",
        "en": "A manual code cannot carry offsets",
        "pt": "Um código manual não pode ter posições",
    },
    "anchored_needs_offsets": {
        "es": "Un código anclado requiere offsets start y end",
        "en": "An anchored code needs start and end offsets",
        "pt": "Um código ancorado exige posições de início e fim",
    },
    "offsets_incoherent": {
        "es": "Offsets incoherentes: se requiere 0 <= start < end",
        "en": "Inconsistent offsets: 0 <= start < end is required",
        "pt": "Posições incoerentes: é necessário 0 <= início < fim",
    },
    "name_empty": {
        "es": "El nombre no puede estar vacío",
        "en": "The name cannot be empty",
        "pt": "O nome não pode ficar vazio",
    },
    "merge_same_names": {
        "es": "Elige dos nombres distintos para fusionar",
        "en": "Choose two different names to merge",
        "pt": "Escolha dois nomes diferentes para mesclar",
    },
    "category_name_empty": {
        "es": "El nombre de la categoría no puede estar vacío",
        "en": "The category name cannot be empty",
        "pt": "O nome da categoria não pode ficar vazio",
    },
    "invalid_color": {
        "es": "Color inválido: «{value}». Debe ser hex tipo #RRGGBB",
        "en": "Invalid colour: “{value}”. It must be a hex value such as #RRGGBB",
        "pt": "Cor inválida: “{value}”. Deve ser hexadecimal como #RRGGBB",
    },
    "invalid_relation_type": {
        "es": "Tipo de relación inválido: «{value}»",
        "en": "Invalid relationship type: “{value}”",
        "pt": "Tipo de relação inválido: “{value}”",
    },
    "relation_same_ends": {
        "es": "Una relación requiere dos códigos distintos",
        "en": "A relationship needs two different codes",
        "pt": "Uma relação exige dois códigos diferentes",
    },
    "invalid_field": {
        "es": "Dato inválido en «{field}»",
        "en": "Invalid value in “{field}”",
        "pt": "Valor inválido em “{field}”",
    },
    "field_too_long": {
        "es": "«{field}» es demasiado largo (máximo {max} caracteres)",
        "en": "“{field}” is too long (maximum {max} characters)",
        "pt": "“{field}” é longo demais (máximo de {max} caracteres)",
    },
    "field_required": {
        "es": "Falta un dato obligatorio: «{field}»",
        "en": "A required value is missing: “{field}”",
        "pt": "Falta um dado obrigatório: “{field}”",
    },
    # ----- Análisis -----
    "corpus_lang_unsupported": {
        "es": "Idioma del corpus no soportado: usa es, en o pt",
        "en": "Unsupported corpus language: use es, en or pt",
        "pt": "Idioma do corpus não suportado: use es, en ou pt",
    },
    "pos_invalid": {
        "es": "Filtro gramatical inválido: usa all, verb, noun o adj",
        "en": "Invalid grammatical filter: use all, verb, noun or adj",
        "pt": "Filtro gramatical inválido: use all, verb, noun ou adj",
    },
    "pos_lang_unsupported": {
        "es": "El foco gramatical está disponible para corpus en español e inglés",
        "en": "Grammatical focus is available for Spanish and English corpora",
        "pt": "O foco gramatical está disponível para corpus em espanhol e inglês",
    },
    "kwic_empty_query": {
        "es": "Debes indicar una palabra para buscar concordancias",
        "en": "Enter a word to search for concordances",
        "pt": "Indique uma palavra para buscar concordâncias",
    },
    "openalex_error": {
        "es": "No se pudo consultar OpenAlex (¿hay conexión a internet?). "
              "Tu trabajo local no se ve afectado.",
        "en": "OpenAlex could not be reached (is there an internet connection?). "
              "Your local work is not affected.",
        "pt": "Não foi possível consultar o OpenAlex (há conexão com a internet?). "
              "Seu trabalho local não foi afetado.",
    },
    "untitled": {
        "es": "(sin título)",
        "en": "(untitled)",
        "pt": "(sem título)",
    },
    "manual_not_found": {
        "es": "Manual no encontrado",
        "en": "Manual not found",
        "pt": "Manual não encontrado",
    },
    "lexicon_download_failed": {
        "es": "No se pudo descargar el léxico desde el sitio del NRC (¿hay conexión a internet?). "
              "También puedes elegir el .zip oficial que ya tengas.",
        "en": "The lexicon could not be downloaded from the NRC website (is there an internet "
              "connection?). You can also choose the official .zip if you already have it.",
        "pt": "Não foi possível baixar o léxico do site do NRC (há conexão com a internet?). "
              "Você também pode escolher o .zip oficial, se já o tiver.",
    },
    "lexicon_invalid": {
        "es": "El archivo no es el .zip oficial del NRC Emotion Lexicon",
        "en": "This file is not the official NRC Emotion Lexicon .zip",
        "pt": "O arquivo não é o .zip oficial do NRC Emotion Lexicon",
    },
    "agreement_file": {"es": "acuerdo", "en": "agreement", "pt": "acordo"},
    "agreement_col_code": {"es": "codigo", "en": "code", "pt": "codigo"},
    "agreement_col_count_a": {"es": "citas_A", "en": "quotes_A", "pt": "citacoes_A"},
    "agreement_col_count_b": {"es": "citas_B", "en": "quotes_B", "pt": "citacoes_B"},
    "agreement_col_agreement": {"es": "acuerdo_porcentual", "en": "percent_agreement", "pt": "acordo_percentual"},
    "agreement_col_kappa": {"es": "kappa_cohen", "en": "cohen_kappa", "pt": "kappa_cohen"},
    "agreement_col_alpha": {"es": "alfa_krippendorff", "en": "krippendorff_alpha", "pt": "alfa_krippendorff"},
    "agreement_col_band": {"es": "tramo_landis_koch", "en": "landis_koch_band", "pt": "faixa_landis_koch"},
    "band_na": {"es": "no calculable", "en": "not computable", "pt": "não calculável"},
    "band_poor": {"es": "pobre", "en": "poor", "pt": "pobre"},
    "band_slight": {"es": "leve", "en": "slight", "pt": "leve"},
    "band_fair": {"es": "aceptable", "en": "fair", "pt": "razoável"},
    "band_moderate": {"es": "moderado", "en": "moderate", "pt": "moderado"},
    "band_substantial": {"es": "considerable", "en": "substantial", "pt": "substancial"},
    "band_almost_perfect": {"es": "casi perfecto", "en": "almost perfect", "pt": "quase perfeito"},
    # ----- Exportación -----
    "csv_columns": {
        "es": "id|fecha|documento|dominio|codigo|cita|memo",
        "en": "id|date|document|category|code|quote|memo",
        "pt": "id|data|documento|categoria|codigo|citacao|memo",
    },
    "manual_origin": {
        "es": "Manual",
        "en": "Manual",
        "pt": "Manual",
    },
    "backup_suffix": {
        "es": "respaldo",
        "en": "backup",
        "pt": "backup",
    },
    "readme_name": {
        "es": "LEEME.txt",
        "en": "README.txt",
        "pt": "LEIAME.txt",
    },
    "codes_csv_name": {
        "es": "codigos.csv",
        "en": "codes.csv",
        "pt": "codigos.csv",
    },
    "documents_folder": {
        "es": "documentos",
        "en": "documents",
        "pt": "documentos",
    },
    "readme_body": {
        "es": (
            "CUA-LIBRE STUDIO · Respaldo completo del proyecto «{name}»\n"
            "Exportado: {date}\n\n"
            "Contenido:\n"
            "- proyecto.json  → el proyecto completo (corpus, códigos, relaciones,\n"
            "                   memos, categorías propias). Fidelidad total: impórtalo\n"
            "                   desde Cua-libre con el botón IMPORTAR de la cabecera.\n"
            "- {csv}     → el banco de códigos en una tabla (UTF-8, abre en Excel).\n"
            "- {docs}/    → el texto de cada documento del corpus, en .txt plano.\n\n"
            "Generado por CUA-LIBRE STUDIO · https://github.com/ymunozs/cualibre\n"
        ),
        "en": (
            "CUA-LIBRE STUDIO · Full backup of the project “{name}”\n"
            "Exported: {date}\n\n"
            "Contents:\n"
            "- proyecto.json  → the complete project (corpus, codes, relationships,\n"
            "                   memos, custom categories). Full fidelity: import it\n"
            "                   from Cua-libre with the IMPORT button in the header.\n"
            "- {csv}       → the code bank as a table (UTF-8, opens in Excel).\n"
            "- {docs}/     → the text of every corpus document, as plain .txt.\n\n"
            "Generated by CUA-LIBRE STUDIO · https://github.com/ymunozs/cualibre\n"
        ),
        "pt": (
            "CUA-LIBRE STUDIO · Backup completo do projeto “{name}”\n"
            "Exportado: {date}\n\n"
            "Conteúdo:\n"
            "- proyecto.json  → o projeto completo (corpus, códigos, relações,\n"
            "                   memos, categorias próprias). Fidelidade total: importe-o\n"
            "                   no Cua-libre com o botão IMPORTAR do cabeçalho.\n"
            "- {csv}     → o banco de códigos em tabela (UTF-8, abre no Excel).\n"
            "- {docs}/    → o texto de cada documento do corpus, em .txt simples.\n\n"
            "Gerado pelo CUA-LIBRE STUDIO · https://github.com/ymunozs/cualibre\n"
        ),
    },
}

# Etiquetas visibles de las Categorías Básicas (las claves no cambian nunca)
DOMAIN_LABELS: dict[str, dict[str, str]] = {
    "Emocional": {"en": "Emotional", "pt": "Emocional"},
    "Descriptivo": {"en": "Descriptive", "pt": "Descritivo"},
    "In Vivo": {"en": "In Vivo", "pt": "In Vivo"},
    "Tensión/CHAT": {"en": "Tension/CHAT", "pt": "Tensão/CHAT"},
    "Proceso": {"en": "Process", "pt": "Processo"},
    "Teórico": {"en": "Theoretical", "pt": "Teórico"},
    "Relacional": {"en": "Relational", "pt": "Relacional"},
    "Crítico": {"en": "Critical", "pt": "Crítico"},
    "Método": {"en": "Method", "pt": "Método"},
}


def tr(key: str, lang: str | None = None, **params) -> str:
    """Mensaje traducido al idioma de la petición en curso (o al indicado)."""
    lang = lang or current()
    entry = MESSAGES.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry[DEFAULT_LANG]
    return text.format(**params) if params else text


def domain_label(key: str, lang: str | None = None) -> str:
    lang = lang or current()
    return DOMAIN_LABELS.get(key, {}).get(lang, key)
