/* Paleta de Control: código manual + memos, documentos del corpus y banco de
   códigos con edición/eliminación (FR-013/014, FR-030/031/033). */

const Paleta = {
  editingId: null,
  bankQuery: "",

  init() {
    document.getElementById("btn-manual-save").addEventListener("click", () => this._saveManual());
    document.getElementById("btn-reset").addEventListener("click", () => this._reset());

    // Buscar en el banco de códigos (filtro local, sin llamada al backend)
    document.getElementById("code-bank-search").addEventListener("input", (e) => {
      this.bankQuery = e.target.value.trim().toLowerCase();
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
    if (!total) Views.toast("Sin resultados en el corpus", true);
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
      chip.title = `${domain} — clic para ${Canvas.hiddenDomains.has(domain) ? "mostrar" : "ocultar"} sus resaltados`;
      const dot = document.createElement("span");
      dot.className = "dom-chip";
      dot.style.backgroundColor = color;
      chip.append(dot, document.createTextNode(domain));
      chip.addEventListener("click", () => { Canvas.toggleDomain(domain); this._renderFilter(); });
      box.appendChild(chip);
    }
    const clean = document.getElementById("btn-clean-read");
    const allHidden = Canvas.hiddenDomains.size === Object.keys(State.domains).length;
    clean.textContent = allHidden ? "◼ RESTAURAR RESALTADOS" : "◻ LECTURA LIMPIA";
  },

  /* Rellena un <select> con dos grupos: Categorías Básicas + Personalizadas
     (FR-064). Reutilizado por el código manual y el formulario de edición. */
  _fillDomainSelect(select, selected) {
    select.textContent = "";
    const basicGroup = document.createElement("optgroup");
    basicGroup.label = "Categorías Básicas";
    for (const domain of Object.keys(State.basicDomains)) {
      const option = document.createElement("option");
      option.value = domain;
      option.textContent = domain;
      option.selected = domain === selected;
      basicGroup.appendChild(option);
    }
    select.appendChild(basicGroup);
    const customNames = Object.keys(State.customDomains);
    if (customNames.length) {
      const customGroup = document.createElement("optgroup");
      customGroup.label = "Personalizadas";
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
    this._fillDomainSelect(document.getElementById("manual-domain"));
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
    if (!fromName || !toName) { Views.toast("Elige un código de origen y escribe el destino", true); return; }
    if (fromName === toName) { Views.toast("Elige dos nombres distintos", true); return; }

    const count = State.project.codes.filter(c => c.name === fromName).length;
    const existsAsTarget = State.project.codes.some(c => c.name === toName);
    const message = existsAsTarget
      ? `Esto fusionará ${count} cita(s) de «${fromName}» dentro de «${toName}» (adoptarán su categoría). ¿Continuar?`
      : `Esto renombrará ${count} cita(s) de «${fromName}» a «${toName}». ¿Continuar?`;
    if (!await Views.confirm(message)) return;

    try {
      const result = await API.mergeCodes(fromName, toName);
      toInput.value = "";
      await State.reload();
      Views.toast(`Fusionado: ${result.merged} cita(s) → «${result.name}»`);
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
      p.textContent = "Aún no hay categorías propias. Créalas desde la Nube Negra (✚ Nueva categoría…).";
      box.appendChild(p);
      return;
    }
    for (const name of names) {
      const chip = document.createElement("span");
      chip.className = "filter-chip";
      chip.title = `Eliminar «${name}»`;
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
        const count = error.headers?.get?.("X-Code-Count") || "algunos";
        const ok = await Views.confirm(
          `${count} código(s) usan «${name}». Se conservarán con ese nombre pero sin color propio. ¿Eliminar la categoría de todas formas?`
        );
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
    Views.toast(`Categoría eliminada: ${name}`);
  },

  _renderDocs() {
    const list = document.getElementById("doc-list");
    list.textContent = "";
    const { documents, codes } = State.project;
    if (!documents.length) {
      const li = document.createElement("li");
      li.textContent = "Sin documentos aún.";
      li.style.color = "#999";
      list.appendChild(li);
      return;
    }
    for (const doc of documents) {
      const li = document.createElement("li");
      const name = document.createElement("span");
      const count = codes.filter(c => c.doc_id === doc.id).length;
      name.textContent = `${doc.filename}${count ? ` (${count} cód.)` : ""}`;
      const del = document.createElement("button");
      del.className = "icon-btn";
      del.title = "Eliminar documento";
      del.textContent = "🗑";
      del.addEventListener("click", () => this._deleteDoc(doc));
      li.append(name, del);
      list.appendChild(li);
    }
  },

  async _deleteDoc(doc) {
    const anchored = State.project.codes.filter(c => c.doc_id === doc.id).length;
    const message = anchored
      ? `Eliminar «${doc.filename}» borrará también sus ${anchored} código(s) asociado(s). ¿Continuar?`
      : `¿Eliminar «${doc.filename}» del corpus?`;
    if (!await Views.confirm(message)) return;
    try {
      await API.deleteDocument(doc.id, true);
      await State.reload();
      Views.toast(`Documento eliminado${anchored ? ` (con ${anchored} códigos)` : ""}`);
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _saveManual() {
    const name = document.getElementById("manual-name").value.trim();
    if (!name) {
      Views.toast("Escribe una etiqueta para el código manual", true);
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
      Views.toast(`Código manual guardado: ${name}`);
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _reset() {
    const ok = await Views.confirm(
      "Esto borrará TODO el proyecto activo: corpus, códigos y memos. ¿Estás seguro?"
    );
    if (!ok) return;
    try {
      await API.resetProject();
      await State.reload();
      Views.toast("Proyecto reiniciado");
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
    let codes = [...State.project.codes].reverse(); // más recientes arriba
    if (this.bankQuery) {
      codes = codes.filter(c =>
        c.name.toLowerCase().includes(this.bankQuery)
        || c.domain.toLowerCase().includes(this.bankQuery)
        || (c.quote && c.quote.toLowerCase().includes(this.bankQuery))
      );
    }
    this._renderBankInto(codes, "code-bank", this.bankQuery ? "Sin coincidencias en el banco." : "Aún no hay códigos.");
    this._renderBankInto([...State.project.codes].reverse(), "code-bank-mini", "Aún no hay códigos.");
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
    for (const code of codes) {
      bank.appendChild(
        this.editingId === code.id ? this._editForm(code) : this._codeItem(code)
      );
    }
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
        Views.toast(`Cita añadida a «${code.name}»`);
      } catch (error) {
        Views.toast(error.message, true);
      }
    });

    const head = document.createElement("div");
    head.className = "code-head";
    const chip = document.createElement("span");
    chip.className = "dom-chip";
    chip.style.backgroundColor = State.domains[code.domain] || "#999";
    chip.title = code.domain;
    const name = document.createElement("span");
    name.className = "code-name";
    name.textContent = code.name;
    name.title = "Clic: ver todas las citas de este código";
    name.addEventListener("click", () => Views.showQuotes(code.name));
    const edit = document.createElement("button");
    edit.className = "icon-btn";
    edit.title = "Editar código";
    edit.textContent = "✎";
    edit.addEventListener("click", () => { this.editingId = code.id; this._renderBank(); });
    const del = document.createElement("button");
    del.className = "icon-btn";
    del.title = "Eliminar código";
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
      memo.textContent = `✎ ${code.memo}`;
      item.appendChild(memo);
    }
    const meta = document.createElement("div");
    meta.className = "code-meta";
    const docName = code.doc_id
      ? (State.project.documents.find(d => d.id === code.doc_id) || {}).filename || "?"
      : "Manual";
    meta.textContent = `#${code.id} · ${code.domain} · ${docName} · ${code.created_at.replace("T", " ")}`;
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
    memoInput.placeholder = "Memo…";

    const buttons = document.createElement("div");
    buttons.className = "code-edit-buttons";
    const save = document.createElement("button");
    save.className = "btn btn-small btn-accent";
    save.textContent = "GUARDAR";
    save.addEventListener("click", async () => {
      const name = nameInput.value.trim();
      if (!name) { Views.toast("El nombre no puede quedar vacío", true); return; }
      try {
        await API.updateCode(code.id, {
          name, domain: domainSelect.value, memo: memoInput.value.trim(),
        });
        this.editingId = null;
        await State.reload(); // el color del resaltado cambia con el dominio (FR-030)
        Views.toast("Código actualizado");
      } catch (error) {
        Views.toast(error.message, true);
      }
    });
    const cancel = document.createElement("button");
    cancel.className = "btn btn-small";
    cancel.textContent = "CANCELAR";
    cancel.addEventListener("click", () => { this.editingId = null; this._renderBank(); });
    buttons.append(save, cancel);

    form.append(domainSelect, nameInput, memoInput, buttons);
    return form;
  },

  async _deleteCode(code) {
    if (!await Views.confirm(`¿Eliminar el código «${code.name}»? Su resaltado desaparecerá del Canvas.`)) return;
    try {
      await API.deleteCode(code.id);
      await State.reload(); // FR-031: resaltado fuera, analytics al día
      Views.toast("Código eliminado");
    } catch (error) {
      Views.toast(error.message, true);
    }
  },
};
