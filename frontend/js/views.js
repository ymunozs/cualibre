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
    document.getElementById("btn-example").addEventListener("click", async () => {
      try {
        await API._fetch("/api/projects/example", { method: "POST" });
        await State.reload();
        this.toast("Proyecto de ejemplo creado — explóralo sin miedo, es ficticio");
      } catch (error) {
        this.toast(error.message, true);
      }
    });

    // Manual en la app (FR-052)
    document.getElementById("btn-manual").addEventListener("click", () => this._openManual());
    document.getElementById("manual-close").addEventListener("click", () => {
      document.getElementById("manual-dialog").close();
    });

    // NLP
    document.getElementById("nlp-lang").addEventListener("change", () => this.renderNlp());
    const minLen = document.getElementById("nlp-minlen");
    minLen.addEventListener("input", () => {
      document.getElementById("nlp-minlen-value").textContent = minLen.value;
    });
    minLen.addEventListener("change", () => this.renderNlp());
    document.getElementById("nlp-pos").addEventListener("change", () => this.renderNlp());

    // Literatura
    document.getElementById("btn-lit-search").addEventListener("click", () => this._searchLiterature());
    document.getElementById("lit-query").addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._searchLiterature();
    });

    // Exclusiones NLP (FR-048) — ADITIVAS: lo nuevo se suma a lo guardado
    const applyExclusions = async () => {
      const input = document.getElementById("nlp-exclusions");
      const nuevas = input.value.split(",").map(w => w.trim()).filter(Boolean);
      const merged = [...new Set([...this._exclusions, ...nuevas])];
      try {
        const { exclusions } = await API.setNlpExclusions(merged);
        this._exclusions = exclusions;
        input.value = "";
        this.toast(nuevas.length ? `Omitiendo ${exclusions.length} palabra(s) en total` : "Sin cambios");
        this.renderNlp();
      } catch (error) {
        this.toast(error.message, true);
      }
    };
    document.getElementById("btn-nlp-exclusions").addEventListener("click", applyExclusions);
    document.getElementById("nlp-exclusions").addEventListener("keydown", (e) => {
      if (e.key === "Enter") applyExclusions();
    });

    // Exportar organizadores gráficos (FR-049)
    document.getElementById("btn-export-cloud").addEventListener("click", () => {
      Charts.downloadCanvas(document.getElementById("wordcloud"), "cualibre_nube_de_conceptos.png");
    });
    const graphSvg = () => document.querySelector("#rel-graph svg");
    document.getElementById("btn-export-graph-svg").addEventListener("click", () => {
      const svg = graphSvg();
      svg ? Charts.downloadSvg(svg, "cualibre_organizador.svg")
          : this.toast("Crea relaciones para exportar el organizador", true);
    });
    document.getElementById("btn-export-graph-png").addEventListener("click", () => {
      const svg = graphSvg();
      svg ? Charts.downloadSvgAsPng(svg, "cualibre_organizador.png")
          : this.toast("Crea relaciones para exportar el organizador", true);
    });

    // Modo inmersión (FR-044): solo el Canvas, para leer sin ruido
    document.getElementById("btn-immersion").addEventListener("click", () => {
      document.body.classList.toggle("immersion");
    });

    // Reporte académico (FR-060)
    document.getElementById("btn-report").addEventListener("click", () => Reporte.generar());

    // Recuperación de citas: cerrar diálogo
    document.getElementById("quotes-close").addEventListener("click", () => {
      document.getElementById("quotes-dialog").close();
    });

    // Preferencias de lectura persistentes (FR-054/056/057)
    const prefToggles = [
      ["btn-dark", "dark", "cua-dark"],
      ["btn-font", "canvas-mono", "cua-font-mono"],
      ["btn-linenum", "no-linenum", "cua-no-linenum"],
    ];
    for (const [btnId, cls, key] of prefToggles) {
      if (localStorage.getItem(key) === "1") document.body.classList.add(cls);
      document.getElementById(btnId).addEventListener("click", () => {
        document.body.classList.toggle(cls);
        localStorage.setItem(key, document.body.classList.contains(cls) ? "1" : "0");
      });
    }

    // Teclas globales: ⌘F busca en el corpus; Esc sale de inmersión
    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "f") {
        e.preventDefault();
        document.body.classList.remove("immersion");
        this.show("pentagrama");
        document.getElementById("search-input").focus();
      }
      if (e.key === "Escape" && document.body.classList.contains("immersion")
          && document.getElementById("nube").classList.contains("hidden")) {
        document.body.classList.remove("immersion");
      }
      // Deshacer última codificación (FR-050) — fuera de campos de texto
      if ((e.metaKey || e.ctrlKey) && e.key === "z"
          && !e.target.matches("input, textarea, select")) {
        e.preventDefault();
        this._undoLastCode();
      }
    });
  },

  /* Recuperación de citas por código (FR-055): todas las citas de un nombre */
  showQuotes(codeName) {
    const dialog = document.getElementById("quotes-dialog");
    const body = document.getElementById("quotes-body");
    const instances = State.project.codes.filter(c => c.name === codeName);
    const docNames = {};
    for (const d of State.project.documents) docNames[d.id] = d.filename;
    document.getElementById("quotes-title").textContent =
      `CITAS DE «${codeName.toUpperCase()}» (${instances.length})`;
    body.textContent = "";
    for (const code of instances) {
      const item = document.createElement("div");
      item.className = "quote-item";
      const head = document.createElement("div");
      head.className = "quote-meta";
      const chip = document.createElement("span");
      chip.className = "dom-chip";
      chip.style.backgroundColor = State.domains[code.domain] || "#999";
      head.append(chip, document.createTextNode(
        ` ${code.domain} · ${code.doc_id ? docNames[code.doc_id] || "?" : "Manual"} · ${code.created_at.replace("T", " ")}`
      ));
      item.appendChild(head);
      const quote = document.createElement("div");
      quote.className = "quote-text";
      quote.textContent = code.quote ? `“${code.quote}”` : "(código manual, sin cita)";
      item.appendChild(quote);
      if (code.memo) {
        const memo = document.createElement("div");
        memo.className = "quote-meta";
        memo.textContent = `✎ ${code.memo}`;
        item.appendChild(memo);
      }
      if (code.doc_id) {
        const go = document.createElement("button");
        go.className = "btn btn-small";
        go.textContent = "IR AL CANVAS →";
        go.addEventListener("click", () => {
          dialog.close();
          this.show("pentagrama");
          Canvas.goToQuote(code);
        });
        item.appendChild(go);
      }
      body.appendChild(item);
    }
    dialog.showModal();
  },

  _manualLoaded: false,
  async _openManual() {
    const dialog = document.getElementById("manual-dialog");
    dialog.showModal();
    if (!this._manualLoaded) {
      try {
        const { html } = await API._fetch("/api/manual");
        document.getElementById("manual-body").innerHTML = html;
        this._manualLoaded = true;
      } catch (error) {
        document.getElementById("manual-body").textContent = error.message;
      }
    }
  },

  async _undoLastCode() {
    const codes = State.project.codes;
    if (!codes.length) { this.toast("Nada que deshacer", true); return; }
    const last = codes.reduce((a, b) => (a.id > b.id ? a : b));
    try {
      await API.deleteCode(last.id);
      await State.reload();
      this.toast(`Deshecho: «${last.name}»`);
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  /* Indicador de autoguardado (FR-047): pulso tras cada sincronización */
  pulseSaved() {
    const dot = document.getElementById("save-dot");
    dot.classList.remove("pulse");
    void dot.offsetWidth; // reiniciar la animación
    dot.classList.add("pulse");
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
    else if (this.current === "sentimiento") this.renderSentiment();
  },

  /* ---------- Sentimiento (FR-059) ---------- */

  async renderSentiment() {
    let data;
    try {
      data = await API.sentiment();
    } catch (error) {
      this.toast(error.message, true);
      return;
    }
    const empty = document.getElementById("sent-empty");
    const body = document.getElementById("sent-body");
    if (!data.documents.length) {
      empty.classList.remove("hidden");
      body.classList.add("hidden");
      return;
    }
    empty.classList.add("hidden");
    body.classList.remove("hidden");

    // Documentos: score + arco
    const docsBox = document.getElementById("sent-docs");
    docsBox.textContent = "";
    for (const doc of data.documents) {
      const card = document.createElement("div");
      card.className = "sent-doc-card";
      const head = document.createElement("div");
      head.className = "sent-doc-head";
      const sign = doc.score > 0.05 ? "positivo" : doc.score < -0.05 ? "negativo" : "neutro";
      head.textContent = `${doc.filename} — valencia ${doc.score > 0 ? "+" : ""}${doc.score} (${sign}, ${doc.matched} palabras con carga)`;
      card.appendChild(head);
      const arcBox = document.createElement("div");
      Charts.line(arcBox, doc.arc);
      card.appendChild(arcBox);
      docsBox.appendChild(card);
    }

    // Dominios y códigos: barras divergentes con colores oficiales
    Charts.diverging(document.getElementById("sent-domains"),
      data.domains.map(d => ({ label: d.domain, value: d.score, sublabel: `${d.n} citas`, color: State.domains[d.domain] })));
    Charts.diverging(document.getElementById("sent-codes"),
      data.codes.map(c => ({ label: c.name, value: c.score, sublabel: `${c.n} citas`, color: State.domains[c.domain] })));

    // Emociones (conteos, un solo tono) y palabras con carga
    Charts.hbar(document.getElementById("sent-emotions"),
      data.emotions.map(e => ({ label: e.emotion, value: e.count, color: "#FF3300" })));
    const rows = [];
    const maxLen = Math.max(data.words.positive.length, data.words.negative.length);
    for (let i = 0; i < maxLen; i++) {
      const p = data.words.positive[i], n = data.words.negative[i];
      rows.push([p ? `${p.word} (${p.count})` : "", n ? `${n.word} (${n.count})` : ""]);
    }
    Charts.table(document.getElementById("sent-words"), ["Positivas ↑", "Negativas ↓"], rows);
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

    this._renderCooccurrence(codes);
  },

  /* Co-ocurrencia (FR-043): dos códigos co-ocurren cuando sus citas se solapan
     en el mismo documento. Matrices código×código y documento×código. */
  _renderCooccurrence(codes) {
    const section = document.getElementById("cooc-section");
    const anchored = codes.filter(c => c.doc_id !== null);
    const counts = new Map();
    for (const code of anchored) counts.set(code.name, (counts.get(code.name) || 0) + 1);
    const names = [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12)
      .map(([name]) => name);

    if (names.length < 2) {
      section.classList.add("hidden");
      return;
    }
    section.classList.remove("hidden");

    const index = new Map(names.map((n, i) => [n, i]));
    const matrix = names.map(() => names.map(() => 0));
    for (let a = 0; a < anchored.length; a++) {
      for (let b = a + 1; b < anchored.length; b++) {
        const A = anchored[a], B = anchored[b];
        if (A.doc_id !== B.doc_id || A.name === B.name) continue;
        if (A.start < B.end && B.start < A.end) { // solapamiento de rangos
          const i = index.get(A.name), j = index.get(B.name);
          if (i === undefined || j === undefined) continue;
          matrix[i][j]++;
          matrix[j][i]++;
        }
      }
    }
    Charts.heatmap(document.getElementById("chart-cooc"), names, names, matrix);

    // Documento × código
    const docs = State.project.documents;
    const docMatrix = docs.map(doc =>
      names.map(name =>
        anchored.filter(c => c.doc_id === doc.id && c.name === name).length
      )
    );
    Charts.heatmap(
      document.getElementById("chart-doccode"),
      docs.map(d => d.filename), names, docMatrix
    );
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
        const data = await API.nlp(lang, minLen, document.getElementById("nlp-pos").value);
        words = data.words;
        this._exclusions = data.exclusions || [];
        this._renderExclusionChips();
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

  _exclusions: [],
  _renderExclusionChips() {
    const box = document.getElementById("nlp-exclusion-chips");
    box.textContent = "";
    for (const word of this._exclusions) {
      const chip = document.createElement("button");
      chip.className = "filter-chip";
      chip.title = `Dejar de omitir «${word}»`;
      chip.textContent = `${word} ✕`;
      chip.addEventListener("click", async () => {
        try {
          const { exclusions } = await API.setNlpExclusions(this._exclusions.filter(w => w !== word));
          this._exclusions = exclusions;
          this.renderNlp();
        } catch (error) {
          this.toast(error.message, true);
        }
      });
      box.appendChild(chip);
    }
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
