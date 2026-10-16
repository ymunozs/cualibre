/* Libro de códigos (FR-084): todos los códigos y categorías del proyecto con
   su descripción cualitativa (definición, cuándo usarlo, cuándo no y un
   ejemplo). Índice a la izquierda, ficha a la derecha, como un libro.

   Todo el texto lo escribe el investigador (Principio VIII): la ficha solo
   reúne lo que ya existe (citas, memos, relaciones) para tenerlo a la vista.
   Se guarda solo, al dejar de escribir y al salir del campo, sin redibujar la
   pestaña (un State.reload() borraría lo que se está escribiendo). */

const Libro = {
  selected: null, // {kind: "code"|"category"|"orphan"|"orphan-category", name}
  query: "",
  _timer: null,
  _pending: null, // guardado en espera: {kind, name, fields}
  _status: "", // texto del estado de guardado de la ficha abierta

  FIELDS: ["definition", "inclusion", "exclusion", "example"],

  init() {
    document.getElementById("book-search").addEventListener("input", (e) => {
      this.query = e.target.value.trim().toLowerCase();
      this._renderIndex();
    });
    // Principio V: lo escrito en los últimos 900 ms no se pierde si la ventana
    // se oculta o se cierra antes del guardado diferido
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") this._flush();
    });
    window.addEventListener("pagehide", () => {
      const pending = this._pending;
      if (!pending) return;
      this._pending = null;
      clearTimeout(this._timer);
      fetch("/api/codebook", {
        method: "PUT", keepalive: true, // sobrevive al cierre de la página
        headers: { "Content-Type": "application/json", "X-Cua-Lang": I18N.lang },
        body: JSON.stringify({ kind: pending.kind, name: pending.name, ...pending.fields }),
      });
    });
  },

  /* ---------- Modelo: qué hay en el libro ---------- */

  _model() {
    const { codes, codebook = {}, category_notes: notes = {} } = State.project;
    const byCategory = new Map(); // categoría -> Map(nombre -> {quotes, total})
    const categoriesOf = new Map(); // nombre -> [categorías]
    for (const code of codes) {
      if (!byCategory.has(code.domain)) byCategory.set(code.domain, new Map());
      const names = byCategory.get(code.domain);
      const info = names.get(code.name) || { quotes: 0, total: 0 };
      info.total++;
      if (code.doc_id) info.quotes++;
      names.set(code.name, info);
      const list = categoriesOf.get(code.name) || [];
      if (!list.includes(code.domain)) list.push(code.domain);
      categoriesOf.set(code.name, list);
    }
    // Categorías: en uso, personalizadas o ya descritas, en el orden de la paleta
    const categories = Object.keys(State.domains).filter(key =>
      byCategory.has(key) || key in State.customDomains || key in notes);
    for (const key of byCategory.keys()) if (!categories.includes(key)) categories.push(key);
    const orphans = Object.keys(codebook).filter(name => !categoriesOf.has(name)).sort();
    const orphanCategories = Object.keys(notes).filter(key => !categories.includes(key));
    return { byCategory, categoriesOf, categories, orphans, orphanCategories, codebook, notes };
  },

  _entry(kind, name) {
    const book = kind === "category" || kind === "orphan-category"
      ? State.project.category_notes : State.project.codebook;
    return (book && book[name]) || null;
  },

  _described(kind, name) {
    const entry = this._entry(kind, name);
    return !!entry && this.FIELDS.some(f => (entry[f] || "").trim());
  },

  _label(kind, name) {
    return kind === "category" || kind === "orphan-category" ? I18N.domain(name) : name;
  },

  /* Orden de lectura del libro: cada categoría seguida de sus códigos. */
  _sequence(model) {
    const seq = [];
    const seen = new Set();
    for (const key of model.categories) {
      seq.push({ kind: "category", name: key });
      for (const name of [...(model.byCategory.get(key) || new Map()).keys()].sort(this._collate)) {
        if (seen.has(name)) continue; // un código en dos categorías: una sola ficha
        seen.add(name);
        seq.push({ kind: "code", name });
      }
    }
    for (const name of model.orphans) seq.push({ kind: "orphan", name });
    for (const key of model.orphanCategories) seq.push({ kind: "orphan-category", name: key });
    return seq;
  },

  _collate(a, b) { return a.localeCompare(b, I18N.locale, { sensitivity: "base" }); },

  /* ---------- Render ---------- */

  render() {
    this._flush(); // lo escrito y aún no guardado sale antes de redibujar
    const model = this._model();
    const seq = this._sequence(model);
    const empty = !seq.length;
    document.getElementById("book-empty").classList.toggle("hidden", !empty);
    document.getElementById("book-grid").classList.toggle("hidden", empty);
    if (empty) { this.selected = null; return; }
    const still = this.selected && seq.some(s => s.kind === this.selected.kind && s.name === this.selected.name);
    if (!still) {
      // Si la ficha abierta cambió de tipo (p. ej., su código se quedó sin citas)
      const same = this.selected && seq.find(s => s.name === this.selected.name
        && (s.kind === "category") === (this.selected.kind === "category"));
      this.selected = same || seq.find(s => s.kind === "code") || seq[0];
    }
    this._renderIndex(model);
    this._renderPage(model, seq);
  },

  _renderIndex(model = this._model()) {
    const box = document.getElementById("book-index");
    box.textContent = "";
    const q = this.query;
    const match = (text) => !q || text.toLowerCase().includes(q);
    const codeNames = [...model.categoriesOf.keys()];
    const described = codeNames.filter(n => this._described("code", n)).length;
    document.getElementById("book-progress").textContent =
      I18N.t("book.progress", { n: described, total: codeNames.length });

    const item = (kind, name, label, extra, level) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = `book-entry book-${level}`;
      if (this.selected && this.selected.kind === kind && this.selected.name === name) {
        row.classList.add("active");
      }
      const mark = document.createElement("span");
      mark.className = "book-mark";
      const isDescribed = this._described(kind, name);
      mark.textContent = isDescribed ? "●" : "○";
      mark.title = I18N.t(isDescribed ? "book.described" : "book.undescribed");
      const text = document.createElement("span");
      text.className = "book-entry-name";
      text.textContent = label;
      row.append(mark, text);
      if (extra) {
        const count = document.createElement("span");
        count.className = "book-count";
        count.textContent = extra;
        row.appendChild(count);
      }
      row.addEventListener("click", () => this.open(kind, name));
      return row;
    };

    let shown = 0;
    for (const key of model.categories) {
      const names = model.byCategory.get(key) || new Map();
      const codes = [...names.keys()].sort(this._collate).filter(n => match(n) || match(I18N.domain(key)));
      if (!codes.length && !match(I18N.domain(key))) continue;
      const head = item("category", key, I18N.domain(key), names.size ? String(names.size) : "", "category");
      const chip = document.createElement("span");
      chip.className = "dom-chip";
      chip.style.backgroundColor = State.domains[key] || "#999";
      head.insertBefore(chip, head.firstChild);
      box.appendChild(head);
      shown++;
      for (const name of codes) {
        const info = names.get(name);
        box.appendChild(item("code", name, name, I18N.t("book.quotes.short", { n: info.quotes }), "code"));
      }
    }
    const orphans = model.orphans.filter(match);
    const orphanCategories = model.orphanCategories.filter(match);
    if (orphans.length || orphanCategories.length) {
      const title = document.createElement("div");
      title.className = "mini-label book-orphans-title";
      title.textContent = I18N.t("book.orphans");
      title.title = I18N.t("book.orphans.title");
      box.appendChild(title);
      for (const name of orphans) box.appendChild(item("orphan", name, name, "", "code"));
      for (const key of orphanCategories) {
        box.appendChild(item("orphan-category", key, I18N.domain(key), "", "code"));
      }
      shown++;
    }
    if (!shown) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = I18N.t("bank.nomatch");
      box.appendChild(p);
    }
  },

  open(kind, name) {
    this._flush();
    this.selected = { kind, name };
    const model = this._model();
    this._status = "";
    this._renderIndex(model);
    this._renderPage(model, this._sequence(model));
    document.getElementById("book-page").scrollTop = 0;
  },

  _renderPage(model, seq) {
    const page = document.getElementById("book-page");
    page.textContent = "";
    const sel = this.selected;
    if (!sel) return;
    const isCategory = sel.kind === "category" || sel.kind === "orphan-category";
    const isOrphan = sel.kind === "orphan" || sel.kind === "orphan-category";

    // Encabezado
    const kicker = document.createElement("div");
    kicker.className = "mini-label";
    kicker.textContent = I18N.t(isCategory ? "book.kind.category" : "book.kind.code");
    const title = document.createElement("h2");
    title.className = "book-title";
    if (isCategory) {
      const chip = document.createElement("span");
      chip.className = "dom-chip book-title-chip";
      chip.style.backgroundColor = State.domains[sel.name] || "#999";
      title.appendChild(chip);
    }
    title.appendChild(document.createTextNode(this._label(sel.kind, sel.name)));
    page.append(kicker, title);

    const meta = document.createElement("p");
    meta.className = "book-meta";
    if (isOrphan) {
      meta.textContent = I18N.t(isCategory ? "book.orphan.category.note" : "book.orphan.note");
    } else if (isCategory) {
      const names = model.byCategory.get(sel.name) || new Map();
      const quotes = [...names.values()].reduce((sum, i) => sum + i.quotes, 0);
      meta.textContent = I18N.t("book.category.meta", { codes: names.size, quotes });
    } else {
      const instances = State.project.codes.filter(c => c.name === sel.name);
      const docs = new Set(instances.filter(c => c.doc_id).map(c => c.doc_id)).size;
      const quotes = instances.filter(c => c.doc_id).length;
      const lit = (State.project.lit_codings || []).filter(c => c.name === sel.name).length;
      meta.textContent = I18N.t("book.code.meta", { quotes, docs })
        + (lit ? I18N.t("book.code.meta.lit", { n: lit }) : "");
      const chips = document.createElement("span");
      chips.className = "book-categories";
      for (const domain of model.categoriesOf.get(sel.name) || []) {
        const tag = document.createElement("button");
        tag.type = "button";
        tag.className = "filter-chip";
        const dot = document.createElement("span");
        dot.className = "dom-chip";
        dot.style.backgroundColor = State.domains[domain] || "#999";
        tag.append(dot, document.createTextNode(I18N.domain(domain)));
        tag.title = I18N.t("book.go.category");
        tag.addEventListener("click", () => this.open("category", domain));
        chips.appendChild(tag);
      }
      meta.appendChild(chips);
    }
    page.appendChild(meta);

    // Campos de la ficha
    const entry = this._entry(sel.kind, sel.name) || {};
    const fields = isCategory ? ["definition", "inclusion", "exclusion"] : this.FIELDS;
    const inputs = {};
    const target = { kind: isCategory ? "category" : "code", name: sel.name };
    for (const field of fields) {
      const label = document.createElement("label");
      label.className = "book-field";
      const name = document.createElement("span");
      name.className = "book-field-label";
      name.textContent = I18N.t(`book.f.${field}`);
      const hint = document.createElement("span");
      hint.className = "book-field-hint";
      hint.textContent = I18N.t(`book.f.${field}.hint${isCategory ? ".cat" : ""}`);
      const area = document.createElement("textarea");
      area.rows = field === "definition" ? 4 : 3;
      area.value = entry[field] || "";
      area.dataset.field = field;
      area.addEventListener("input", () => this._schedule(target, inputs));
      area.addEventListener("change", () => this._schedule(target, inputs, true));
      inputs[field] = area;
      label.append(name, hint, area);
      page.appendChild(label);
    }

    // Ejemplo tomado de una cita del propio código
    if (!isCategory && !isOrphan) {
      const quoted = State.project.codes.filter(c => c.name === sel.name && c.quote);
      if (quoted.length) {
        const docNames = new Map(State.project.documents.map(d => [d.id, d.filename]));
        const pick = document.createElement("select");
        pick.className = "book-example-pick";
        const first = document.createElement("option");
        first.value = "";
        first.textContent = I18N.t("book.example.pick");
        pick.appendChild(first);
        for (const c of quoted) {
          const option = document.createElement("option");
          option.value = String(c.id);
          const snippet = c.quote.length > 90 ? c.quote.slice(0, 90) + "…" : c.quote;
          option.textContent = `“${snippet}” · ${docNames.get(c.doc_id) || "?"}`;
          pick.appendChild(option);
        }
        pick.addEventListener("change", () => {
          const c = quoted.find(q => String(q.id) === pick.value);
          pick.value = "";
          if (!c) return;
          const area = inputs.example;
          const text = `“${c.quote}” (${docNames.get(c.doc_id) || "?"})`;
          area.value = area.value.trim() ? `${area.value.trim()}\n\n${text}` : text;
          this._schedule(target, inputs, true);
        });
        inputs.example.parentElement.appendChild(pick);
      }
    }

    const status = document.createElement("p");
    status.className = "book-status mini-label";
    status.id = "book-status";
    status.textContent = this._status;
    page.appendChild(status);

    // Lo que ya existe sobre este código: memos, relaciones y citas
    if (!isCategory && !isOrphan) this._renderEvidence(page, sel.name);
    if (sel.kind === "category") this._renderCategoryCodes(page, model, sel.name);
    if (sel.kind !== "orphan") this._renderRelations(page, target);

    if (isOrphan) {
      const del = document.createElement("button");
      del.className = "btn btn-small";
      del.textContent = I18N.t("book.orphan.delete");
      del.addEventListener("click", () => this._deleteOrphan(target));
      page.appendChild(del);
    }

    // Navegación de página en página
    const index = seq.findIndex(s => s.kind === sel.kind && s.name === sel.name);
    const nav = document.createElement("div");
    nav.className = "book-nav";
    const prev = document.createElement("button");
    prev.className = "btn btn-small";
    prev.textContent = I18N.t("book.prev");
    prev.disabled = index <= 0;
    prev.addEventListener("click", () => { const s = seq[index - 1]; if (s) this.open(s.kind, s.name); });
    const next = document.createElement("button");
    next.className = "btn btn-small";
    next.textContent = I18N.t("book.next");
    next.disabled = index < 0 || index >= seq.length - 1;
    next.addEventListener("click", () => { const s = seq[index + 1]; if (s) this.open(s.kind, s.name); });
    const position = document.createElement("span");
    position.className = "mini-label";
    position.textContent = index >= 0 ? `${index + 1} / ${seq.length}` : "";
    nav.append(prev, position, next);
    page.appendChild(nav);
  },

  _section(page, text) {
    const title = document.createElement("div");
    title.className = "section-title book-section";
    title.textContent = text;
    page.appendChild(title);
  },

  _renderEvidence(page, name) {
    const instances = State.project.codes.filter(c => c.name === name);
    const memos = instances.filter(c => c.memo);
    if (memos.length) {
      this._section(page, I18N.t("book.memos", { n: memos.length }));
      const list = document.createElement("ul");
      list.className = "plain-list book-list";
      for (const c of memos) {
        const li = document.createElement("li");
        li.textContent = `✎ ${c.memo}`;
        list.appendChild(li);
      }
      page.appendChild(list);
    }
    const quoted = instances.filter(c => c.quote);
    if (quoted.length) {
      this._section(page, I18N.t("book.quotes", { n: quoted.length }));
      for (const c of quoted.slice(0, 3)) {
        const q = document.createElement("div");
        q.className = "quote-text book-quote";
        q.textContent = `“${c.quote.length > 280 ? c.quote.slice(0, 280) + "…" : c.quote}”`;
        page.appendChild(q);
      }
      const all = document.createElement("button");
      all.className = "btn btn-small";
      all.textContent = I18N.t("book.quotes.all", { n: quoted.length });
      all.addEventListener("click", () => Views.showQuotes(name));
      page.appendChild(all);
    }
    // Citas de la literatura (FR-091): aparte de las del corpus
    const lit = (State.project.lit_codings || []).filter(c => c.name === name);
    if (lit.length) {
      if (!Biblioteca.items.length && !this._loadingLibrary) {
        this._loadingLibrary = true; // las fichas llegan después: se redibuja la página
        Biblioteca.loadItems().then(() => { this._loadingLibrary = false; if (Views.current === "libro") this.render(); });
      }
      this._section(page, I18N.t("book.lit", { n: lit.length }));
      for (const c of lit) {
        const row = document.createElement("div");
        row.className = "book-lit";
        const q = document.createElement("div");
        q.className = "quote-text book-quote";
        q.textContent = `“${c.quote.length > 280 ? c.quote.slice(0, 280) + "…" : c.quote}”`;
        const item = Biblioteca.item(c.item_id);
        const meta = document.createElement("div");
        meta.className = "quote-meta";
        meta.textContent = `${item ? `(${item.cite}${c.page ? `, ${I18N.t("lib.page.short", { n: c.page })}` : ""})` : ""}${c.memo ? ` · ✎ ${c.memo}` : ""}`;
        const open = document.createElement("button");
        open.className = "btn btn-small";
        open.textContent = I18N.t("book.lit.open");
        open.addEventListener("click", () => Biblioteca.openCoding(c));
        row.append(q, meta, open);
        page.appendChild(row);
      }
    }
  },

  _renderCategoryCodes(page, model, key) {
    const names = [...(model.byCategory.get(key) || new Map()).keys()].sort(this._collate);
    if (!names.length) return;
    this._section(page, I18N.t("book.category.codes", { n: names.length }));
    const box = document.createElement("div");
    box.className = "book-chips";
    for (const name of names) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "filter-chip";
      chip.textContent = `${this._described("code", name) ? "●" : "○"} ${name}`;
      chip.addEventListener("click", () => this.open("code", name));
      box.appendChild(chip);
    }
    page.appendChild(box);
  },

  _renderRelations(page, target) {
    const related = State.project.relations.filter(r =>
      ((r.source_kind || "code") === target.kind && r.source === target.name)
      || ((r.target_kind || "code") === target.kind && r.target === target.name));
    if (!related.length) return;
    this._section(page, I18N.t("book.relations", { n: related.length }));
    const list = document.createElement("ul");
    list.className = "plain-list book-list";
    for (const r of related) {
      const li = document.createElement("li");
      li.textContent = `${Relations.nodeLabel(r.source_kind, r.source)} —${I18N.relVerb(r.type)}→ ${Relations.nodeLabel(r.target_kind, r.target)}`;
      list.appendChild(li);
    }
    page.appendChild(list);
  },

  /* ---------- Guardado ---------- */

  _schedule(target, inputs, now = false) {
    const fields = {};
    for (const field of this.FIELDS) fields[field] = inputs[field] ? inputs[field].value : "";
    if (target.kind === "category") {
      // Las categorías no muestran «ejemplo»: se conserva el que tuviera
      const entry = this._entry("category", target.name);
      fields.example = (entry && entry.example) || "";
    }
    this._pending = { ...target, fields };
    this._setStatus(I18N.t("book.status.typing"));
    clearTimeout(this._timer);
    if (now) this._flush();
    else this._timer = setTimeout(() => this._flush(), 900);
  },

  _flush() {
    clearTimeout(this._timer);
    const pending = this._pending;
    this._pending = null;
    if (!pending) return;
    const current = this._entry(pending.kind, pending.name) || {};
    const changed = this.FIELDS.some(f => (current[f] || "") !== (pending.fields[f] || ""));
    if (!changed) { this._setStatus(this._status === I18N.t("book.status.typing") ? "" : this._status); return; }
    this._save(pending);
  },

  async _save({ kind, name, fields }) {
    this._setStatus(I18N.t("book.status.saving"));
    try {
      const { entry } = await API.saveCodebook({ kind, name, ...fields });
      const key = kind === "category" ? "category_notes" : "codebook";
      if (!State.project[key]) State.project[key] = {};
      if (entry) State.project[key][name] = entry;
      else delete State.project[key][name];
      const time = new Date().toLocaleTimeString(I18N.locale, { hour: "2-digit", minute: "2-digit" });
      this._setStatus(I18N.t("book.status.saved", { time }));
      Views.pulseSaved();
      if (Views.current === "libro") this._renderIndex(); // marcas ●/○ y avance
    } catch (error) {
      this._setStatus(I18N.t("book.status.error"));
      Views.toast(error.message, true);
    }
  },

  _setStatus(text) {
    this._status = text;
    const el = document.getElementById("book-status");
    if (el) el.textContent = text;
  },

  async _deleteOrphan(target) {
    const label = this._label(target.kind, target.name);
    if (!await Views.confirm(I18N.t("book.orphan.delete.confirm", { name: label }))) return;
    try {
      await API.deleteCodebook(target.kind, target.name);
      await State.reload();
      Views.toast(I18N.t("book.orphan.deleted", { name: label }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },
};
