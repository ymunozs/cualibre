/* Paleta de Control: código manual + memos, documentos del corpus y banco de
   códigos con edición/eliminación (FR-013/014, FR-030/031/033). */

const Paleta = {
  editingId: null,
  bankQuery: "",
  PAGE: 200, // ítems por tanda: con miles de códigos, el banco se dibuja por partes
  bankLimit: { "code-bank": 200, "code-bank-mini": 200 },

  init() {
    document.getElementById("btn-manual-save").addEventListener("click", () => this._saveManual());
    document.getElementById("btn-reset").addEventListener("click", () => this._reset());

    // Buscar en el banco de códigos (filtro local, sin llamada al backend)
    document.getElementById("code-bank-search").addEventListener("input", (e) => {
      this.bankQuery = e.target.value.trim().toLowerCase();
      this.bankLimit["code-bank"] = this.PAGE;
      this._renderBank();
    });

    // Fusionar/renombrar códigos en bloque (FR-068, codificación axial)
    document.getElementById("btn-merge-codes").addEventListener("click", () => this._mergeCodes());

    // Búsqueda en el corpus (FR-041)
    const input = document.getElementById("search-input");
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._runSearch();
      if (e.key === "Escape") { input.value = ""; this._clearSearch(); }
    });
    document.getElementById("search-next").addEventListener("click", () => { Canvas.nextHit(1); this._updateCount(); });
    document.getElementById("search-prev").addEventListener("click", () => { Canvas.nextHit(-1); this._updateCount(); });
    document.getElementById("search-clear").addEventListener("click", () => { input.value = ""; this._clearSearch(); });

    // Lectura limpia (FR-042)
    document.getElementById("btn-clean-read").addEventListener("click", () => {
      const allHidden = Canvas.hiddenDomains.size === Object.keys(State.domains).length;
      Canvas.setAllDomains(!allHidden);
      this._renderFilter();
    });
  },

  _runSearch() {
    const total = Canvas.search(document.getElementById("search-input").value);
    this._updateCount();
    if (!total) Views.toast(I18N.t("search.none"), true);
  },

  _clearSearch() {
    Canvas.clearSearch();
    this._updateCount();
  },

  _updateCount() {
    const count = document.getElementById("search-count");
    count.textContent = Canvas.searchRanges.length
      ? `${Canvas.currentHit + 1}/${Canvas.searchRanges.length}`
      : "—";
  },

  _renderFilter() {
    const box = document.getElementById("domain-filter");
    box.textContent = "";
    for (const [domain, color] of Object.entries(State.domains)) {
      const chip = document.createElement("button");
      chip.className = "filter-chip" + (Canvas.hiddenDomains.has(domain) ? " off" : "");
      chip.title = I18N.t(Canvas.hiddenDomains.has(domain) ? "filter.chip.show" : "filter.chip.hide",
        { domain: I18N.domain(domain) });
      const dot = document.createElement("span");
      dot.className = "dom-chip";
      dot.style.backgroundColor = color;
      chip.append(dot, document.createTextNode(I18N.domain(domain)));
      chip.addEventListener("click", () => { Canvas.toggleDomain(domain); this._renderFilter(); });
      box.appendChild(chip);
    }
    const clean = document.getElementById("btn-clean-read");
    const allHidden = Canvas.hiddenDomains.size === Object.keys(State.domains).length;
    clean.textContent = I18N.t(allHidden ? "filter.restore" : "filter.clean");
  },

  /* Rellena un <select> con dos grupos: Categorías Básicas + Personalizadas
     (FR-064). Reutilizado por el código manual y el formulario de edición. */
  _fillDomainSelect(select, selected) {
    select.textContent = "";
    const basicGroup = document.createElement("optgroup");
    basicGroup.label = I18N.t("optgroup.basic");
    for (const domain of Object.keys(State.basicDomains)) {
      const option = document.createElement("option");
      option.value = domain;
      option.textContent = I18N.domain(domain);
      option.selected = domain === selected;
      basicGroup.appendChild(option);
    }
    select.appendChild(basicGroup);
    const customNames = Object.keys(State.customDomains);
    if (customNames.length) {
      const customGroup = document.createElement("optgroup");
      customGroup.label = I18N.t("optgroup.custom");
      for (const domain of customNames) {
        const option = document.createElement("option");
        option.value = domain;
        option.textContent = domain;
        option.selected = domain === selected;
        customGroup.appendChild(option);
      }
      select.appendChild(customGroup);
    }
  },

  populateDomains() {
    const select = document.getElementById("manual-domain");
    this._fillDomainSelect(select, select.value);
  },

  render() {
    this._renderDocs();
    this._renderBank();
    this._renderFilter();
    this._renderCustomDomains();
    this._renderMergeControls();
  },

  /* Fusionar/renombrar códigos en bloque (FR-068) */
  _renderMergeControls() {
    const names = [...new Set(State.project.codes.map(c => c.name))].sort();
    const fromSelect = document.getElementById("merge-from");
    const previous = fromSelect.value;
    fromSelect.textContent = "";
    for (const name of names) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      fromSelect.appendChild(option);
    }
    if (names.includes(previous)) fromSelect.value = previous;

    const datalist = document.getElementById("merge-to-list");
    datalist.textContent = "";
    for (const name of names) {
      const option = document.createElement("option");
      option.value = name;
      datalist.appendChild(option);
    }
  },

  async _mergeCodes() {
    const fromName = document.getElementById("merge-from").value;
    const toInput = document.getElementById("merge-to");
    const toName = toInput.value.trim();
    if (!fromName || !toName) { Views.toast(I18N.t("codes.merge.missing"), true); return; }
    if (fromName === toName) { Views.toast(I18N.t("codes.merge.same"), true); return; }

    const count = State.project.codes.filter(c => c.name === fromName).length;
    const existsAsTarget = State.project.codes.some(c => c.name === toName);
    const message = I18N.t(existsAsTarget ? "codes.merge.confirm.merge" : "codes.merge.confirm.rename",
      { n: count, from: fromName, to: toName });
    if (!await Views.confirm(message)) return;

    try {
      const result = await API.mergeCodes(fromName, toName);
      toInput.value = "";
      await State.reload();
      Views.toast(I18N.t("codes.merge.done", { n: result.merged, name: result.name }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  /* Gestión de categorías personalizadas (FR-064): solo eliminar aquí; se
     crean desde la Nube Negra, que es donde ocurre el flujo de codificación. */
  _renderCustomDomains() {
    const box = document.getElementById("custom-domains-list");
    box.textContent = "";
    const names = Object.keys(State.customDomains);
    if (!names.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = I18N.t("custom.empty");
      box.appendChild(p);
      return;
    }
    for (const name of names) {
      const chip = document.createElement("span");
      chip.className = "filter-chip";
      chip.title = I18N.t("custom.delete.title", { name });
      const dot = document.createElement("span");
      dot.className = "dom-chip";
      dot.style.backgroundColor = State.customDomains[name];
      chip.append(dot, document.createTextNode(name + " "));
      const del = document.createElement("button");
      del.className = "icon-btn";
      del.textContent = "✕";
      del.addEventListener("click", (e) => { e.stopPropagation(); this._deleteCustomDomain(name); });
      chip.appendChild(del);
      box.appendChild(chip);
    }
  },

  async _deleteCustomDomain(name) {
    try {
      await API.deleteCustomDomain(name, false);
    } catch (error) {
      if (error.status === 409) {
        const count = error.headers?.get?.("X-Code-Count") || I18N.t("custom.some");
        const relations = Number(error.headers?.get?.("X-Relation-Count") || 0);
        // Usada por códigos, por relaciones (FR-085) o por ambos
        let message = Number(count) === 0 && relations
          ? I18N.t("custom.relations.confirm", { r: relations, name })
          : I18N.t("custom.inuse.confirm", { n: count, name });
        if (Number(count) > 0 && relations) message += " " + I18N.t("custom.relations.also", { r: relations });
        const ok = await Views.confirm(message);
        if (!ok) return;
        try {
          await API.deleteCustomDomain(name, true);
        } catch (err) {
          Views.toast(err.message, true);
          return;
        }
      } else {
        Views.toast(error.message, true);
        return;
      }
    }
    await State.reload();
    Views.toast(I18N.t("custom.deleted", { name }));
  },

  _renderDocs() {
    const list = document.getElementById("doc-list");
    list.textContent = "";
    const { documents, codes } = State.project;
    if (!documents.length) {
      const li = document.createElement("li");
      li.textContent = I18N.t("docs.empty");
      li.className = "muted";
      list.appendChild(li);
      return;
    }
    const counts = new Map();
    for (const c of codes) if (c.doc_id) counts.set(c.doc_id, (counts.get(c.doc_id) || 0) + 1);
    for (const doc of documents) {
      const li = document.createElement("li");
      const name = document.createElement("span");
      const count = counts.get(doc.id) || 0;
      name.textContent = `${doc.filename}${count ? ` ${I18N.t("docs.codes", { n: count })}` : ""}`;
      if (doc.ocr_pages && doc.ocr_pages.length) {
        // Transparencia (FR-080): este texto es lectura automática de una imagen
        const badge = document.createElement("span");
        badge.className = "ocr-badge";
        badge.textContent = I18N.t("docs.ocr");
        badge.title = I18N.t("docs.ocr.title", { pages: doc.ocr_pages.join(", ") });
        name.appendChild(badge);
      }
      const del = document.createElement("button");
      del.className = "icon-btn";
      del.title = I18N.t("docs.delete.title");
      del.textContent = "🗑";
      del.addEventListener("click", () => this._deleteDoc(doc));
      li.append(name, del);
      list.appendChild(li);
    }
  },

  async _deleteDoc(doc) {
    const anchored = State.project.codes.filter(c => c.doc_id === doc.id).length;
    const message = anchored
      ? I18N.t("docs.delete.withcodes", { name: doc.filename, n: anchored })
      : I18N.t("docs.delete.plain", { name: doc.filename });
    if (!await Views.confirm(message)) return;
    try {
      await API.deleteDocument(doc.id, true);
      await State.reload();
      Views.toast(anchored ? I18N.t("docs.deleted.codes", { n: anchored }) : I18N.t("docs.deleted"));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _saveManual() {
    const name = document.getElementById("manual-name").value.trim();
    if (!name) {
      Views.toast(I18N.t("manual.missing"), true);
      return;
    }
    try {
      await API.createCode({
        domain: document.getElementById("manual-domain").value,
        name,
        memo: document.getElementById("manual-memo").value.trim(),
      });
      document.getElementById("manual-name").value = "";
      document.getElementById("manual-memo").value = "";
      await State.reload();
      Views.toast(I18N.t("manual.saved", { name }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _reset() {
    const ok = await Views.confirm(I18N.t("reset.confirm"));
    if (!ok) return;
    try {
      await API.resetProject();
      await State.reload();
      Views.toast(I18N.t("reset.done"));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  /* Dos vistas del mismo banco: la completa con buscador (pestaña ▤ CÓDIGOS,
     #code-bank) y una compacta sin filtrar en la Paleta (#code-bank-mini) —
     esta última existe para que arrastrar una selección del Canvas a un
     código siga funcionando (FR-037) aunque el banco completo viva en otra
     pestaña y no pueda verse a la vez que el Canvas. */
  _renderBank() {
    const all = [...State.project.codes].reverse(); // más recientes arriba
    this._docNames = new Map(State.project.documents.map(d => [d.id, d.filename]));
    let codes = all;
    if (this.bankQuery) {
      codes = all.filter(c =>
        c.name.toLowerCase().includes(this.bankQuery)
        || c.domain.toLowerCase().includes(this.bankQuery)
        || I18N.domain(c.domain).toLowerCase().includes(this.bankQuery)
        || (c.quote && c.quote.toLowerCase().includes(this.bankQuery))
      );
    }
    this._renderBankInto(codes, "code-bank", I18N.t(this.bankQuery ? "bank.nomatch" : "bank.empty"));
    this._renderBankInto(all, "code-bank-mini", I18N.t("bank.empty"));
  },

  _renderBankInto(codes, containerId, emptyMessage) {
    const bank = document.getElementById(containerId);
    bank.textContent = "";
    if (!codes.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = emptyMessage;
      bank.appendChild(p);
      return;
    }
    const limit = this.bankLimit[containerId] || this.PAGE;
    const fragment = document.createDocumentFragment();
    for (const code of codes.slice(0, limit)) {
      fragment.appendChild(
        this.editingId === code.id ? this._editForm(code) : this._codeItem(code)
      );
    }
    if (codes.length > limit) {
      const more = document.createElement("button");
      more.className = "btn btn-small bank-more";
      more.textContent = I18N.t("bank.more", {
        n: Math.min(this.PAGE, codes.length - limit), shown: limit, total: codes.length,
      });
      more.addEventListener("click", () => {
        this.bankLimit[containerId] = limit + this.PAGE;
        this._renderBankInto(codes, containerId, emptyMessage);
      });
      fragment.appendChild(more);
    }
    bank.appendChild(fragment);
  },

  _codeItem(code) {
    const item = document.createElement("div");
    item.className = "code-item";

    // Destino de arrastre: re-aplicar este código a la selección (FR-037)
    item.addEventListener("dragover", (event) => {
      if (!Canvas.dragSelection) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
      item.classList.add("drop-target");
    });
    item.addEventListener("dragleave", () => item.classList.remove("drop-target"));
    item.addEventListener("drop", async (event) => {
      event.preventDefault();
      item.classList.remove("drop-target");
      const sel = Canvas.dragSelection;
      if (!sel) return;
      Canvas.dragSelection = null;
      window.getSelection().removeAllRanges();
      try {
        await API.createCode({
          doc_id: sel.docId,
          domain: code.domain,
          name: code.name,
          quote: sel.quote,
          start: sel.start,
          end: sel.end,
          memo: "",
        });
        await State.reload();
        Views.toast(I18N.t("bank.added", { name: code.name }));
      } catch (error) {
        Views.toast(error.message, true);
      }
    });

    const head = document.createElement("div");
    head.className = "code-head";
    const chip = document.createElement("span");
    chip.className = "dom-chip";
    chip.style.backgroundColor = State.domains[code.domain] || "#999";
    chip.title = I18N.domain(code.domain);
    const name = document.createElement("span");
    name.className = "code-name";
    name.textContent = code.name;
    name.title = I18N.t("bank.quotes.title");
    name.addEventListener("click", () => Views.showQuotes(code.name));
    const edit = document.createElement("button");
    edit.className = "icon-btn";
    edit.title = I18N.t("bank.edit.title");
    edit.textContent = "✎";
    edit.addEventListener("click", () => { this.editingId = code.id; this._renderBank(); });
    const del = document.createElement("button");
    del.className = "icon-btn";
    del.title = I18N.t("bank.delete.title");
    del.textContent = "🗑";
    del.addEventListener("click", () => this._deleteCode(code));
    head.append(chip, name, edit, del);
    item.appendChild(head);

    if (code.quote) {
      const quote = document.createElement("div");
      quote.className = "code-quote";
      const snippet = code.quote.length > 90 ? code.quote.slice(0, 90) + "…" : code.quote;
      quote.textContent = `“${snippet}”`;
      item.appendChild(quote);
    }
    if (code.memo) {
      const memo = document.createElement("div");
      memo.className = "code-memo";
      const pencil = document.createElement("span");
      pencil.className = "sym";
      pencil.textContent = "✎ ";
      memo.append(pencil, code.memo);
      item.appendChild(memo);
    }
    const meta = document.createElement("div");
    meta.className = "code-meta";
    const docName = code.doc_id
      ? (this._docNames && this._docNames.get(code.doc_id)) || "?"
      : I18N.t("origin.manual");
    meta.textContent = `#${code.id} · ${I18N.domain(code.domain)} · ${docName} · ${I18N.dateTime(code.created_at)}`;
    item.appendChild(meta);
    return item;
  },

  _editForm(code) {
    const form = document.createElement("div");
    form.className = "code-item code-edit-form";

    const domainSelect = document.createElement("select");
    this._fillDomainSelect(domainSelect, code.domain);
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.value = code.name;
    nameInput.maxLength = 200;
    const memoInput = document.createElement("textarea");
    memoInput.rows = 2;
    memoInput.value = code.memo;
    memoInput.placeholder = I18N.t("bank.memo.placeholder");

    const buttons = document.createElement("div");
    buttons.className = "code-edit-buttons";
    const save = document.createElement("button");
    save.className = "btn btn-small btn-accent";
    save.textContent = I18N.t("bank.save");
    save.addEventListener("click", async () => {
      const name = nameInput.value.trim();
      if (!name) { Views.toast(I18N.t("bank.name.empty"), true); return; }
      try {
        await API.updateCode(code.id, {
          name, domain: domainSelect.value, memo: memoInput.value.trim(),
        });
        this.editingId = null;
        await State.reload(); // el color del resaltado cambia con el dominio (FR-030)
        Views.toast(I18N.t("bank.updated"));
      } catch (error) {
        Views.toast(error.message, true);
      }
    });
    const cancel = document.createElement("button");
    cancel.className = "btn btn-small";
    cancel.textContent = I18N.t("dlg.cancel");
    cancel.addEventListener("click", () => { this.editingId = null; this._renderBank(); });
    buttons.append(save, cancel);

    form.append(domainSelect, nameInput, memoInput, buttons);
    return form;
  },

  async _deleteCode(code) {
    if (!await Views.confirm(I18N.t("bank.delete.confirm", { name: code.name }))) return;
    try {
      try {
        await API.deleteCode(code.id);
      } catch (error) {
        if (error.status !== 409) throw error;
        // Última instancia de un código con pasajes de literatura (FR-091)
        const n = error.headers.get("X-Lit-Count") || "?";
        if (!await Views.confirm(I18N.t("bank.delete.literature", { name: code.name, n }))) return;
        await API.deleteCode(code.id, true);
      }
      await State.reload(); // FR-031: resaltado fuera, analytics al día
      Views.toast(I18N.t("bank.deleted"));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },
};
