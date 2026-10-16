/* Biblioteca de literatura (FR-089..092): común a todos los proyectos.

   - Lista de documentos con sus fichas (metadatos para APA 7) y búsqueda.
   - Lector: los PDF se dibujan con PDF.js directamente en la página (sin
     iframes: Principio IV), con su capa de texto para seleccionar; los Word y
     TXT se leen como texto continuo.
   - Anotaciones de lectura (resaltar, subrayar, tachar, nota) y pasajes
     codificados con los códigos del proyecto activo. Las anotaciones son de la
     persona; los pasajes codificados son del proyecto y viven aparte del corpus.
   - Un menú efímero aparece al seleccionar, como la Nube Negra, y desaparece
     al confirmar o con Esc: ninguna barra fija queda sobre el texto.

   Posiciones en PDF: página + rectángulos en fracciones de la página (no
   dependen del zoom). En texto: offsets UTF-16, como el Canvas. */

const Biblioteca = {
  items: [],
  query: "",
  // Tabla de la biblioteca, al estilo Finder/Mendeley (FR-089)
  filters: { author: "", title: "", container: "", year: "" },
  sort: { key: "year", dir: -1 }, // por omisión: lo más reciente arriba
  selectedId: null,
  _editingMeta: false,
  current: null, // documento abierto
  annotations: [],
  codings: [],
  scale: 1,
  _pdf: null,
  _observer: null,
  _rendered: new Set(),
  _text: "",
  _pending: null, // selección en espera del menú: {anchor, quote}
  _popupMode: "main",
  COLORS: ["#FFCC00", "#00CC66", "#0099CC", "#FF0066"],

  init() {
    if (window.pdfjsLib) {
      pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.min.js";
    }
    document.getElementById("lib-file").addEventListener("change", (e) => this._import(e));
    document.getElementById("lib-search").addEventListener("input", (e) => {
      this.query = e.target.value.trim().toLowerCase();
      this._renderList();
    });
    try { // orden elegido: preferencia de esta persona (no un dato del proyecto)
      const saved = JSON.parse(localStorage.getItem("cua-lib-sort") || "null");
      if (saved && ["author", "title", "container", "year"].includes(saved.key)) this.sort = saved;
    } catch (_) { /* sin almacenamiento */ }
    // Teclado como en Finder: ↑↓ recorren la lista, Enter abre
    document.addEventListener("keydown", (e) => {
      if (Views.current !== "literatura" || this.current) return;
      if (e.target.matches("input, textarea, select") || document.querySelector("dialog[open]")) return;
      const rows = this._visible || [];
      if (!rows.length) return;
      const i = rows.findIndex(item => item.id === this.selectedId);
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        const next = rows[Math.max(0, Math.min(rows.length - 1, i + (e.key === "ArrowDown" ? 1 : -1)))];
        this._select(next.id, true);
      } else if (e.key === "Enter" && i >= 0 && rows[i].has_file) {
        e.preventDefault();
        this.open(rows[i].id);
      }
    });
    document.getElementById("lib-back").addEventListener("click", () => this.close());
    document.getElementById("lib-zoom-in").addEventListener("click", () => this._zoom(1.2));
    document.getElementById("lib-zoom-out").addEventListener("click", () => this._zoom(1 / 1.2));
    document.querySelectorAll(".lib-side-tab").forEach(tab => {
      tab.addEventListener("click", () => this._showSide(tab.dataset.side));
    });
    const pages = document.getElementById("lib-pages");
    pages.addEventListener("mouseup", (e) => setTimeout(() => this._onMouseUp(e), 0));
    // Esc cierra el menú; un clic fuera también
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      if (!document.getElementById("lib-popup").classList.contains("hidden")) {
        e.preventDefault();
        this._closePopup();
      }
      if (!document.getElementById("lib-dict-popup").classList.contains("hidden")) {
        e.preventDefault();
        this._closeDict();
      }
    });
    document.addEventListener("mousedown", (e) => {
      const popup = document.getElementById("lib-popup");
      if (!popup.classList.contains("hidden") && !popup.contains(e.target)) this._closePopup();
      const dict = document.getElementById("lib-dict-popup");
      if (!dict.classList.contains("hidden") && !dict.contains(e.target)) this._closeDict();
    });
  },

  /* ---------- Lista ---------- */

  async render() {
    if (this.current) {
      await this._loadMarks();
      this._redrawMarks();
      this._renderNotes();
      return;
    }
    await this.loadItems();
    this._renderList();
    this._renderDictStatus();
  },

  async loadItems() {
    try {
      const { items } = await API.library();
      this.items = items;
    } catch (error) {
      Views.toast(error.message, true);
    }
    return this.items;
  },

  item(id) { return this.items.find(i => i.id === id); },

  _authorsShort(meta) {
    const names = (meta.authors || []).map(a => a.family).filter(Boolean);
    if (!names.length) return "";
    if (names.length <= 2) return names.join(" & ");
    return `${names[0]} et al.`;
  },

  /* ---------- Tabla (al estilo Finder / Mendeley) ---------- */

  COLUMNS: ["kind", "author", "title", "container", "year", "notes"],

  _authorKey(item) {
    const first = (item.meta.authors || [])[0];
    return first ? first.family : "";
  },

  _value(item, key) {
    if (key === "author") return this._authorsShort(item.meta);
    if (key === "title") return item.meta.title || item.filename;
    if (key === "container") return item.meta.container || "";
    if (key === "year") return item.meta.year || "";
    return "";
  },

  _plain(text) {
    return (text || "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  },

  /* Filtro de año: «2019», «2015-2020», «>2018», «<2000», «2018-» */
  _yearMatches(year, filter) {
    filter = filter.replace(/\s+/g, "").replace("–", "-");
    if (!filter) return true;
    const y = parseInt(year, 10);
    let m;
    if ((m = filter.match(/^(\d{4})-(\d{4})$/))) return y >= +m[1] && y <= +m[2];
    if ((m = filter.match(/^(\d{4})-$/))) return y >= +m[1];
    if ((m = filter.match(/^-(\d{4})$/))) return y <= +m[1];
    if ((m = filter.match(/^(>=|<=|>|<)(\d{4})$/))) {
      const n = +m[2];
      return { ">": y > n, "<": y < n, ">=": y >= n, "<=": y <= n }[m[1]];
    }
    return (year || "").startsWith(filter);
  },

  _filtered() {
    const q = this._plain(this.query);
    const f = this.filters;
    const people = (item) => this._plain((item.meta.authors || []).map(a => `${a.family} ${a.given}`).join(" "));
    const rows = this.items.filter(item => {
      if (q && !this._plain([item.meta.title, item.meta.year, item.meta.container, item.filename,
        item.meta.publisher, item.meta.doi].join(" ") + " " + people(item)).includes(q)) return false;
      if (f.author && !people(item).includes(this._plain(f.author))) return false;
      if (f.title && !this._plain(item.meta.title || item.filename).includes(this._plain(f.title))) return false;
      if (f.container && !this._plain(item.meta.container).includes(this._plain(f.container))) return false;
      if (f.year && !this._yearMatches(item.meta.year, f.year)) return false;
      return true;
    });
    const { key, dir } = this.sort;
    const val = (item) => (key === "author" ? this._plain(this._authorKey(item))
      : key === "year" ? parseInt(item.meta.year, 10) : this._plain(this._value(item, key)));
    return rows.sort((a, b) => {
      const va = val(a), vb = val(b);
      const emptyA = va === "" || Number.isNaN(va), emptyB = vb === "" || Number.isNaN(vb);
      if (emptyA !== emptyB) return emptyA ? 1 : -1; // sin dato: siempre al final
      if (va < vb) return -dir;
      if (va > vb) return dir;
      return this._plain(this._value(a, "title")).localeCompare(this._plain(this._value(b, "title")));
    });
  },

  _renderList() {
    const box = document.getElementById("lib-list");
    box.textContent = "";
    if (!this.items.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = I18N.t("lib.empty");
      box.appendChild(p);
      this._renderDetail();
      return;
    }
    const rows = this._visible = this._filtered();
    const browser = document.createElement("div");
    browser.className = "lib-browser";
    const wrap = document.createElement("div");
    wrap.className = "lib-table-wrap";
    const table = document.createElement("table");
    table.className = "lib-table";
    const head = document.createElement("thead");
    const titles = document.createElement("tr");
    const filters = document.createElement("tr");
    filters.className = "lib-filter-row";
    for (const key of this.COLUMNS) {
      const th = document.createElement("th");
      th.className = `lib-col-${key}`;
      const sortable = ["author", "title", "container", "year"].includes(key);
      th.textContent = I18N.t(`lib.col.${key}`);
      if (sortable) {
        th.classList.add("sortable");
        if (this.sort.key === key) th.textContent += this.sort.dir > 0 ? " ▲" : " ▼";
        th.title = I18N.t("lib.sort.title");
        th.addEventListener("click", () => {
          this.sort = this.sort.key === key ? { key, dir: -this.sort.dir } : { key, dir: key === "year" ? -1 : 1 };
          try { localStorage.setItem("cua-lib-sort", JSON.stringify(this.sort)); } catch (_) { /* sin almacenamiento */ }
          this._renderList();
        });
      }
      titles.appendChild(th);
      const cell = document.createElement("th");
      if (sortable) {
        const input = document.createElement("input");
        input.type = "search";
        input.className = "lib-filter";
        input.dataset.filter = key;
        input.value = this.filters[key];
        input.placeholder = I18N.t(`lib.filter.${key}`);
        input.addEventListener("input", () => {
          this.filters[key] = input.value.trim();
          this._renderRows(table);
        });
        cell.appendChild(input);
      }
      filters.appendChild(cell);
    }
    head.append(titles, filters);
    table.appendChild(head);
    table.appendChild(document.createElement("tbody"));
    wrap.appendChild(table);
    const detail = document.createElement("aside");
    detail.id = "lib-detail";
    detail.className = "panel lib-detail";
    browser.append(wrap, detail);
    box.appendChild(browser);
    this._renderRows(table);
  },

  /* Solo las filas: escribir en un filtro no reconstruye los campos (no se pierde el foco). */
  _renderRows(table) {
    const rows = this._visible = this._filtered();
    const body = table.tBodies[0];
    body.textContent = "";
    for (const item of rows) {
      const tr = document.createElement("tr");
      tr.dataset.id = item.id;
      if (item.id === this.selectedId) tr.classList.add("selected");
      for (const key of this.COLUMNS) {
        const td = document.createElement("td");
        td.className = `lib-col-${key}`;
        if (key === "kind") {
          td.textContent = I18N.t(`lib.kind.short.${item.kind}`);
          td.title = I18N.t(`lib.kind.${item.kind}`);
        } else if (key === "notes") {
          const parts = [];
          if (item.annotations) parts.push(`✎${item.annotations}`);
          if (item.codings) parts.push(`◉${item.codings}`);
          td.textContent = parts.join(" ");
          td.title = I18N.t("lib.counts", { a: item.annotations, c: item.codings });
        } else {
          td.textContent = this._value(item, key) || "—";
          if (key === "title") td.title = item.meta.title || item.filename;
          if (!this._value(item, key)) td.classList.add("muted");
        }
        tr.appendChild(td);
      }
      tr.addEventListener("click", () => this._select(item.id));
      tr.addEventListener("dblclick", () => { if (item.has_file) this.open(item.id); });
      body.appendChild(tr);
    }
    const count = document.getElementById("lib-count");
    if (count) count.textContent = I18N.t("lib.count", { n: rows.length, total: this.items.length });
    if (this.selectedId && !this.items.some(i => i.id === this.selectedId)) this.selectedId = null;
    this._renderDetail();
  },

  _select(id, scroll = false) {
    this.selectedId = id;
    this._editingMeta = false;
    document.querySelectorAll("#lib-list .lib-table tbody tr").forEach(tr =>
      tr.classList.toggle("selected", tr.dataset.id === id));
    if (scroll) {
      const row = document.querySelector(`#lib-list .lib-table tbody tr[data-id="${id}"]`);
      if (row) row.scrollIntoView({ block: "nearest" });
    }
    this._renderDetail();
  },

  /* Panel de detalle del documento elegido (como en Mendeley). */
  _renderDetail() {
    const box = document.getElementById("lib-detail");
    if (!box) return;
    box.textContent = "";
    const item = this.item(this.selectedId);
    if (!item) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = I18N.t("lib.detail.empty");
      box.appendChild(p);
      return;
    }
    if (this._editingMeta) {
      this._renderMeta(item, box);
      return;
    }
    const kind = document.createElement("div");
    kind.className = "mini-label";
    kind.textContent = `${I18N.t(`lib.kind.${item.kind}`)} · ${I18N.t(`lib.type.${item.meta.type}`)}`;
    const title = document.createElement("div");
    title.className = "lib-detail-title";
    title.textContent = item.meta.title || item.filename;
    const people = document.createElement("div");
    people.className = "lib-detail-people";
    people.textContent = (item.meta.authors || []).map(a => a.given ? `${a.given} ${a.family}` : a.family).join(", ");
    const where = document.createElement("div");
    where.className = "lib-detail-where";
    where.textContent = [item.meta.container, item.meta.year].filter(Boolean).join(" · ");
    box.append(kind, title, people, where);
    const apa = document.createElement("div");
    apa.className = "lib-apa";
    const label = document.createElement("div");
    label.className = "mini-label";
    label.textContent = I18N.t("lib.apa");
    const ref = document.createElement("div");
    ref.className = "lib-apa-text";
    ref.innerHTML = item.apa; // generado por el servidor con el texto escapado
    apa.append(label, ref);
    box.appendChild(apa);
    const counts = document.createElement("div");
    counts.className = "mini-label lib-detail-counts";
    counts.textContent = I18N.t("lib.counts", { a: item.annotations, c: item.codings });
    box.appendChild(counts);
    const buttons = document.createElement("div");
    buttons.className = "lib-meta-buttons";
    if (item.has_file) {
      const open = document.createElement("button");
      open.className = "btn btn-small btn-accent";
      open.textContent = I18N.t("lib.open");
      open.addEventListener("click", () => this.open(item.id));
      buttons.appendChild(open);
    }
    const edit = document.createElement("button");
    edit.className = "btn btn-small";
    edit.textContent = I18N.t("lib.detail.edit");
    edit.addEventListener("click", () => { this._editingMeta = true; this._renderDetail(); });
    const del = document.createElement("button");
    del.className = "btn btn-small";
    del.textContent = I18N.t("lib.detail.delete");
    del.addEventListener("click", () => this._delete(item));
    buttons.append(edit, del);
    box.appendChild(buttons);
    if (item.has_file) {
      const hint = document.createElement("p");
      hint.className = "empty-note";
      hint.textContent = I18N.t("lib.detail.hint");
      box.appendChild(hint);
    }
  },

  async _import(event) {
    const files = [...event.target.files];
    event.target.value = "";
    if (!files.length) return;
    const status = document.getElementById("lib-status");
    for (const [i, file] of files.entries()) {
      status.textContent = I18N.t("import.progress", { name: file.name, i: i + 1, n: files.length });
      try {
        const item = await API.addLibraryItem(file);
        if (item.duplicate) Views.toast(I18N.t("lib.duplicate", { name: file.name }));
        else Views.toast(I18N.t(item.doi_found ? "lib.added.doi" : "lib.added", { name: item.meta.title || file.name }));
      } catch (error) {
        Views.toast(`${file.name}: ${error.message}`, true);
      }
    }
    status.textContent = "";
    await this.loadItems();
    this._renderList();
  },

  async _delete(item) {
    try {
      await API.deleteLibraryItem(item.id, false);
    } catch (error) {
      if (error.status !== 409) { Views.toast(error.message, true); return; }
      const n = Number(error.headers.get("X-Coding-Count") || 0);
      const message = I18N.t(n ? "lib.delete.confirm.codings" : "lib.delete.confirm",
        { name: item.meta.title || item.filename, n });
      if (!await Views.confirm(message)) return;
      try {
        await API.deleteLibraryItem(item.id, true);
      } catch (err) {
        Views.toast(err.message, true);
        return;
      }
    }
    await this.loadItems();
    await State.reload();
    this._renderList();
    Views.toast(I18N.t("lib.deleted"));
  },

  /* Agregar a la biblioteca una referencia encontrada en OpenAlex (por su DOI). */
  async addReference(doi) {
    try {
      const item = await API.addReference(doi);
      Views.toast(I18N.t(item.duplicate ? "lib.ref.duplicate" : "lib.ref.added", { name: item.meta.title }));
      await this.loadItems();
      this._renderList();
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  /* ---------- Lector ---------- */

  async open(id, focus = null) {
    if (!this.items.length || !this.item(id)) await this.loadItems();
    const item = this.item(id);
    if (!item || !item.has_file) return;
    this.current = item;
    this._closePopup();
    document.getElementById("lib-home").classList.add("hidden");
    document.getElementById("lib-reader").classList.remove("hidden");
    document.getElementById("lib-reader-title").textContent = this._readerTitle(item);
    document.getElementById("lib-zoom-in").parentElement.classList.toggle("hidden", item.kind !== "pdf");
    await this._loadMarks();
    this._renderNotes();
    this._renderMeta();
    if (item.kind === "pdf") await this._openPdf(item);
    else await this._openText(item);
    if (focus) this.focusMark(focus);
  },

  /* Título del lector: con (Autoría, año) solo si la ficha tiene autoría
     (sin ella, la cita breve repetiría el título). */
  _readerTitle(item) {
    const title = item.meta.title || item.filename;
    return (item.meta.authors || []).length ? `${title} (${item.cite})` : title;
  },

  close() {
    this._closePopup();
    if (this._observer) this._observer.disconnect();
    if (this._pdf) { this._pdf.destroy(); this._pdf = null; }
    this.current = null;
    document.getElementById("lib-pages").textContent = "";
    document.getElementById("lib-reader").classList.add("hidden");
    document.getElementById("lib-home").classList.remove("hidden");
    this.render();
  },

  async _loadMarks() {
    if (!this.current) return;
    try {
      const { annotations, codings } = await API.libraryAnnotations(this.current.id);
      this.annotations = annotations;
      this.codings = codings;
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _openPdf(item) {
    const pages = document.getElementById("lib-pages");
    pages.textContent = I18N.t("dlg.loading");
    try {
      this._pdf = await pdfjsLib.getDocument({
        url: `/api/library/items/${item.id}/file`,
        standardFontDataUrl: "/static/vendor/pdfjs/standard_fonts/",
      }).promise;
    } catch (error) {
      pages.textContent = I18N.t("lib.pdf.error");
      return;
    }
    const first = await this._pdf.getPage(1);
    const base = first.getViewport({ scale: 1 });
    this._baseSize = { width: base.width, height: base.height };
    // Ajuste al ancho disponible
    const available = Math.max(320, pages.clientWidth - 30);
    this.scale = Math.max(0.5, Math.min(2.5, available / base.width));
    this._layoutPages();
  },

  _layoutPages() {
    const pages = document.getElementById("lib-pages");
    pages.textContent = "";
    this._rendered = new Set();
    if (this._observer) this._observer.disconnect();
    document.getElementById("lib-zoom-value").textContent = `${Math.round(this.scale * 100)}%`;
    this._observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) this._renderPage(Number(entry.target.dataset.page));
      }
    }, { root: null, rootMargin: "800px 0px" });
    for (let n = 1; n <= this._pdf.numPages; n++) {
      const page = document.createElement("div");
      page.className = "lib-page";
      page.dataset.page = String(n);
      page.style.width = `${this._baseSize.width * this.scale}px`;
      page.style.height = `${this._baseSize.height * this.scale}px`;
      const number = document.createElement("div");
      number.className = "lib-page-number";
      number.textContent = String(n);
      page.appendChild(number);
      pages.appendChild(page);
      this._observer.observe(page);
    }
  },

  async _renderPage(n) {
    if (this._rendered.has(n) || !this._pdf) return;
    this._rendered.add(n);
    const pageEl = document.querySelector(`#lib-pages .lib-page[data-page="${n}"]`);
    if (!pageEl) return;
    const page = await this._pdf.getPage(n);
    const viewport = page.getViewport({ scale: this.scale });
    pageEl.style.width = `${viewport.width}px`;
    pageEl.style.height = `${viewport.height}px`;
    const ratio = window.devicePixelRatio || 1;
    const canvas = document.createElement("canvas");
    canvas.width = Math.floor(viewport.width * ratio);
    canvas.height = Math.floor(viewport.height * ratio);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;
    const marks = document.createElement("div");
    marks.className = "lib-marks";
    const textLayer = document.createElement("div");
    textLayer.className = "textLayer";
    textLayer.style.setProperty("--scale-factor", this.scale);
    pageEl.append(canvas, marks, textLayer);
    await page.render({ canvasContext: canvas.getContext("2d"), viewport,
      transform: ratio !== 1 ? [ratio, 0, 0, ratio, 0, 0] : null }).promise;
    await pdfjsLib.renderTextLayer({ textContentSource: page.streamTextContent(),
      container: textLayer, viewport, textDivs: [] }).promise;
    this._drawPageMarks(n);
  },

  _zoom(factor) {
    if (!this._pdf) return;
    this.scale = Math.max(0.4, Math.min(3, this.scale * factor));
    // Conserva la página a la vista
    const pages = [...document.querySelectorAll("#lib-pages .lib-page")];
    const visible = pages.find(p => p.getBoundingClientRect().bottom > 120);
    const keep = visible ? Number(visible.dataset.page) : 1;
    this._layoutPages();
    const target = document.querySelector(`#lib-pages .lib-page[data-page="${keep}"]`);
    if (target) target.scrollIntoView({ block: "start" });
  },

  async _openText(item) {
    const pages = document.getElementById("lib-pages");
    pages.textContent = I18N.t("dlg.loading");
    try {
      const { text } = await API.libraryText(item.id);
      this._text = text || "";
    } catch (error) {
      pages.textContent = error.message;
      return;
    }
    this._drawText();
  },

  /* Texto continuo con segmentos planos (como el Canvas: nunca etiquetas anidadas). */
  _drawText() {
    const pages = document.getElementById("lib-pages");
    pages.textContent = "";
    const box = document.createElement("div");
    box.className = "lib-text";
    const text = this._text;
    const marks = [
      ...this.annotations.filter(a => a.start != null).map(a => ({ ...a, _type: "ann" })),
      ...this.codings.filter(c => c.start != null).map(c => ({ ...c, _type: "cod" })),
    ];
    const cuts = new Set([0, text.length]);
    for (const m of marks) { cuts.add(Math.min(m.start, text.length)); cuts.add(Math.min(m.end, text.length)); }
    const points = [...cuts].sort((a, b) => a - b);
    for (let i = 0; i < points.length - 1; i++) {
      const a = points[i], b = points[i + 1];
      if (a === b) continue;
      const span = document.createElement("span");
      span.textContent = text.slice(a, b);
      const over = marks.filter(m => m.start <= a && m.end >= b);
      if (over.length) this._styleTextSpan(span, over);
      box.appendChild(span);
    }
    pages.appendChild(box);
  },

  _styleTextSpan(span, over) {
    const decorations = [];
    const shadows = [];
    for (const m of over) {
      if (m._type === "cod") {
        shadows.push(`inset 0 -3px 0 ${State.domains[m.domain] || "#999"}`);
        continue;
      }
      if (m.kind === "highlight" || m.kind === "note") span.style.backgroundColor = this._alpha(m.color, 0.4);
      if (m.kind === "underline") { decorations.push("underline"); span.style.textDecorationColor = m.color; }
      if (m.kind === "strike") { decorations.push("line-through"); span.style.textDecorationColor = m.color; }
      if (m.kind === "note") span.classList.add("lib-has-note");
    }
    if (decorations.length) {
      span.style.textDecorationLine = decorations.join(" ");
      span.style.textDecorationThickness = "2px";
    }
    if (shadows.length) span.style.boxShadow = shadows.join(", ");
    span.dataset.marks = over.map(m => `${m._type}:${m.id}`).join(" ");
  },

  _alpha(hex, a) {
    const n = parseInt((hex || "#FFCC00").slice(1), 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
  },

  /* ---------- Marcas sobre el PDF ---------- */

  _redrawMarks() {
    if (!this.current) return;
    if (this.current.kind === "pdf") for (const n of this._rendered) this._drawPageMarks(n);
    else this._drawText();
  },

  _drawPageMarks(n) {
    const pageEl = document.querySelector(`#lib-pages .lib-page[data-page="${n}"]`);
    const layer = pageEl && pageEl.querySelector(".lib-marks");
    if (!layer) return;
    layer.textContent = "";
    const add = (r, cls, style) => {
      const d = document.createElement("div");
      d.className = cls;
      Object.assign(d.style, { left: `${r[0] * 100}%`, top: `${r[1] * 100}%`,
        width: `${r[2] * 100}%`, height: `${r[3] * 100}%`, ...style });
      layer.appendChild(d);
      return d;
    };
    for (const a of this.annotations.filter(x => x.page === n)) {
      a.rects.forEach((r, i) => {
        if (a.kind === "highlight" || a.kind === "note") add(r, "lib-mark", { background: this._alpha(a.color, 0.38) });
        if (a.kind === "underline") add([r[0], r[1] + r[3] - 0.0022, r[2], 0.0022], "lib-mark", { background: a.color });
        if (a.kind === "strike") add([r[0], r[1] + r[3] * 0.52, r[2], 0.0018], "lib-mark", { background: a.color });
        if (a.kind === "note" && i === a.rects.length - 1) {
          const pin = add([r[0] + r[2], r[1] - 0.004, 0.018, 0.016], "lib-note-pin", {});
          pin.textContent = "✎";
        }
      });
    }
    for (const c of this.codings.filter(x => x.page === n)) {
      const color = State.domains[c.domain] || "#999999";
      c.rects.forEach((r, i) => {
        add(r, "lib-mark lib-coding", { boxShadow: `inset 0 -3px 0 ${color}`, outline: `1px solid ${this._alpha(color, 0.7)}` });
        if (i === 0) {
          const tag = add([r[0], r[1] - 0.016, 0.3, 0.015], "lib-coding-tag", { color: "#000" });
          tag.textContent = c.name;
          tag.style.borderLeft = `6px solid ${color}`;
        }
      });
    }
  },

  /* ---------- Selección → menú efímero ---------- */

  _onMouseUp(event) {
    if (!this.current) return;
    const selection = window.getSelection();
    if (event.detail === 2 && selection.rangeCount && !selection.isCollapsed) {
      // Doble clic sobre una palabra: diccionario (FR-093). Para anotar una sola
      // palabra, basta con seleccionarla arrastrando.
      const word = selection.toString().trim();
      const rect = selection.getRangeAt(0).getBoundingClientRect();
      if (word && !/\s/.test(word)) {
        this._closePopup();
        this.lookup(word, rect);
        return;
      }
    }
    if (!selection.rangeCount || selection.isCollapsed) {
      this._hitTest(event);
      return;
    }
    const range = selection.getRangeAt(0);
    const quote = selection.toString().replace(/\s+/g, " ").trim();
    if (!quote) return;
    let anchor;
    if (this.current.kind === "pdf") {
      const startPage = this._pageOf(range.startContainer);
      const endPage = this._pageOf(range.endContainer);
      if (!startPage || startPage !== endPage) {
        Views.toast(I18N.t("lib.onepage"), true);
        return;
      }
      const rects = this._rects(range, startPage);
      if (!rects.length) return;
      anchor = { page: Number(startPage.dataset.page), rects };
    } else {
      const box = document.querySelector("#lib-pages .lib-text");
      if (!box || !box.contains(range.startContainer) || !box.contains(range.endContainer)) return;
      const before = document.createRange();
      before.setStart(box, 0);
      before.setEnd(range.startContainer, range.startOffset);
      const start = before.toString().length;
      const end = start + range.toString().length;
      if (end <= start) return;
      anchor = { start, end };
    }
    this._pending = { anchor: { item_id: this.current.id, quote, ...anchor } };
    const last = range.getClientRects();
    const rect = last.length ? last[last.length - 1] : range.getBoundingClientRect();
    this._openPopup(rect);
  },

  _pageOf(node) {
    const el = node.nodeType === 1 ? node : node.parentElement;
    return el ? el.closest(".lib-page") : null;
  },

  /* Rectángulos de la selección, unidos por línea, en fracciones de la página. */
  _rects(range, pageEl) {
    const box = pageEl.getBoundingClientRect();
    const raw = [...range.getClientRects()].filter(r => r.width > 0.5 && r.height > 0.5)
      .sort((a, b) => a.top - b.top || a.left - b.left);
    const lines = [];
    for (const r of raw) {
      const last = lines[lines.length - 1];
      if (last && Math.abs(r.top - last.top) < r.height * 0.6 && r.left <= last.right + 6) {
        last.right = Math.max(last.right, r.right);
        last.top = Math.min(last.top, r.top);
        last.bottom = Math.max(last.bottom, r.bottom);
      } else {
        lines.push({ left: r.left, right: r.right, top: r.top, bottom: r.bottom });
      }
    }
    const clamp = (v) => Math.max(0, Math.min(1, v));
    return lines.map(l => [clamp((l.left - box.left) / box.width), clamp((l.top - box.top) / box.height),
      clamp((l.right - l.left) / box.width), clamp((l.bottom - l.top) / box.height)])
      .filter(r => r[2] > 0 && r[3] > 0);
  },

  /* Clic sin selección: ¿cayó sobre una anotación o un pasaje codificado? */
  _hitTest(event) {
    if (!this.current) return;
    if (this.current.kind !== "pdf") {
      const span = event.target.closest && event.target.closest("[data-marks]");
      if (span) this.focusMark(span.dataset.marks.split(" ")[0], false);
      return;
    }
    const pageEl = event.target.closest && event.target.closest(".lib-page");
    if (!pageEl) return;
    const box = pageEl.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width, y = (event.clientY - box.top) / box.height;
    const n = Number(pageEl.dataset.page);
    const inside = (r) => x >= r[0] && x <= r[0] + r[2] && y >= r[1] - 0.004 && y <= r[1] + r[3] + 0.004;
    const coding = this.codings.find(c => c.page === n && c.rects.some(inside));
    const annotation = this.annotations.find(a => a.page === n && a.rects.some(inside));
    // La marca está bajo el cursor: solo se destaca en el panel, sin mover la
    // página (si se moviera, el segundo clic de un doble clic caería en otra palabra)
    if (coding) this.focusMark(`cod:${coding.id}`, false);
    else if (annotation) this.focusMark(`ann:${annotation.id}`, false);
  },

  _openPopup(rect) {
    const popup = document.getElementById("lib-popup");
    this._popupMode = "main";
    this._drawPopup();
    popup.classList.remove("hidden");
    const width = popup.offsetWidth || 320;
    const left = Math.min(window.innerWidth - width - 12, Math.max(12, rect.left));
    const top = rect.bottom + 8 + popup.offsetHeight > window.innerHeight
      ? Math.max(12, rect.top - popup.offsetHeight - 8) : rect.bottom + 8;
    popup.style.left = `${left}px`;
    popup.style.top = `${top}px`;
  },

  _closePopup() {
    document.getElementById("lib-popup").classList.add("hidden");
    this._pending = null;
  },

  _drawPopup() {
    const popup = document.getElementById("lib-popup");
    popup.textContent = "";
    const title = document.createElement("div");
    title.className = "nube-title";
    title.textContent = I18N.t("lib.popup.title");
    popup.appendChild(title);
    if (this._popupMode === "main") {
      const row = document.createElement("div");
      row.className = "lib-popup-row";
      for (const color of this.COLORS) {
        const swatch = document.createElement("button");
        swatch.type = "button";
        swatch.className = "lib-swatch";
        swatch.style.backgroundColor = color;
        swatch.title = I18N.t("lib.highlight");
        swatch.addEventListener("click", () => this._annotate("highlight", color));
        row.appendChild(swatch);
      }
      const tool = (label, title, fn) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "lib-tool";
        b.textContent = label;
        b.title = title;
        b.addEventListener("click", fn);
        row.appendChild(b);
        return b;
      };
      tool("U̲", I18N.t("lib.underline"), () => this._annotate("underline", "#0066FF"));
      tool("S̶", I18N.t("lib.strike"), () => this._annotate("strike", "#CC0000"));
      tool("✎", I18N.t("lib.note"), () => { this._popupMode = "note"; this._drawPopup(); });
      popup.appendChild(row);
      const code = document.createElement("button");
      code.type = "button";
      code.className = "lib-code-btn";
      code.textContent = I18N.t("lib.code");
      code.addEventListener("click", () => { this._popupMode = "code"; this._drawPopup(); });
      popup.appendChild(code);
    } else if (this._popupMode === "note") {
      const area = document.createElement("textarea");
      area.className = "lib-popup-input";
      area.rows = 3;
      area.placeholder = I18N.t("lib.note.placeholder");
      area.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this._annotate("note", "#FFCC00", area.value.trim());
        }
      });
      popup.appendChild(area);
      const hint = document.createElement("div");
      hint.className = "nube-hint";
      hint.textContent = I18N.t("lib.note.hint");
      popup.appendChild(hint);
      setTimeout(() => area.focus(), 0);
    } else {
      // Codificar con los códigos y categorías del proyecto activo (FR-091)
      const domain = document.createElement("select");
      domain.className = "lib-popup-input";
      // La Nube Negra del Canvas no se toca (Principio III): este menú recuerda su propia categoría
      Paleta._fillDomainSelect(domain, this._lastDomain || (Nube.last && Nube.last.domain)
        || Object.keys(State.basicDomains)[0]);
      const name = document.createElement("input");
      name.type = "text";
      name.className = "lib-popup-input";
      name.maxLength = 200;
      name.autocomplete = "off";
      name.placeholder = I18N.t("lib.code.placeholder");
      name.setAttribute("list", "lib-code-names");
      const list = document.createElement("datalist");
      list.id = "lib-code-names";
      const domains = new Map();
      for (const c of State.project.codes) domains.set(c.name, c.domain);
      for (const n of [...domains.keys()].sort((a, b) => a.localeCompare(b, I18N.locale))) {
        const option = document.createElement("option");
        option.value = n;
        list.appendChild(option);
      }
      // Elegir un código existente propone su categoría
      name.addEventListener("input", () => {
        if (domains.has(name.value.trim())) domain.value = domains.get(name.value.trim());
      });
      name.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          this._code(name.value.trim(), domain.value);
        }
      });
      popup.append(domain, name, list);
      const hint = document.createElement("div");
      hint.className = "nube-hint";
      hint.textContent = I18N.t("lib.code.hint", { project: State.project.name });
      popup.appendChild(hint);
      setTimeout(() => name.focus(), 0);
    }
  },

  async _annotate(kind, color, comment = "") {
    const pending = this._pending;
    if (!pending) return;
    try {
      await API.createAnnotation({ ...pending.anchor, kind, color, comment });
      window.getSelection().removeAllRanges();
      this._closePopup();
      await this._afterChange();
      Views.toast(I18N.t(`lib.done.${kind}`));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _code(name, domain) {
    const pending = this._pending;
    if (!pending || !name || !domain) {
      if (!name) Views.toast(I18N.t("manual.missing"), true);
      return;
    }
    try {
      // Código nuevo: se crea como código manual del proyecto, para que exista
      // en el banco, el libro de códigos y las relaciones
      if (!State.project.codes.some(c => c.name === name)) {
        await API.createCode({ domain, name, memo: "" });
      }
      await API.createLitCoding({ ...pending.anchor, name, domain });
      this._lastDomain = domain;
      window.getSelection().removeAllRanges();
      this._closePopup();
      await State.reload(); // banco, libro de códigos y análisis al día
      Views.toast(I18N.t("lib.coded", { name }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _afterChange() {
    await this._loadMarks();
    this._redrawMarks();
    this._renderNotes();
    const item = this.current && this.item(this.current.id);
    if (item) {
      item.annotations = this.annotations.length;
      item.codings = this.codings.length;
    }
  },

  /* ---------- Diccionario (FR-093): solo consulta ---------- */

  _dictTimer: null,

  async _renderDictStatus() {
    const box = document.getElementById("lib-dict");
    let languages;
    try {
      ({ languages } = await API.dictionaryStatus());
    } catch (error) {
      return;
    }
    box.textContent = "";
    const langs = Object.entries(languages);
    const ready = langs.every(([, v]) => v.installed);
    const working = langs.filter(([, v]) => v.progress && ["queued", "downloading", "building"].includes(v.progress.state));
    const text = document.createElement("span");
    if (ready) {
      text.textContent = I18N.t("dict.ready");
    } else if (working.length) {
      text.textContent = I18N.t("dict.working", { detail: langs.map(([lang, v]) => this._dictProgress(lang, v)).join(" · ") });
    } else {
      const failed = langs.some(([, v]) => v.progress && v.progress.state === "error");
      text.textContent = I18N.t(failed ? "dict.failed" : "dict.missing");
      const button = document.createElement("button");
      button.className = "btn btn-small";
      button.textContent = I18N.t("dict.download");
      button.addEventListener("click", async () => {
        try {
          await API.dictionaryDownload();
          this._renderDictStatus();
        } catch (error) {
          Views.toast(error.message, true);
        }
      });
      box.append(text, button);
      return;
    }
    box.appendChild(text);
    clearTimeout(this._dictTimer);
    if (working.length) {
      this._dictTimer = setTimeout(() => {
        if (Views.current === "literatura") this._renderDictStatus();
        const popup = document.getElementById("lib-dict-popup");
        if (!popup.classList.contains("hidden") && this._dictLast) this.lookup(...this._dictLast);
      }, 1500);
    }
  },

  _dictProgress(lang, v) {
    const name = lang.toUpperCase();
    if (v.installed) return `${name} ✓`;
    const p = v.progress || {};
    if (p.state === "downloading" && p.total) return `${name} ${Math.round((p.done / p.total) * 100)}%`;
    if (p.state === "building") return `${name} ${I18N.t("dict.building")}`;
    if (p.state === "queued") return `${name} …`;
    if (p.state === "error") return `${name} ✕`;
    return `${name} —`;
  },

  async lookup(word, rect, lang = "") {
    this._dictLast = [word, rect, lang];
    const popup = document.getElementById("lib-dict-popup");
    // Respuesta inmediata: la primera consulta carga el modelo lingüístico y tarda un poco
    if (popup.classList.contains("hidden") || popup.dataset.word !== word) {
      popup.textContent = "";
      const wait = document.createElement("div");
      wait.className = "lib-dict-word";
      wait.textContent = word;
      const note = document.createElement("p");
      note.className = "empty-note";
      note.textContent = I18N.t("dict.searching");
      popup.append(wait, note);
      popup.classList.remove("hidden");
      popup.style.left = `${Math.min(window.innerWidth - 392, Math.max(12, rect.left))}px`;
      popup.style.top = `${rect.bottom + 8}px`;
    }
    popup.dataset.word = word;
    let data;
    try {
      data = await API.dictionaryLookup(word, lang, this.current ? this.current.id : "");
    } catch (error) {
      Views.toast(error.message, true);
      return;
    }
    popup.textContent = "";
    const head = document.createElement("div");
    head.className = "lib-dict-head";
    const title = document.createElement("span");
    title.className = "lib-dict-word";
    title.textContent = data.word;
    const chips = document.createElement("span");
    chips.className = "lib-dict-langs";
    for (const code of ["es", "en", "pt"]) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "lib-dict-lang" + (code === data.lang ? " active" : "");
      chip.textContent = code.toUpperCase();
      chip.title = I18N.t("dict.lang.title", { language: I18N.t(`langname.${code}`) });
      chip.addEventListener("click", () => this.lookup(word, rect, code));
      chips.appendChild(chip);
    }
    head.append(title, chips);
    popup.appendChild(head);
    const body = document.createElement("div");
    body.className = "lib-dict-body";
    if (!data.installed) {
      const p = document.createElement("p");
      p.textContent = I18N.t("dict.missing");
      body.appendChild(p);
      const status = document.createElement("div");
      status.id = "lib-dict-popup-status";
      body.appendChild(status);
      const button = document.createElement("button");
      button.className = "btn btn-small";
      button.textContent = I18N.t("dict.download");
      button.addEventListener("click", async () => {
        await API.dictionaryDownload();
        this._renderDictStatus();
        button.disabled = true;
        button.textContent = I18N.t("dict.downloading");
      });
      body.appendChild(button);
    } else if (!data.groups.length) {
      const p = document.createElement("p");
      p.textContent = I18N.t("dict.none");
      body.appendChild(p);
    } else {
      for (const note of data.form_notes || []) {
        const p = document.createElement("p");
        p.className = "lib-dict-note";
        p.textContent = note;
        body.appendChild(p);
      }
      for (const group of data.groups) {
        if (group.is_lemma) {
          const lemma = document.createElement("div");
          lemma.className = "lib-dict-lemma";
          lemma.textContent = `→ ${group.headword}`;
          body.appendChild(lemma);
        }
        for (const entry of group.entries) {
          const pos = document.createElement("div");
          pos.className = "lib-dict-pos";
          pos.textContent = entry.pos;
          const list = document.createElement("ol");
          list.className = "lib-dict-senses";
          entry.senses.forEach((sense, i) => {
            const li = document.createElement("li");
            li.textContent = sense;
            if (i >= 4) li.classList.add("lib-dict-extra", "hidden");
            list.appendChild(li);
          });
          body.append(pos, list);
          if (entry.senses.length > 4) {
            const more = document.createElement("button");
            more.type = "button";
            more.className = "lib-dict-more";
            more.textContent = I18N.t("dict.more", { n: entry.senses.length - 4 });
            more.addEventListener("click", () => {
              list.querySelectorAll(".lib-dict-extra").forEach(li => li.classList.remove("hidden"));
              more.remove();
            });
            body.appendChild(more);
          }
        }
      }
    }
    popup.appendChild(body);
    const source = document.createElement("div");
    source.className = "lib-dict-source";
    source.textContent = `${data.source} · ${data.license}`;
    popup.appendChild(source);
    popup.classList.remove("hidden");
    const width = popup.offsetWidth || 360;
    popup.style.left = `${Math.min(window.innerWidth - width - 12, Math.max(12, rect.left))}px`;
    const below = rect.bottom + 8;
    popup.style.top = `${below + popup.offsetHeight > window.innerHeight
      ? Math.max(12, rect.top - popup.offsetHeight - 8) : below}px`;
  },

  _closeDict() {
    document.getElementById("lib-dict-popup").classList.add("hidden");
    this._dictLast = null;
  },

  /* ---------- Panel lateral ---------- */

  _showSide(which) {
    document.querySelectorAll(".lib-side-tab").forEach(t => t.classList.toggle("active", t.dataset.side === which));
    document.getElementById("lib-side-notes").classList.toggle("hidden", which !== "notes");
    document.getElementById("lib-side-meta").classList.toggle("hidden", which !== "meta");
  },

  _where(m) {
    return m.page != null ? I18N.t("lib.page", { n: m.page }) : "";
  },

  _renderNotes() {
    const box = document.getElementById("lib-side-notes");
    box.textContent = "";
    if (!this.current) return;
    const order = (m) => (m.page != null ? m.page * 10 + (m.rects[0] ? m.rects[0][1] : 0) : m.start || 0);
    const all = [
      ...this.codings.map(c => ({ ...c, _type: "cod" })),
      ...this.annotations.map(a => ({ ...a, _type: "ann" })),
    ].sort((a, b) => order(a) - order(b));
    const head = document.createElement("div");
    head.className = "lib-notes-head";
    const count = document.createElement("span");
    count.className = "mini-label";
    count.textContent = I18N.t("lib.notes.count", { a: this.annotations.length, c: this.codings.length });
    const exp = document.createElement("button");
    exp.className = "btn-export-mini";
    exp.textContent = I18N.t("lib.notes.csv");
    exp.title = I18N.t("lib.notes.csv.title");
    exp.addEventListener("click", () => this._exportNotes());
    head.append(count, exp);
    box.appendChild(head);
    if (!all.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = I18N.t("lib.notes.empty");
      box.appendChild(p);
      return;
    }
    for (const m of all) box.appendChild(this._noteCard(m));
  },

  _noteCard(m) {
    const card = document.createElement("div");
    card.className = "lib-note-card";
    card.dataset.mark = `${m._type}:${m.id}`;
    const head = document.createElement("div");
    head.className = "quote-meta";
    const chip = document.createElement("span");
    chip.className = "dom-chip";
    if (m._type === "cod") {
      chip.style.backgroundColor = State.domains[m.domain] || "#999";
      head.append(chip, document.createTextNode(` ◉ ${m.name} · ${I18N.domain(m.domain)} ${this._where(m) && "· " + this._where(m)}`));
    } else {
      chip.style.backgroundColor = m.color;
      head.append(chip, document.createTextNode(` ${I18N.t(`lib.kind.ann.${m.kind}`)} ${this._where(m) && "· " + this._where(m)}`));
    }
    const quote = document.createElement("div");
    quote.className = "lib-note-quote";
    quote.textContent = `“${m.quote.length > 220 ? m.quote.slice(0, 220) + "…" : m.quote}”`;
    quote.title = I18N.t("lib.goto");
    quote.addEventListener("click", () => this.scrollToMark(m));
    const comment = document.createElement("textarea");
    comment.className = "lib-note-comment";
    comment.rows = 2;
    comment.value = m._type === "cod" ? m.memo : m.comment;
    comment.placeholder = I18N.t(m._type === "cod" ? "lib.memo.placeholder" : "lib.comment.placeholder");
    comment.addEventListener("change", async () => {
      try {
        if (m._type === "cod") await API.updateLitCoding(m.id, comment.value.trim());
        else await API.updateAnnotation(m.id, { comment: comment.value.trim() });
        Views.pulseSaved();
        await this._loadMarks();
      } catch (error) {
        Views.toast(error.message, true);
      }
    });
    const del = document.createElement("button");
    del.className = "icon-btn";
    del.title = I18N.t("lib.mark.delete");
    del.textContent = "🗑";
    del.addEventListener("click", async () => {
      if (!await Views.confirm(I18N.t("lib.mark.delete.confirm"))) return;
      try {
        if (m._type === "cod") { await API.deleteLitCoding(m.id); await State.reload(); }
        else await API.deleteAnnotation(m.id);
        await this._afterChange();
      } catch (error) {
        Views.toast(error.message, true);
      }
    });
    head.appendChild(del);
    card.append(head, quote, comment);
    return card;
  },

  /* Destaca una marca en el panel y, si se pide, lleva el lector hasta ella. */
  focusMark(key, scrollDocument = true) {
    const [type, id] = key.split(":");
    const list = type === "cod" ? this.codings : this.annotations;
    const mark = list.find(m => String(m.id) === id);
    if (!mark) return;
    this._showSide("notes");
    const panel = document.getElementById("lib-side-notes");
    const card = panel.querySelector(`[data-mark="${type}:${id}"]`);
    if (card) {
      // Solo se desplaza el panel (scrollIntoView movería también la página)
      const top = card.offsetTop - panel.offsetTop;
      if (top < panel.scrollTop || top + card.offsetHeight > panel.scrollTop + panel.clientHeight) {
        panel.scrollTop = Math.max(0, top - 12);
      }
      card.classList.remove("flash");
      void card.offsetWidth;
      card.classList.add("flash");
    }
    if (scrollDocument) this.scrollToMark(mark);
  },

  scrollToMark(m) {
    if (m.page != null) {
      const pageEl = document.querySelector(`#lib-pages .lib-page[data-page="${m.page}"]`);
      if (!pageEl) return;
      const y = m.rects[0] ? m.rects[0][1] : 0;
      const top = pageEl.getBoundingClientRect().top + window.scrollY + y * pageEl.offsetHeight - 120;
      window.scrollTo({ top, behavior: "smooth" });
    } else {
      const spans = [...document.querySelectorAll("#lib-pages [data-marks]")];
      const target = spans.find(s => s.dataset.marks.split(" ").some(k => k.endsWith(`:${m.id}`)));
      if (target) target.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  },

  /* Abre un documento en un pasaje codificado (desde el libro de códigos). */
  async openCoding(coding) {
    Views.show("literatura");
    await this.open(coding.item_id, `cod:${coding.id}`);
  },

  _exportNotes() {
    const rows = [[I18N.t("lib.csv.type"), I18N.t("lib.csv.page"), I18N.t("lib.csv.quote"),
      I18N.t("lib.csv.comment"), I18N.t("lib.csv.code"), I18N.t("lib.csv.category")]];
    for (const a of this.annotations) {
      rows.push([I18N.t(`lib.kind.ann.${a.kind}`), a.page ?? "", a.quote, a.comment, "", ""]);
    }
    for (const c of this.codings) rows.push(["◉", c.page ?? "", c.quote, c.memo, c.name, I18N.domain(c.domain)]);
    const csv = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\r\n");
    const title = (this.current.meta.title || this.current.filename).replace(/[^\p{L}\p{N} _-]/gu, "_").slice(0, 60);
    Files.save(new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" }), `cualibre_${I18N.t("lib.csv.file")}_${title}.csv`);
  },

  /* Ficha bibliográfica (metadatos para APA 7) */
  _renderMeta(item = this.current, box = document.getElementById("lib-side-meta")) {
    box.textContent = "";
    if (!item) return;
    const m = item.meta;
    const field = (key, value, type = "input") => {
      const label = document.createElement("label");
      label.className = "lib-field";
      const span = document.createElement("span");
      span.className = "mini-label";
      span.textContent = I18N.t(`lib.f.${key}`);
      let input;
      if (type === "select") {
        input = document.createElement("select");
        for (const t of ["article", "book", "chapter", "thesis", "report", "other"]) {
          const option = document.createElement("option");
          option.value = t;
          option.textContent = I18N.t(`lib.type.${t}`);
          input.appendChild(option);
        }
      } else if (type === "area") {
        input = document.createElement("textarea");
        input.rows = 3;
      } else {
        input = document.createElement("input");
        input.type = "text";
      }
      input.value = value || "";
      input.dataset.key = key;
      label.append(span, input);
      box.appendChild(label);
      return input;
    };
    const people = (list) => (list || []).map(p => p.given ? `${p.family}, ${p.given}` : p.family).join("\n");
    field("type", m.type, "select");
    field("title", m.title, "area");
    const authors = field("authors", people(m.authors), "area");
    authors.placeholder = I18N.t("lib.f.authors.placeholder");
    field("year", m.year);
    field("container", m.container);
    field("editors", people(m.editors), "area");
    field("volume", m.volume);
    field("issue", m.issue);
    field("pages", m.pages);
    field("publisher", m.publisher);
    const doi = field("doi", m.doi);
    field("url", m.url);
    field("isbn", m.isbn);
    const buttons = document.createElement("div");
    buttons.className = "lib-meta-buttons";
    const lookup = document.createElement("button");
    lookup.className = "btn btn-small";
    lookup.textContent = I18N.t("lib.lookup");
    lookup.addEventListener("click", async () => {
      try {
        const updated = await API.lookupLibraryItem(item.id, doi.value.trim());
        this._replaceItem(updated);
        this._renderMeta(updated, box);
        Views.toast(I18N.t("lib.lookup.done"));
      } catch (error) {
        Views.toast(error.message, true);
      }
    });
    const save = document.createElement("button");
    save.className = "btn btn-small btn-accent";
    save.textContent = I18N.t("lib.meta.save");
    save.addEventListener("click", () => this._saveMeta(box, item));
    buttons.append(lookup, save);
    if (!this.current) { // en el panel de detalle: volver sin guardar
      const cancel = document.createElement("button");
      cancel.className = "btn btn-small";
      cancel.textContent = I18N.t("dlg.cancel");
      cancel.addEventListener("click", () => { this._editingMeta = false; this._renderDetail(); });
      buttons.appendChild(cancel);
    }
    box.appendChild(buttons);
    const apa = document.createElement("div");
    apa.className = "lib-apa";
    const label = document.createElement("div");
    label.className = "mini-label";
    label.textContent = I18N.t("lib.apa");
    const ref = document.createElement("div");
    ref.className = "lib-apa-text";
    ref.innerHTML = item.apa; // generado por el servidor con el texto escapado
    apa.append(label, ref);
    box.appendChild(apa);
  },

  _parsePeople(text) {
    return text.split("\n").map(l => l.trim()).filter(Boolean).map(line => {
      const [family, ...rest] = line.split(",");
      return { family: family.trim(), given: rest.join(",").trim() };
    });
  },

  async _saveMeta(box, item = this.current) {
    const value = (key) => (box.querySelector(`[data-key="${key}"]`) || { value: "" }).value.trim();
    const meta = {
      type: value("type"), title: value("title"), year: value("year"), container: value("container"),
      volume: value("volume"), issue: value("issue"), pages: value("pages"), publisher: value("publisher"),
      doi: value("doi"), url: value("url"), isbn: value("isbn"),
      authors: this._parsePeople(value("authors")), editors: this._parsePeople(value("editors")),
    };
    try {
      const updated = await API.updateLibraryItem(item.id, { meta });
      this._replaceItem(updated);
      if (this.current) {
        this._renderMeta(updated, box);
        document.getElementById("lib-reader-title").textContent = this._readerTitle(updated);
      } else {
        this._editingMeta = false;
        this._renderList(); // la tabla refleja la ficha nueva (orden incluido)
      }
      Views.toast(I18N.t("lib.meta.saved"));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  _replaceItem(updated) {
    this.items = this.items.map(i => (i.id === updated.id ? updated : i));
    if (this.current && this.current.id === updated.id) this.current = updated;
  },
};
