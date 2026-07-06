/* Canvas de Análisis: render del corpus con resaltado por segmentación de rangos
   y mapeo selección→offsets. El Canvas es solo lectura (Principio II).

   Anti-espagueti (FR-006/007, research.md D2): el texto de cada documento se
   parte en los límites de todos sus códigos y cada segmento se emite como un
   <span> PLANO — jamás anidado — así los solapamientos no pueden romper el HTML.
   Los offsets son unidades UTF-16 nativas de JS y se anclan a la posición, no
   a la cadena: las citas repetidas solo pintan la ocurrencia seleccionada. */

const Canvas = {
  el: null,

  init() {
    this.el = document.getElementById("canvas");
    this.el.addEventListener("mouseup", (event) => this._onMouseUp(event));
  },

  render() {
    const { documents, codes } = State.project;
    this.el.textContent = "";
    if (!documents.length) {
      const empty = document.createElement("p");
      empty.id = "canvas-empty";
      empty.textContent = "El corpus está vacío. Importa un PDF, DOCX o TXT desde la zona superior.";
      this.el.appendChild(empty);
      return;
    }
    for (const doc of documents) {
      const wrapper = document.createElement("div");
      wrapper.className = "doc";

      const header = document.createElement("div");
      header.className = "doc-header";
      header.textContent = `— ${doc.filename} —`;
      wrapper.appendChild(header);

      const textEl = document.createElement("div");
      textEl.className = "doc-text";
      textEl.dataset.doc = doc.id;
      this._renderSegments(textEl, doc, codes);
      wrapper.appendChild(textEl);

      this.el.appendChild(wrapper);
    }
  },

  /* Segmentación: límites ordenados → segmentos contiguos → spans planos. */
  _renderSegments(container, doc, codes) {
    const anchored = codes.filter(c => c.doc_id === doc.id);
    const length = doc.text.length;
    const bounds = new Set([0, length]);
    for (const code of anchored) {
      bounds.add(Math.min(code.start, length));
      bounds.add(Math.min(code.end, length));
    }
    const points = [...bounds].sort((a, b) => a - b);

    for (let i = 0; i < points.length - 1; i++) {
      const start = points[i];
      const end = points[i + 1];
      if (end <= start) continue;
      const covering = anchored.filter(c => c.start <= start && c.end >= end);
      const span = document.createElement("span");
      span.className = "seg";
      span.textContent = doc.text.slice(start, end);
      if (covering.length) {
        // El código más reciente (id mayor) define el color visible
        const top = covering.reduce((a, b) => (a.id > b.id ? a : b));
        span.classList.add("hl");
        span.style.backgroundColor = State.domains[top.domain] || "#999";
        span.style.color = this._contrastText(State.domains[top.domain]);
        span.title = covering
          .map(c => `[${c.domain}] ${c.name}`)
          .join("\n");
      }
      container.appendChild(span);
    }
  },

  _contrastText(hex) {
    if (!hex) return "#fff";
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? "#000" : "#fff";
  },

  /* Selección → offsets absolutos dentro de un documento.
     Un Range desde el inicio del .doc-text hasta el punto de selección: la
     longitud de su toString() ES el offset UTF-16 (pre-wrap conserva los \n). */
  _absOffset(docTextEl, container, offset) {
    const range = document.createRange();
    range.setStart(docTextEl, 0);
    range.setEnd(container, offset);
    return range.toString().length;
  },

  _docTextOf(node) {
    const el = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
    return el ? el.closest(".doc-text") : null;
  },

  _onMouseUp(event) {
    // Un clic dentro de la Nube no debe reposicionarla ni cerrarla
    if (event.target.closest && event.target.closest("#nube")) return;

    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) {
      Nube.hide();
      return;
    }
    const range = selection.getRangeAt(0);
    const startDoc = this._docTextOf(range.startContainer);
    const endDoc = this._docTextOf(range.endContainer);

    // Fuera del corpus, o cruzando dos documentos: no codificable (spec, edge case)
    if (!startDoc || !endDoc || startDoc !== endDoc) {
      Nube.hide();
      return;
    }

    const docId = startDoc.dataset.doc;
    const start = this._absOffset(startDoc, range.startContainer, range.startOffset);
    const end = this._absOffset(startDoc, range.endContainer, range.endOffset);
    if (end - start < 3) { // umbral FR-009
      Nube.hide();
      return;
    }

    const doc = State.project.documents.find(d => d.id === docId);
    const quote = doc.text.slice(start, end);
    Nube.show(range.getBoundingClientRect(), { docId, start, end, quote });
  },
};
