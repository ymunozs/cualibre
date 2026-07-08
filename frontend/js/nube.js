/* Nube Negra: popup efímero de codificación (FR-009–012).
   Flujo expedito (Principio III): selección → categoría → nombre → ENTER.
   ESC o clic fuera cancelan sin dejar rastro. Teclas 1–9 eligen una de las
   Categorías Básicas directamente, sin abrir el menú.

   Selector de categoría (FR-064): ya no es un <select> plano. Es un menú
   propio con "Categorías Básicas" como un ítem que despliega sus 9 opciones
   en un submenú lateral al pasar el cursor (como las familias de menú de
   iOS/Windows), más las categorías personalizadas del proyecto listadas
   directamente, y una opción para crear una nueva. */

const Nube = {
  el: null,
  nameInput: null,
  selection: null, // {docId, start, end, quote}
  selectedDomain: null,

  init() {
    this.el = document.getElementById("nube");
    this.nameInput = document.getElementById("nube-name");
    this.domainBtn = document.getElementById("nube-domain-btn");
    this.domainLabel = document.getElementById("nube-domain-label");
    this.domainMenu = document.getElementById("nube-domain-menu");
    this.customList = document.getElementById("nube-custom-domains");
    this.basicSubmenu = document.getElementById("nube-basic-submenu");
    this.basicToggle = document.getElementById("nube-basic-toggle");
    this.newDomainForm = document.getElementById("nube-new-domain-form");
    this.newDomainName = document.getElementById("nube-new-domain-name");
    this.newDomainColor = document.getElementById("nube-new-domain-color");

    this.el.addEventListener("keydown", (e) => this._onKeyDown(e));
    this.domainBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.domainMenu.classList.toggle("hidden");
    });
    // Clic en "Categorías Básicas": alternativa al hover para abrir el submenú
    this.basicToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      this.basicToggle.parentElement.classList.toggle("open");
    });
    // Mini-formulario inline para crear categorías (nunca prompt()+color
    // encadenados: varios navegadores invalidan el "gesto de usuario" tras un
    // diálogo bloqueante como prompt(), y el color picker nativo simplemente
    // no se abre — la categoría nunca se creaba. Con inputs siempre visibles
    // dentro del menú, el clic en el color es un gesto directo y confiable.
    document.getElementById("nube-new-domain").addEventListener("click", (e) => {
      e.stopPropagation();
      this.newDomainForm.classList.toggle("hidden");
      if (!this.newDomainForm.classList.contains("hidden")) {
        this.newDomainName.value = "";
        this.newDomainName.focus();
      }
    });
    this.newDomainName.addEventListener("keydown", (e) => {
      e.stopPropagation(); // no debe llegar al keydown de la Nube (guardaría el código)
      if (e.key === "Enter") { e.preventDefault(); this._createCustomDomain(); }
      if (e.key === "Escape") { e.preventDefault(); this.newDomainForm.classList.add("hidden"); }
    });
    document.getElementById("nube-new-domain-confirm").addEventListener("click", (e) => {
      e.stopPropagation();
      this._createCustomDomain();
    });
    // Clic dentro del menú no debe cerrar la Nube completa
    this.domainMenu.addEventListener("mousedown", (e) => e.stopPropagation());

    // Clic fuera → cancelar (capture: antes de que otros handlers actúen)
    document.addEventListener("mousedown", (e) => {
      if (!this.domainMenu.classList.contains("hidden") && !this.domainMenu.contains(e.target)
          && e.target !== this.domainBtn) {
        this._closeDomainMenu();
      }
      if (!this.el.classList.contains("hidden") && !this.el.contains(e.target)) {
        this.hide();
      }
    }, true);
  },

  _closeDomainMenu() {
    this.domainMenu.classList.add("hidden");
    this.basicToggle.parentElement.classList.remove("open");
    this.newDomainForm.classList.add("hidden");
  },

  _selectDomain(name) {
    this.selectedDomain = name;
    this.domainLabel.textContent = name;
    const color = State.domains[name] || "#999";
    this.domainBtn.style.setProperty("--dom-color", color);
    this._closeDomainMenu();
    this.nameInput.focus();
  },

  populateDomains() {
    // Categorías personalizadas: listado plano al tope del menú
    this.customList.textContent = "";
    for (const name of Object.keys(State.customDomains)) {
      const item = document.createElement("div");
      item.className = "domain-menu-item";
      const dot = document.createElement("span");
      dot.className = "dom-chip";
      dot.style.backgroundColor = State.customDomains[name];
      item.append(dot, document.createTextNode(name));
      item.addEventListener("click", () => this._selectDomain(name));
      this.customList.appendChild(item);
    }

    // Categorías Básicas: submenú lateral, orden fijo (también usado por 1–9)
    this.basicSubmenu.textContent = "";
    Object.keys(State.basicDomains).forEach((name, i) => {
      const item = document.createElement("div");
      item.className = "domain-menu-item";
      const dot = document.createElement("span");
      dot.className = "dom-chip";
      dot.style.backgroundColor = State.basicDomains[name];
      const label = document.createElement("span");
      label.textContent = `${i + 1} · ${name}`;
      item.append(dot, label);
      item.addEventListener("click", () => this._selectDomain(name));
      this.basicSubmenu.appendChild(item);
    });

    // Si no hay selección vigente (o la categoría elegida desapareció), usar
    // la primera Categoría Básica por defecto.
    if (!this.selectedDomain || !State.domains[this.selectedDomain]) {
      this._selectDomain(Object.keys(State.basicDomains)[0]);
    }
  },

  async _createCustomDomain() {
    const name = this.newDomainName.value.trim();
    if (!name) { this.newDomainName.focus(); return; }
    const color = this.newDomainColor.value;
    try {
      await API.createCustomDomain(name, color);
      this.newDomainForm.classList.add("hidden");
      // Reload completo: refresca también el panel de la Paleta, no solo la Nube
      await State.reload();
      this._selectDomain(name);
      Views.toast(`Categoría creada: ${name}`);
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  show(rect, selection) {
    this.selection = selection;
    this.nameInput.value = "";
    this.nameInput.classList.remove("error");
    this.nameInput.placeholder = "Nombre del código…";
    this._closeDomainMenu();

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
    this._closeDomainMenu();
    this.selection = null;
  },

  _onKeyDown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      if (!this.domainMenu.classList.contains("hidden")) { this._closeDomainMenu(); return; }
      this.hide();
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      // ⌘↵ / Ctrl+↵: repetir la última codificación sobre esta selección (FR-046)
      if ((event.metaKey || event.ctrlKey) && this.last) {
        this._selectDomain(this.last.domain);
        this.nameInput.value = this.last.name;
      }
      this._commit();
      return;
    }
    // 1–9 eligen una Categoría Básica directamente, en cualquier momento
    // mientras el nombre está vacío (no interfiere con escribir números en el nombre)
    if (/^[1-9]$/.test(event.key) && event.target === this.nameInput && this.nameInput.value === "") {
      const names = Object.keys(State.basicDomains);
      const index = parseInt(event.key, 10) - 1;
      if (index < names.length) {
        event.preventDefault();
        this._selectDomain(names[index]);
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
      domain: this.selectedDomain,
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
      this.last = { domain: payload.domain, name: payload.name }; // para ⌘↵ (FR-046)
      await State.reload(); // resaltado + banco + analytics inmediatos (FR-010)
      Views.toast(`Codificado: ${name}`);
    } catch (error) {
      Views.toast(error.message, true);
    }
  },
};
