/* Vistas: pestañas, importador, selector de proyectos, NLP, Analytics,
   Exportar y Literatura. */

const Views = {
  current: "pentagrama",

  init() {
    // Pestañas
    document.querySelectorAll("#tabs .tab").forEach(tab => {
      tab.addEventListener("click", () => this.show(tab.dataset.view));
    });

    // Importador (FR-001: jerarquía superior)
    document.getElementById("file-input").addEventListener("change", (e) => this._import(e));

    // Proyectos (FR-032)
    document.getElementById("project-select").addEventListener("change", (e) => this._switchProject(e));
    document.getElementById("btn-new-project").addEventListener("click", () => this._newProject());
    document.getElementById("btn-rename-project").addEventListener("click", () => this._renameProject());
    document.getElementById("btn-save-project").addEventListener("click", () => this._saveProject());

    // NLP
    document.getElementById("nlp-lang").addEventListener("change", () => this.renderNlp());
    const minLen = document.getElementById("nlp-minlen");
    minLen.addEventListener("input", () => {
      document.getElementById("nlp-minlen-value").textContent = minLen.value;
    });
    minLen.addEventListener("change", () => this.renderNlp());

    // Literatura
    document.getElementById("btn-lit-search").addEventListener("click", () => this._searchLiterature());
    document.getElementById("lit-query").addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._searchLiterature();
    });
  },

  show(view) {
    this.current = view;
    document.querySelectorAll("#tabs .tab").forEach(tab => {
      tab.classList.toggle("active", tab.dataset.view === view);
    });
    document.querySelectorAll("main .view").forEach(section => {
      section.classList.toggle("hidden", section.id !== `view-${view}`);
    });
    this.refreshCurrent();
  },

  refreshCurrent() {
    if (this.current === "analytics") this.renderAnalytics();
    else if (this.current === "nlp") this.renderNlp();
    else if (this.current === "exportar") this.renderExport();
    else if (this.current === "relaciones") Relations.render();
  },

  async _saveProject() {
    try {
      const { updated_at } = await API.saveProject();
      const time = updated_at.split("T")[1] || updated_at;
      this.toast(`💾 Proyecto guardado (${time})`);
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  // ---------- Importador ----------

  async _import(event) {
    const files = [...event.target.files];
    if (!files.length) return;
    const status = document.getElementById("import-status");
    for (const file of files) {
      status.textContent = `Importando ${file.name}…`;
      try {
        await API.uploadDocument(file);
        this.toast(`Importado: ${file.name}`);
      } catch (error) {
        this.toast(error.message, true);
      }
    }
    status.textContent = "";
    event.target.value = "";
    await State.reload();
  },

  // ---------- Proyectos ----------

  renderProjectBar(projects) {
    const select = document.getElementById("project-select");
    select.textContent = "";
    for (const project of projects) {
      const option = document.createElement("option");
      option.value = project.id;
      option.textContent = project.name;
      option.selected = project.id === State.project.id;
      select.appendChild(option);
    }
  },

  async _switchProject(event) {
    try {
      await API.activateProject(event.target.value);
      await State.reload();
      this.toast(`Proyecto activo: ${State.project.name}`);
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  async _newProject() {
    const name = prompt("Nombre del nuevo proyecto:");
    if (!name || !name.trim()) return;
    try {
      await API.createProject(name.trim());
      await State.reload();
      this.toast(`Proyecto creado: ${name.trim()}`);
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  async _renameProject() {
    const name = prompt("Nuevo nombre del proyecto:", State.project.name);
    if (!name || !name.trim() || name.trim() === State.project.name) return;
    try {
      await API.renameProject(State.project.id, name.trim());
      await State.reload();
      this.toast("Proyecto renombrado");
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  // ---------- Analytics (FR-019/020) ----------

  renderAnalytics() {
    const codes = State.project.codes;
    const empty = document.getElementById("analytics-empty");
    const charts = document.getElementById("analytics-charts");
    if (!codes.length) {
      empty.classList.remove("hidden");
      charts.classList.add("hidden");
      return;
    }
    empty.classList.add("hidden");
    charts.classList.remove("hidden");

    // Torta: distribución por dominios, en el orden fijo de la paleta
    const byDomain = {};
    for (const code of codes) byDomain[code.domain] = (byDomain[code.domain] || 0) + 1;
    const pieData = Object.keys(State.domains)
      .filter(domain => byDomain[domain])
      .map(domain => ({ label: domain, value: byDomain[domain], color: State.domains[domain] }));
    Charts.pie(document.getElementById("chart-pie"), pieData);

    // Barras: densidad por código (color = dominio del código)
    const byName = new Map();
    for (const code of codes) {
      const key = JSON.stringify([code.name, code.domain]);
      byName.set(key, (byName.get(key) || 0) + 1);
    }
    const barData = [...byName.entries()]
      .map(([key, value]) => {
        const [label, domain] = JSON.parse(key);
        return { label, sublabel: domain, value, color: State.domains[domain] };
      })
      .sort((a, b) => b.value - a.value)
      .slice(0, 20);
    Charts.hbar(document.getElementById("chart-bars"), barData);
  },

  // ---------- NLP (FR-017/018/034) ----------

  async renderNlp() {
    if (this.current !== "nlp") return;
    const emptyNote = document.getElementById("nlp-empty");
    const hasCorpus = State.project.documents.length > 0;
    emptyNote.classList.toggle("hidden", hasCorpus);
    const lang = document.getElementById("nlp-lang").value;
    const minLen = document.getElementById("nlp-minlen").value;

    let words = [];
    if (hasCorpus) {
      try {
        words = (await API.nlp(lang, minLen)).words;
      } catch (error) {
        this.toast(error.message, true);
        return;
      }
    }
    // Tres visualizaciones simultáneas y coherentes (FR-018)
    WordCloud.render(document.getElementById("wordcloud"), words);
    Charts.hbar(
      document.getElementById("nlp-bars"),
      words.slice(0, 15).map(w => ({ label: w.word, value: w.count, color: "#FF3300" }))
    );
    Charts.table(
      document.getElementById("nlp-table"),
      ["#", "Palabra", "Frecuencia"],
      words.map((w, i) => [i + 1, w.word, w.count])
    );
  },

  // ---------- Exportar (FR-021) ----------

  renderExport() {
    const docNames = {};
    for (const doc of State.project.documents) docNames[doc.id] = doc.filename;
    Charts.table(
      document.getElementById("export-table"),
      ["ID", "Fecha", "Documento", "Dominio", "Código", "Cita", "Memo"],
      State.project.codes.map(code => [
        code.id,
        code.created_at.replace("T", " "),
        code.doc_id ? (docNames[code.doc_id] || "?") : "Manual",
        code.domain,
        code.name,
        code.quote,
        code.memo,
      ])
    );
  },

  // ---------- Literatura (FR-023/024) ----------

  async _searchLiterature() {
    const query = document.getElementById("lit-query").value.trim();
    if (!query) return;
    const results = document.getElementById("lit-results");
    results.textContent = "Buscando en OpenAlex…";
    try {
      const { results: works } = await API.literature(query);
      results.textContent = "";
      if (!works.length) {
        results.textContent = "Sin resultados para esa búsqueda.";
        return;
      }
      for (const work of works) {
        const card = document.createElement("div");
        card.className = "lit-card";
        const title = document.createElement("div");
        title.className = "lit-title";
        title.textContent = work.title;
        const meta = document.createElement("div");
        meta.className = "lit-meta";
        meta.textContent = `Año: ${work.year ?? "?"} · Citas: ${work.cited_by_count}`;
        card.append(title, meta);
        if (work.doi) {
          const link = document.createElement("a");
          link.href = work.doi;
          link.target = "_blank";
          link.rel = "noopener";
          link.textContent = "Enlace DOI →";
          card.appendChild(link);
        }
        results.appendChild(card);
      }
    } catch (error) {
      results.textContent = "";
      this.toast(error.message, true);
    }
  },

  // ---------- Utilidades ----------

  _toastTimer: null,
  toast(message, isError = false) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.remove("hidden");
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => toast.classList.add("hidden"), isError ? 5000 : 2600);
  },

  confirm(message) {
    return new Promise(resolve => {
      const dialog = document.getElementById("confirm-dialog");
      document.getElementById("confirm-message").textContent = message;
      const ok = document.getElementById("confirm-ok");
      const cancel = document.getElementById("confirm-cancel");
      const cleanup = (result) => {
        ok.onclick = cancel.onclick = null;
        dialog.close();
        resolve(result);
      };
      ok.onclick = () => cleanup(true);
      cancel.onclick = () => cleanup(false);
      dialog.showModal();
    });
  },
};
