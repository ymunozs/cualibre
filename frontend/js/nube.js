/* Nube Negra: popup efímero de codificación (FR-009–012).
   Flujo expedito (Principio III): selección → dominio → nombre → ENTER.
   ESC o clic fuera cancelan sin dejar rastro. Teclas 1–9 eligen dominio. */

const Nube = {
  el: null,
  domainSelect: null,
  nameInput: null,
  selection: null, // {docId, start, end, quote}

  init() {
    this.el = document.getElementById("nube");
    this.domainSelect = document.getElementById("nube-domain");
    this.nameInput = document.getElementById("nube-name");

    this.el.addEventListener("keydown", (e) => this._onKeyDown(e));
    // Clic fuera → cancelar (capture: antes de que otros handlers actúen)
    document.addEventListener("mousedown", (e) => {
      if (!this.el.classList.contains("hidden") && !this.el.contains(e.target)) {
        this.hide();
      }
    }, true);
  },

  populateDomains() {
    this.domainSelect.textContent = "";
    Object.keys(State.domains).forEach((domain, i) => {
      const option = document.createElement("option");
      option.value = domain;
      option.textContent = `${i + 1} · ${domain}`;
      this.domainSelect.appendChild(option);
    });
  },

  show(rect, selection) {
    this.selection = selection;
    this.nameInput.value = "";
    this.nameInput.classList.remove("error");
    this.nameInput.placeholder = "Nombre del código…";

    this.el.classList.remove("hidden");
    const width = this.el.offsetWidth;
    let left = rect.left + window.scrollX;
    const maxLeft = window.scrollX + document.documentElement.clientWidth - width - 12;
    if (left > maxLeft) left = maxLeft;
    this.el.style.left = `${Math.max(12, left)}px`;
    this.el.style.top = `${rect.bottom + window.scrollY + 10}px`;

    this.nameInput.focus();
  },

  hide() {
    this.el.classList.add("hidden");
    this.selection = null;
  },

  _onKeyDown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      this.hide();
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      this._commit();
      return;
    }
    // 1–9 eligen dominio cuando el foco está en el selector,
    // o desde el campo de nombre mientras aún está vacío
    if (/^[1-9]$/.test(event.key)) {
      const onSelect = event.target === this.domainSelect;
      const onEmptyName = event.target === this.nameInput && this.nameInput.value === "";
      if (onSelect || onEmptyName) {
        const index = parseInt(event.key, 10) - 1;
        if (index < this.domainSelect.options.length) {
          event.preventDefault();
          this.domainSelect.selectedIndex = index;
          this.nameInput.focus();
        }
      }
    }
  },

  async _commit() {
    if (!this.selection) return;
    const name = this.nameInput.value.trim();
    if (!name) { // FR-012: sin nombre no se guarda, y se indica
      this.nameInput.value = "";
      this.nameInput.placeholder = "⚠ Falta el nombre del código";
      this.nameInput.classList.add("error");
      this.nameInput.focus();
      return;
    }
    const payload = {
      doc_id: this.selection.docId,
      domain: this.domainSelect.value,
      name,
      quote: this.selection.quote,
      start: this.selection.start,
      end: this.selection.end,
      memo: "",
    };
    this.hide();
    window.getSelection().removeAllRanges();
    try {
      await API.createCode(payload);
      await State.reload(); // resaltado + banco + analytics inmediatos (FR-010)
      Views.toast(`Codificado: ${name}`);
    } catch (error) {
      Views.toast(error.message, true);
    }
  },
};
