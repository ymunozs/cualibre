/* Canvas de Análisis: render del corpus con resaltado por segmentación de rangos
   y mapeo selección→offsets. El Canvas es solo lectura (Principio II).

   Anti-espagueti (FR-006/007, research.md D2): el texto de cada documento se
   parte en los límites de todos sus códigos y cada segmento se emite como un
   <span> PLANO — jamás anidado — así los solapamientos no pueden romper el HTML.
   Los offsets son unidades UTF-16 nativas de JS y se anclan a la posición, no
   a la cadena: las citas repetidas solo pintan la ocurrencia seleccionada. */

const Canvas = {
  el: null,
  activeDocId: null, // null = todos los documentos (FR-035)
  dragSelection: null, // selección arrastrada hacia un código del banco (FR-037)
  hiddenDomains: new Set(), // dominios con resaltado apagado (FR-042)
  searchRanges: [], // resultados de búsqueda en el corpus (FR-041)
  currentHit: -1,

  init() {
    this.el = document.getElementById("canvas");
    this.el.addEventListener("mouseup", (event) => this._onMouseUp(event));
    try {
      this.hiddenDomains = new Set(JSON.parse(localStorage.getItem("cua-hidden-domains") || "[]"));
    } catch (_) { /* preferencia corrupta: partir limpia */ }
    // Posición de lectura persistente (FR-045)
    let scrollTimer = null;
    this.el.addEventListener("scroll", () => {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(() => {
        localStorage.setItem(this._scrollKey(), String(this.el.scrollTop));
      }, 300);
    });
    // Arrastrar la selección: capturar sus offsets antes de soltarla en el banco
    this.el.addEventListener("dragstart", (event) => {
      const info = this._selectionInfo();
      if (!info) { event.preventDefault(); return; }
      this.dragSelection = info;
      event.dataTransfer.setData("text/plain", info.quote);
      event.dataTransfer.effectAllowed = "copy";
      Nube.hide();
    });
    this.el.addEventListener("dragend", () => { this.dragSelection = null; });
  },

  _scrollKey() {
    const pid = State.project ? State.project.id : "none";
    return `cua-scroll-${pid}-${this.activeDocId || "all"}`;
  },

  render() {
    const { documents, codes } = State.project;
    // Si el documento activo ya no existe, volver a "Todos"
    if (this.activeDocId && !documents.some(d => d.id === this.activeDocId)) {
      this.activeDocId = null;
    }
    this._renderDocTabs(documents);
    // No perder el punto de lectura al re-renderizar (FR-045)
    const savedScroll = this.el.scrollTop || parseInt(localStorage.getItem(this._scrollKey()) || "0", 10);

    this.el.textContent = "";
    if (!documents.length) {
      const empty = document.createElement("p");
      empty.id = "canvas-empty";
      empty.textContent = "El corpus está vacío. Importa un PDF, DOCX o TXT desde la zona superior.";
      this.el.appendChild(empty);
      return;
    }
    const visible = this.activeDocId
      ? documents.filter(d => d.id === this.activeDocId)
      : documents;
    for (const doc of visible) {
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
    this.el.scrollTop = savedScroll;
  },

  /* Pestañas de documentos: navegación, nunca entrada de datos (Principio II). */
  _renderDocTabs(documents) {
    const bar = document.getElementById("doc-tabs");
    bar.textContent = "";
    if (documents.length < 2) {
      bar.classList.add("hidden");
      return;
    }
    bar.classList.remove("hidden");
    const makeTab = (label, docId) => {
      const tab = document.createElement("button");
      tab.className = "doc-tab" + (this.activeDocId === docId ? " active" : "");
      tab.textContent = label;
      tab.title = label;
      tab.addEventListener("click", () => {
        this.activeDocId = docId;
        this.render();
      });
      bar.appendChild(tab);
    };
    makeTab("TODOS", null);
    for (const doc of documents) makeTab(doc.filename, doc.id);
  },

  /* Segmentación: límites ordenados → segmentos contiguos → spans planos.
     Incluye filtro de dominios (FR-042) y marcas de búsqueda (FR-041). */
  _renderSegments(container, doc, codes) {
    const anchored = codes.filter(
      c => c.doc_id === doc.id && !this.hiddenDomains.has(c.domain)
    );
    const hits = this.searchRanges.filter(r => r.docId === doc.id);
    const length = doc.text.length;
    const bounds = new Set([0, length]);
    for (const code of anchored) {
      bounds.add(Math.min(code.start, length));
      bounds.add(Math.min(code.end, length));
    }
    for (const hit of hits) {
      bounds.add(Math.min(hit.start, length));
      bounds.add(Math.min(hit.end, length));
    }
    // Numeración de líneas (FR-057): cada \n es un límite; el texto se agrupa
    // en divs .line y el número vive en un ::before CSS (fuera de la selección
    // y del copiado). El \n real queda en un span oculto DENTRO del div para
    // que Range.toString() siga reproduciendo doc.text exacto (offsets intactos).
    for (let i = 0; i < length; i++) {
      if (doc.text[i] === "\n") { bounds.add(i); bounds.add(i + 1); }
    }
    const points = [...bounds].sort((a, b) => a - b);

    let line = document.createElement("div");
    line.className = "line";
    for (let i = 0; i < points.length - 1; i++) {
      const start = points[i];
      const end = points[i + 1];
      if (end <= start) continue;
      const segText = doc.text.slice(start, end);
      if (segText === "\n") {
        const nl = document.createElement("span");
        nl.className = "nl";
        nl.textContent = "\n";
        line.appendChild(nl);
        container.appendChild(line);
        line = document.createElement("div");
        line.className = "line";
        continue;
      }
      const covering = anchored.filter(c => c.start <= start && c.end >= end);
      const span = document.createElement("span");
      span.className = "seg";
      span.textContent = segText;
      const hit = hits.find(h => h.start <= start && h.end >= end);
      if (hit) {
        span.classList.add("search-hit");
        span.dataset.hit = hit.idx;
        if (hit.idx === this.currentHit) span.classList.add("search-current");
      }
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
      line.appendChild(span);
    }
    container.appendChild(line);
  },

  /* Ir a una cita concreta (recuperación por código, FR-055) */
  goToQuote(code) {
    this.activeDocId = null;
    this.searchRanges = [{ docId: code.doc_id, start: code.start, end: code.end, idx: 0 }];
    this.currentHit = 0;
    this.render();
    this._scrollToHit();
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

  /* Selección actual → {docId, start, end, quote, rect} o null si no es codificable. */
  _selectionInfo() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) return null;

    const range = selection.getRangeAt(0);
    const startDoc = this._docTextOf(range.startContainer);
    const endDoc = this._docTextOf(range.endContainer);

    // Fuera del corpus, o cruzando dos documentos: no codificable (spec, edge case)
    if (!startDoc || !endDoc || startDoc !== endDoc) return null;

    const docId = startDoc.dataset.doc;
    const start = this._absOffset(startDoc, range.startContainer, range.startOffset);
    const end = this._absOffset(startDoc, range.endContainer, range.endOffset);
    if (end - start < 3) return null; // umbral FR-009

    const doc = State.project.documents.find(d => d.id === docId);
    return {
      docId, start, end,
      quote: doc.text.slice(start, end),
      rect: range.getBoundingClientRect(),
    };
  },

  _onMouseUp(event) {
    // Un clic dentro de la Nube no debe reposicionarla ni cerrarla
    if (event.target.closest && event.target.closest("#nube")) return;

    const info = this._selectionInfo();
    if (!info) {
      Nube.hide();
      return;
    }
    Nube.show(info.rect, info);
  },

  // ---------- Búsqueda en el corpus (FR-041) ----------

  search(query) {
    this.searchRanges = [];
    this.currentHit = -1;
    const needle = query.trim().toLowerCase();
    if (needle.length >= 2) {
      let idx = 0;
      for (const doc of State.project.documents) {
        const haystack = doc.text.toLowerCase();
        let from = 0;
        while (true) {
          const at = haystack.indexOf(needle, from);
          if (at === -1 || idx > 500) break;
          this.searchRanges.push({ docId: doc.id, start: at, end: at + needle.length, idx });
          from = at + needle.length;
          idx++;
        }
      }
      if (this.searchRanges.length) {
        this.activeDocId = null; // ver todos los documentos para navegar los hits
        this.currentHit = 0;
      }
    }
    this.render();
    this._scrollToHit();
    return this.searchRanges.length;
  },

  nextHit(delta) {
    if (!this.searchRanges.length) return;
    this.currentHit = (this.currentHit + delta + this.searchRanges.length) % this.searchRanges.length;
    this.render();
    this._scrollToHit();
  },

  clearSearch() {
    this.searchRanges = [];
    this.currentHit = -1;
    this.render();
  },

  _scrollToHit() {
    if (this.currentHit < 0) return;
    const el = this.el.querySelector(`.search-current`);
    if (el) el.scrollIntoView({ block: "center", behavior: "smooth" });
  },

  // ---------- Filtro de resaltados (FR-042) ----------

  toggleDomain(domain) {
    this.hiddenDomains.has(domain)
      ? this.hiddenDomains.delete(domain)
      : this.hiddenDomains.add(domain);
    localStorage.setItem("cua-hidden-domains", JSON.stringify([...this.hiddenDomains]));
    this.render();
  },

  setAllDomains(hidden) {
    this.hiddenDomains = hidden ? new Set(Object.keys(State.domains)) : new Set();
    localStorage.setItem("cua-hidden-domains", JSON.stringify([...this.hiddenDomains]));
    this.render();
  },
};
