/* Paleta de Control: código manual + memos, documentos del corpus y banco de
   códigos con edición/eliminación (FR-013/014, FR-030/031/033). */

const Paleta = {
  editingId: null,

  init() {
    document.getElementById("btn-manual-save").addEventListener("click", () => this._saveManual());
    document.getElementById("btn-reset").addEventListener("click", () => this._reset());
  },

  populateDomains() {
    const select = document.getElementById("manual-domain");
    select.textContent = "";
    for (const domain of Object.keys(State.domains)) {
      const option = document.createElement("option");
      option.value = domain;
      option.textContent = domain;
      select.appendChild(option);
    }
  },

  render() {
    this._renderDocs();
    this._renderBank();
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

  _renderBank() {
    const bank = document.getElementById("code-bank");
    bank.textContent = "";
    const codes = [...State.project.codes].reverse(); // más recientes arriba
    if (!codes.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = "Aún no hay códigos.";
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
    for (const domain of Object.keys(State.domains)) {
      const option = document.createElement("option");
      option.value = domain;
      option.textContent = domain;
      option.selected = domain === code.domain;
      domainSelect.appendChild(option);
    }
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
