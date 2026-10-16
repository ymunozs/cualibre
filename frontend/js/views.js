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

    // Proyectos (FR-032) + importar/eliminar (FR-073)
    document.getElementById("project-select").addEventListener("change", (e) => this._switchProject(e));
    document.getElementById("btn-new-project").addEventListener("click", () => this._newProject());
    document.getElementById("btn-rename-project").addEventListener("click", () => this._renameProject());
    document.getElementById("btn-save-project").addEventListener("click", () => this._saveProject());
    document.getElementById("btn-delete-project").addEventListener("click", () => this._deleteProject());
    const projectFile = document.getElementById("project-file");
    document.getElementById("btn-import-project").addEventListener("click", () => projectFile.click());
    projectFile.addEventListener("change", (e) => this._importProject(e));
    document.getElementById("btn-example").addEventListener("click", async () => {
      try {
        await API.createExample();
        await State.reload();
        this.toast(I18N.t("toast.demo"));
      } catch (error) {
        this.toast(error.message, true);
      }
    });

    // Diálogos con botón de cierre
    for (const [openId, dialogId, closeId] of [
      ["btn-about", "about-dialog", "about-close"],
      [null, "manual-dialog", "manual-close"],
      [null, "history-dialog", "history-close"],
      [null, "kwic-dialog", "kwic-close"],
      [null, "emotion-words-dialog", "emotion-words-close"],
      [null, "quotes-dialog", "quotes-close"],
    ]) {
      const dialog = document.getElementById(dialogId);
      if (openId) document.getElementById(openId).addEventListener("click", () => dialog.showModal());
      document.getElementById(closeId).addEventListener("click", () => dialog.close());
    }
    document.getElementById("btn-manual").addEventListener("click", () => this._openManual());
    document.getElementById("btn-history").addEventListener("click", () => this._openHistory());

    // Concordancias / KWIC (FR-063)
    WordCloud.onWordClick = (word) => this.openKwic(word);

    // Ajustes del léxico (FR-086): sumar una palabra a la categoría abierta
    const addWord = () => {
      const input = document.getElementById("lexf-add-input");
      const word = input.value.trim().toLowerCase();
      if (!word || !this._lexCat) return;
      input.value = "";
      this._adjustLexicon(this._lexCat, word, "add");
    };
    document.getElementById("lexf-add-btn").addEventListener("click", addWord);
    document.getElementById("lexf-add-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); addWord(); }
    });

    // NLP
    // Idioma del corpus: un solo valor por proyecto, compartido por NLP y Sentimiento
    document.querySelectorAll("select.corpus-lang").forEach(select => {
      select.addEventListener("change", () => this._setCorpusLang(select.value));
    });

    // Léxicos de sentimiento en inglés y portugués (FR-077)
    document.getElementById("btn-lex-download").addEventListener("click", () => this._installLexicons());
    document.getElementById("lexicon-file").addEventListener("change", (e) => this._installLexicons(e));

    // Modo navegador: botón para apagar la app (en la ventana basta con cerrarla)
    const quit = document.getElementById("btn-quit");
    quit.classList.toggle("hidden", Files.mode !== "browser");
    quit.addEventListener("click", () => this._quit());
    this._renderOcrHint();
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
        this.toast(nuevas.length
          ? I18N.t("nlp.exclusions.count", { n: exclusions.length })
          : I18N.t("nlp.exclusions.nochange"));
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
          : this.toast(I18N.t("rel.graph.export.empty"), true);
    });
    document.getElementById("btn-export-graph-png").addEventListener("click", () => {
      const svg = graphSvg();
      svg ? Charts.downloadSvgAsPng(svg, "cualibre_organizador.png")
          : this.toast(I18N.t("rel.graph.export.empty"), true);
    });

    // Modo inmersión (FR-044): solo el Canvas, para leer sin ruido
    document.getElementById("btn-immersion").addEventListener("click", () => {
      document.body.classList.toggle("immersion");
    });

    // REFI-QDA: perfil de destino (NVivo cuenta posiciones distinto, ver qdpx.py)
    document.getElementById("qdpx-profile").addEventListener("change", (e) => {
      const link = document.getElementById("btn-export-qdpx");
      link.dataset.download = `/api/export.qdpx?profile=${e.target.value}`;
      I18N.apply(link.parentElement);
    });

    // Reporte académico (FR-060)
    document.getElementById("btn-report").addEventListener("click", () => Reporte.generar());

    // Preferencias de lectura persistentes (FR-054/056/057)
    const prefToggles = [
      ["btn-dark", "dark", "cua-dark"],
      ["btn-font", "canvas-mono", "cua-font-mono"],
      ["btn-linenum", "no-linenum", "cua-no-linenum"],
    ];
    for (const [btnId, cls, key] of prefToggles) {
      if (Canvas._readPref(key) === "1") document.body.classList.add(cls);
      document.getElementById(btnId).addEventListener("click", () => {
        document.body.classList.toggle(cls);
        Canvas._writePref(key, document.body.classList.contains(cls) ? "1" : "0");
      });
    }

    // Teclas globales: ⌘F / Ctrl+F busca en el corpus; Esc sale de inmersión
    document.addEventListener("keydown", (e) => {
      const key = (e.key || "").toLowerCase(); // Bloq Mayús activo → "F"
      if ((e.metaKey || e.ctrlKey) && key === "f") {
        e.preventDefault();
        document.body.classList.remove("immersion");
        this.show("pentagrama");
        document.getElementById("search-input").focus();
      }
      if (e.key === "Escape" && document.body.classList.contains("immersion")
          && document.getElementById("nube").classList.contains("hidden")) {
        document.body.classList.remove("immersion");
      }
      // Deshacer última codificación (FR-050) — fuera de campos de texto.
      // En Relaciones no: ahí se espera deshacer un movimiento, que tiene su
      // propio botón (FR-087); borrar una cita por error sería grave.
      if ((e.metaKey || e.ctrlKey) && key === "z" && !e.shiftKey
          && !e.target.matches("input, textarea, select")) {
        e.preventDefault();
        if (this.current === "relaciones") {
          this.toast(I18N.t("rel.undo.hint"));
          return;
        }
        if (this.current === "literatura") { // tampoco en la biblioteca (FR-090)
          this.toast(I18N.t("lib.undo.hint"));
          return;
        }
        this._undoLastCode();
      }
    });

    // Cambio de idioma: el manual se vuelve a pedir en el idioma nuevo
    I18N.onChange(() => {
      this._manualLoaded = false;
      if (document.getElementById("manual-dialog").open) this._openManual();
      this._renderOcrHint();
    });
  },

  _renderOcrHint() {
    document.getElementById("import-ocr-hint").textContent =
      Files.ocr ? I18N.t("import.ocr.hint", { engine: Files.ocr }) : "";
  },

  get corpusLang() {
    return (State.project && State.project.corpus_lang) || "es";
  },

  _syncCorpusLang() {
    document.querySelectorAll("select.corpus-lang").forEach(s => { s.value = this.corpusLang; });
  },

  async _setCorpusLang(lang) {
    try {
      await API.setCorpusLang(lang);
      State.project.corpus_lang = lang;
      this._syncCorpusLang();
      this.refreshCurrent();
    } catch (error) {
      this.toast(error.message, true);
      this._syncCorpusLang();
    }
  },

  async _installLexicons(event) {
    const file = event && event.target.files[0];
    if (event) event.target.value = "";
    if (event && !file) return;
    const progress = this._progress("sent-progress");
    document.getElementById("sent-progress").textContent = I18N.t("lex.downloading");
    document.getElementById("sent-progress").classList.remove("hidden");
    try {
      const { installed } = file ? await API.importLexicons(file) : await API.downloadLexicons();
      const names = Object.keys(installed).map(l => I18N.t(`langname.${l}`)).join(", ");
      this.toast(I18N.t("lex.installed", { langs: names }));
      progress.hide();
      this.renderSentiment();
    } catch (error) {
      progress.hide();
      this.toast(error.message, true);
    }
  },

  async _quit() {
    if (!await this.confirm(I18N.t("app.quit.confirm"))) return;
    try {
      await API.quit();
      document.body.textContent = "";
      const message = document.createElement("p");
      message.className = "closed-note";
      message.textContent = I18N.t("app.closed");
      document.body.appendChild(message);
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  /* Recuperación de citas por código (FR-055): todas las citas de un nombre */
  showQuotes(codeName) {
    const dialog = document.getElementById("quotes-dialog");
    const body = document.getElementById("quotes-body");
    const instances = State.project.codes.filter(c => c.name === codeName);
    const docNames = {};
    for (const d of State.project.documents) docNames[d.id] = d.filename;
    document.getElementById("quotes-title").textContent =
      I18N.t("quotes.title.code", { name: codeName.toUpperCase(), n: instances.length });
    body.textContent = "";
    for (const code of instances) {
      const item = document.createElement("div");
      item.className = "quote-item";
      const head = document.createElement("div");
      head.className = "quote-meta";
      const chip = document.createElement("span");
      chip.className = "dom-chip";
      chip.style.backgroundColor = State.domains[code.domain] || "#999";
      const origin = code.doc_id ? docNames[code.doc_id] || "?" : I18N.t("origin.manual");
      head.append(chip, document.createTextNode(
        ` ${I18N.domain(code.domain)} · ${origin} · ${I18N.dateTime(code.created_at)}`
      ));
      item.appendChild(head);
      const quote = document.createElement("div");
      quote.className = "quote-text";
      quote.textContent = code.quote ? `“${code.quote}”` : I18N.t("quotes.manual");
      item.appendChild(quote);
      if (code.memo) {
        const memo = document.createElement("div");
        memo.className = "quote-meta";
        memo.textContent = `✎ ${code.memo}`;
        item.appendChild(memo);
      }
      if (code.doc_id) item.appendChild(this._goToCanvasButton(dialog, code));
      body.appendChild(item);
    }
    dialog.showModal();
  },

  _goToCanvasButton(dialog, target) {
    const go = document.createElement("button");
    go.className = "btn btn-small";
    go.textContent = I18N.t("go.canvas");
    go.addEventListener("click", () => {
      dialog.close();
      this.show("pentagrama");
      Canvas.goToQuote(target);
    });
    return go;
  },

  _manualLoaded: false,
  async _openManual() {
    const dialog = document.getElementById("manual-dialog");
    const body = document.getElementById("manual-body");
    if (!dialog.open) dialog.showModal();
    if (!this._manualLoaded) {
      body.textContent = I18N.t("dlg.loading");
      try {
        const { html } = await API._fetch("/api/manual");
        body.innerHTML = html;
        this._manualLoaded = true;
      } catch (error) {
        body.textContent = error.message;
      }
    }
  },

  async _openHistory() {
    const dialog = document.getElementById("history-dialog");
    const body = document.getElementById("history-body");
    dialog.showModal();
    body.textContent = I18N.t("dlg.loading");
    try {
      const { snapshots } = await API.getSnapshots();
      body.textContent = "";
      if (!snapshots.length) {
        const p = document.createElement("p");
        p.className = "empty-note";
        p.textContent = I18N.t("hist.empty");
        body.appendChild(p);
        return;
      }
      const list = document.createElement("ul");
      list.className = "plain-list";
      for (const snap of snapshots) {
        const li = document.createElement("li");
        const label = document.createElement("span");
        const date = I18N.dateTime(snap.saved_at.replace(" ", "T"));
        label.textContent = `${date} · ${snap.size_kb} KB`;
        const restore = document.createElement("button");
        restore.className = "icon-btn";
        restore.title = I18N.t("hist.restore.title");
        restore.textContent = "↺";
        restore.addEventListener("click", async () => {
          if (!await this.confirm(I18N.t("hist.restore.confirm", { date }))) return;
          try {
            await API.restoreSnapshot(snap.name);
            await State.reload();
            dialog.close();
            this.toast(I18N.t("hist.restored", { date }));
          } catch (error) {
            this.toast(error.message, true);
          }
        });
        li.append(label, restore);
        list.appendChild(li);
      }
      body.appendChild(list);
    } catch (error) {
      body.textContent = error.message;
    }
  },

  async _undoLastCode() {
    // Solo codificación del corpus: un código manual nacido en la biblioteca
    // (con pasajes de literatura) no se deshace con ⌘Z (FR-091)
    const litNames = new Set((State.project.lit_codings || []).map(c => c.name));
    const codes = State.project.codes.filter(c => !(c.doc_id === null && litNames.has(c.name)));
    if (!codes.length) { this.toast(I18N.t("undo.none"), true); return; }
    const last = codes.reduce((a, b) => (a.id > b.id ? a : b));
    try {
      await API.deleteCode(last.id);
      await State.reload();
      this.toast(I18N.t("undo.done", { name: last.name }));
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
    if (view !== "relaciones" && Relations.expanded) Relations.setExpanded(false);
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
    else if (this.current === "libro") Libro.render();
    else if (this.current === "literatura") Biblioteca.render();
    else if (this.current === "sentimiento") this.renderSentiment();
    else if (this.current === "acuerdo") Acuerdo.render();
  },

  /* Avance del análisis de corpus grandes (202 del backend). */
  _progress(elementId) {
    const el = document.getElementById(elementId);
    return {
      update: ({ done, total }) => {
        el.textContent = I18N.t("analysis.progress", { done, total });
        el.classList.remove("hidden");
      },
      hide: () => el.classList.add("hidden"),
    };
  },

  /* ---------- Sentimiento (FR-059) ---------- */

  _sentimentRun: 0,
  _sentData: null, // última respuesta: la usan el diálogo de palabras y los ajustes
  async renderSentiment() {
    const run = ++this._sentimentRun; // descarta respuestas de sondeos anteriores
    const progress = this._progress("sent-progress");
    const lang = this.corpusLang;
    this._syncCorpusLang();
    let data;
    try {
      data = await API.sentiment(lang, progress.update);
    } catch (error) {
      progress.hide();
      this.toast(error.message, true);
      return;
    }
    progress.hide();
    if (run !== this._sentimentRun) return;
    this._sentData = data;
    const empty = document.getElementById("sent-empty");
    const body = document.getElementById("sent-body");
    const language = I18N.t(`langname.${data.lang}`);
    document.getElementById("sent-title").textContent =
      I18N.t("sent.title.lang", { code: data.lang.toUpperCase() });
    const intro = document.getElementById("sent-intro");
    intro.textContent = I18N.t("sent.intro.lang", {
      n: (data.lexicon_size || 0).toLocaleString(I18N.locale), language });
    intro.classList.toggle("hidden", !!data.lexicon_missing);
    const mt = document.getElementById("sent-mt");
    mt.textContent = I18N.t("sent.mt", { language });
    mt.classList.toggle("hidden", data.lang === "en" || !!data.lexicon_missing);
    const panel = document.getElementById("lexicon-panel");
    panel.classList.toggle("hidden", !data.lexicon_missing);
    if (data.lexicon_missing) {
      document.getElementById("lexicon-title").textContent =
        I18N.t("lex.missing.title", { LANG: language.toUpperCase() });
      empty.classList.add("hidden");
      body.classList.add("hidden");
      return;
    }
    if (!data.documents.length) {
      empty.classList.remove("hidden");
      body.classList.add("hidden");
      return;
    }
    empty.classList.add("hidden");
    body.classList.remove("hidden");
    this._renderLexiconAdjustments(data);

    // Documentos: score + arco
    const docsBox = document.getElementById("sent-docs");
    docsBox.textContent = "";
    for (const doc of data.documents) {
      const card = document.createElement("div");
      card.className = "sent-doc-card";
      const head = document.createElement("div");
      head.className = "sent-doc-head";
      head.textContent = this.sentimentHead(doc);
      card.appendChild(head);
      const arcBox = document.createElement("div");
      Charts.line(arcBox, doc.arc);
      card.appendChild(arcBox);
      docsBox.appendChild(card);
    }

    // Dominios y códigos: barras divergentes con colores oficiales
    Charts.diverging(document.getElementById("sent-domains"), this.sentimentDomains(data));
    Charts.diverging(document.getElementById("sent-codes"),
      data.codes.map(c => ({ label: c.name, value: c.score,
        sublabel: I18N.t("sent.quotes", { n: c.n }), color: State.domains[c.domain] })));

    // Emociones (conteos, un solo tono) y palabras con carga — ambos clicables
    // hacia su trazabilidad (FR-071): qué menciones exactas produjeron el número.
    Charts.hbar(document.getElementById("sent-emotions"), this.sentimentEmotions(data),
      (d) => this.openEmotionWords(d.key));

    const rows = [];
    const maxLen = Math.max(data.words.positive.length, data.words.negative.length);
    for (let i = 0; i < maxLen; i++) {
      const p = data.words.positive[i], n = data.words.negative[i];
      rows.push([p ? `${p.word} (${p.count})` : "", n ? `${n.word} (${n.count})` : ""]);
    }
    Charts.table(document.getElementById("sent-words"), [I18N.t("sent.col.pos"), I18N.t("sent.col.neg")], rows);
    const wordsTable = document.querySelector("#sent-words table");
    if (wordsTable) {
      const posWords = data.words.positive, negWords = data.words.negative;
      [...wordsTable.tBodies[0].rows].forEach((row, i) => {
        [[0, posWords[i]], [1, negWords[i]]].forEach(([col, entry]) => {
          if (!entry) return;
          row.cells[col].classList.add("clickable-word");
          row.cells[col].title = I18N.t("sent.mentions");
          row.cells[col].addEventListener("click", () => this.openKwic(entry.word, "all"));
        });
      });
    }
  },

  /* Piezas del sentimiento compartidas con el reporte académico. */
  sentimentHead(doc) {
    const sign = I18N.t(doc.score > 0.05 ? "sent.positive" : doc.score < -0.05 ? "sent.negative" : "sent.neutral");
    return I18N.t("sent.doc.head", {
      file: doc.filename, score: `${doc.score > 0 ? "+" : ""}${doc.score}`, sign, n: doc.matched,
    });
  },
  sentimentDomains(data) {
    return data.domains.map(d => ({ label: I18N.domain(d.domain), value: d.score,
      sublabel: I18N.t("sent.quotes", { n: d.n }), color: State.domains[d.domain] }));
  },
  sentimentEmotions(data) {
    return data.emotions.map(e => ({ key: e.emotion, label: I18N.emotion(e.emotion),
      value: e.count, color: "#FF3300" }));
  },

  /* ---------- Ajustes del léxico (FR-086) ---------- */

  LEXICON_CATEGORIES: ["alegría", "confianza", "anticipación", "sorpresa",
    "miedo", "tristeza", "rabia", "asco", "positivo", "negativo"],

  lexCategoryLabel(cat) {
    if (cat === "positivo") return I18N.t("lexf.positive");
    if (cat === "negativo") return I18N.t("lexf.negative");
    return I18N.emotion(cat);
  },

  /* Palabras (ya ajustadas) de una emoción o polaridad. */
  _lexWords(data, cat) {
    if (cat === "positivo" || cat === "negativo") return (data.polarity_words || {})[cat] || [];
    return (data.emotion_words || {})[cat] || [];
  },

  _overrides(data) {
    const o = (data && data.overrides) || {};
    return { removed: o.removed || {}, added: o.added || {} };
  },

  /* Las diez categorías siempre visibles (aunque un ajuste deje una en cero,
     se puede volver a abrir y restaurar) y el resumen de todo lo ajustado. */
  _renderLexiconAdjustments(data) {
    const chips = document.getElementById("lexf-chips");
    chips.textContent = "";
    const { removed, added } = this._overrides(data);
    for (const cat of this.LEXICON_CATEGORIES) {
      const total = this._lexWords(data, cat).reduce((sum, w) => sum + w.count, 0);
      const adjusted = (removed[cat] || []).length + (added[cat] || []).length;
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "filter-chip" + (adjusted ? " lexf-adjusted" : "");
      const label = this.lexCategoryLabel(cat);
      chip.textContent = `${label.charAt(0).toLocaleUpperCase(I18N.locale)}${label.slice(1)} (${total})${adjusted ? ` ✎${adjusted}` : ""}`;
      chip.title = I18N.t("lexf.chip.title");
      chip.addEventListener("click", () => this.openEmotionWords(cat));
      chips.appendChild(chip);
    }

    const summary = document.getElementById("lexf-summary");
    summary.textContent = "";
    const cats = this.LEXICON_CATEGORIES.filter(c => (removed[c] || []).length || (added[c] || []).length);
    summary.classList.toggle("hidden", !cats.length);
    if (!cats.length) return;
    const head = document.createElement("div");
    head.className = "mini-label";
    const n = cats.reduce((sum, c) => sum + (removed[c] || []).length + (added[c] || []).length, 0);
    head.textContent = I18N.t("lexf.summary", { n });
    summary.appendChild(head);
    for (const cat of cats) {
      const row = document.createElement("div");
      row.className = "lexf-row";
      const label = document.createElement("strong");
      const text = this.lexCategoryLabel(cat);
      label.textContent = `${text.charAt(0).toLocaleUpperCase(I18N.locale)}${text.slice(1)}:`;
      row.appendChild(label);
      for (const word of removed[cat] || []) {
        row.appendChild(this._lexToken(`− ${word}`, I18N.t("lexf.restore.title", { word }),
          () => this._adjustLexicon(cat, word, "restore"), "lexf-removed"));
      }
      for (const word of added[cat] || []) {
        row.appendChild(this._lexToken(`+ ${word}`, I18N.t("lexf.unadd.title", { word }),
          () => this._adjustLexicon(cat, word, "unadd"), "lexf-added"));
      }
      summary.appendChild(row);
    }
    const reset = document.createElement("button");
    reset.className = "btn btn-small";
    reset.textContent = I18N.t("lexf.reset");
    reset.addEventListener("click", () => this._resetLexicon());
    summary.appendChild(reset);
  },

  _lexToken(text, title, onClick, cls) {
    const token = document.createElement("button");
    token.type = "button";
    token.className = `filter-chip ${cls}`;
    token.textContent = `${text} ✕`;
    token.title = title;
    token.addEventListener("click", onClick);
    return token;
  },

  /* Un cambio en el léxico: descartar, restaurar, sumar o quitar lo sumado.
     Se guarda y se recalcula todo (valencias, arcos, tono, emociones). */
  async _adjustLexicon(cat, word, action) {
    const data = this._sentData;
    if (!data) return;
    const { removed, added } = this._overrides(data);
    const next = {
      removed: Object.fromEntries(Object.entries(removed).map(([c, w]) => [c, [...w]])),
      added: Object.fromEntries(Object.entries(added).map(([c, w]) => [c, [...w]])),
    };
    const list = (group) => (next[group][cat] = next[group][cat] || []);
    const drop = (group) => { next[group][cat] = list(group).filter(w => w !== word); };
    if (action === "discard") { if (!list("removed").includes(word)) list("removed").push(word); }
    else if (action === "restore") drop("removed");
    else if (action === "add") { drop("removed"); if (!list("added").includes(word)) list("added").push(word); }
    else if (action === "unadd") drop("added");
    try {
      await API.setSentimentOverrides(data.lang, next.removed, next.added);
    } catch (error) {
      this.toast(error.message, true);
      return;
    }
    await this.renderSentiment();
    const fresh = this._sentData;
    if (action === "add" && fresh && !this._lexWords(fresh, cat).some(w => w.word === word)) {
      this.toast(I18N.t("lexf.add.none", { word }), true);
    } else {
      const key = { discard: "lexf.done.discard", restore: "lexf.done.restore",
        add: "lexf.done.add", unadd: "lexf.done.unadd" }[action];
      this.toast(I18N.t(key, { word, cat: this.lexCategoryLabel(cat) }));
    }
    if (document.getElementById("emotion-words-dialog").open && this._lexCat === cat) {
      this._drawEmotionWords(cat);
    }
  },

  async _resetLexicon() {
    const data = this._sentData;
    if (!data || !await this.confirm(I18N.t("lexf.reset.confirm"))) return;
    try {
      await API.setSentimentOverrides(data.lang, {}, {});
      await this.renderSentiment();
      this.toast(I18N.t("lexf.reset.done"));
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  /* Trazabilidad de una emoción (FR-071): qué palabras exactas la dispararon,
     cada una clicable hacia sus concordancias en el corpus. Desde v2.0 es
     también el lugar para ajustar el léxico (FR-086): descartar una palabra
     de la emoción, restaurarla o sumar otra. */
  _lexCat: null,
  openEmotionWords(cat) {
    this._lexCat = cat;
    this._drawEmotionWords(cat);
    const dialog = document.getElementById("emotion-words-dialog");
    if (!dialog.open) dialog.showModal();
  },

  _drawEmotionWords(cat) {
    const data = this._sentData || {};
    const body = document.getElementById("emotion-words-body");
    document.getElementById("emotion-words-title").textContent =
      I18N.t("sent.emo.title", { emotion: this.lexCategoryLabel(cat).toUpperCase() });
    body.textContent = "";
    const { removed, added } = this._overrides(data);
    const words = this._lexWords(data, cat);
    const addedHere = new Set(added[cat] || []);
    const note = document.createElement("p");
    note.className = "empty-note";
    note.style.paddingTop = "0";
    note.textContent = words.length ? I18N.t("lexf.dialog.hint") : I18N.t("sent.emo.empty");
    body.appendChild(note);

    const list = document.createElement("ul");
    list.className = "plain-list";
    const shown = new Set();
    const row = (word, count) => {
      const li = document.createElement("li");
      const label = document.createElement("span");
      label.className = count ? "clickable-word" : "muted";
      label.textContent = `${word} (${count})`;
      if (count) {
        label.title = I18N.t("sent.mentions");
        label.addEventListener("click", () => {
          document.getElementById("emotion-words-dialog").close();
          this.openKwic(word, "all");
        });
      }
      const side = document.createElement("span");
      side.className = "lexf-side";
      if (addedHere.has(word)) {
        const badge = document.createElement("span");
        badge.className = "lexf-badge";
        badge.textContent = I18N.t(count ? "lexf.badge.added" : "lexf.badge.added.none");
        side.appendChild(badge);
      }
      const action = document.createElement("button");
      action.className = "btn btn-small";
      const isAdded = addedHere.has(word);
      action.textContent = I18N.t(isAdded ? "lexf.unadd" : "lexf.discard");
      action.title = I18N.t(isAdded ? "lexf.unadd.title" : "lexf.discard.title", { word });
      action.addEventListener("click", () => this._adjustLexicon(cat, word, isAdded ? "unadd" : "discard"));
      side.appendChild(action);
      li.append(label, side);
      list.appendChild(li);
    };
    for (const w of words) { shown.add(w.word); row(w.word, w.count); }
    for (const word of addedHere) if (!shown.has(word)) row(word, 0);
    body.appendChild(list);

    const gone = removed[cat] || [];
    if (gone.length) {
      const title = document.createElement("div");
      title.className = "section-title";
      title.textContent = I18N.t("lexf.discarded", { n: gone.length });
      body.appendChild(title);
      const ul = document.createElement("ul");
      ul.className = "plain-list";
      for (const word of gone) {
        const li = document.createElement("li");
        const label = document.createElement("span");
        label.className = "lexf-struck";
        label.textContent = word;
        const restore = document.createElement("button");
        restore.className = "btn btn-small";
        restore.textContent = I18N.t("lexf.restore");
        restore.addEventListener("click", () => this._adjustLexicon(cat, word, "restore"));
        li.append(label, restore);
        ul.appendChild(li);
      }
      body.appendChild(ul);
    }
  },

  async _saveProject() {
    try {
      const { updated_at } = await API.saveProject();
      const time = updated_at.split("T")[1] || updated_at;
      this.toast(I18N.t("toast.saved", { time }));
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  // ---------- Importador ----------

  async _import(event) {
    const files = [...event.target.files];
    if (!files.length) return;
    const status = document.getElementById("import-status");
    let ok = 0;
    for (const [i, file] of files.entries()) {
      status.textContent = I18N.t("import.progress", { name: file.name, i: i + 1, n: files.length });
      try {
        await API.uploadDocument(file);
        ok++;
        if (files.length === 1) this.toast(I18N.t("import.done", { name: file.name }));
      } catch (error) {
        this.toast(`${file.name}: ${error.message}`, true);
      }
    }
    status.textContent = "";
    event.target.value = "";
    if (files.length > 1) this.toast(I18N.t("import.summary", { ok, n: files.length }), ok < files.length);
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
      this.toast(I18N.t("toast.active", { name: State.project.name }));
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  async _newProject() {
    const name = await this.ask(I18N.t("ask.new"));
    if (!name) return;
    try {
      await API.createProject(name);
      await State.reload();
      this.toast(I18N.t("toast.created", { name }));
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  async _renameProject() {
    const name = await this.ask(I18N.t("ask.rename"), State.project.name);
    if (!name || name === State.project.name) return;
    try {
      await API.renameProject(State.project.id, name);
      await State.reload();
      this.toast(I18N.t("toast.renamed"));
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  async _deleteProject() {
    const project = State.project;
    const ok = await this.confirm(I18N.t("confirm.delete.project", {
      name: project.name, docs: project.documents.length, codes: project.codes.length,
    }));
    if (!ok) return;
    try {
      await API.deleteProject(project.id);
      Canvas.activeDocId = null;
      await State.reload();
      this.toast(I18N.t("toast.deleted", { name: project.name }));
    } catch (error) {
      this.toast(error.message, true);
    }
  },

  async _importProject(event) {
    const file = event.target.files[0];
    event.target.value = "";
    if (!file) return;
    try {
      const project = await API.importProject(file);
      Canvas.activeDocId = null;
      await State.reload();
      const report = project.import_report;
      if (report) {
        let message = I18N.t("import.report", {
          name: project.name, sources: report.sources, selections: report.selections });
        if (report.skipped_sources) message += I18N.t("import.skipped", { n: report.skipped_sources });
        this.toast(message, report.skipped_sources > 0);
      } else {
        this.toast(I18N.t("toast.imported", { name: project.name }));
      }
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
      document.getElementById("cooc-section").classList.add("hidden");
      return;
    }
    empty.classList.add("hidden");
    charts.classList.remove("hidden");

    // Torta: distribución por dominios, en el orden fijo de la paleta
    const byDomain = {};
    for (const code of codes) byDomain[code.domain] = (byDomain[code.domain] || 0) + 1;
    const pieData = Object.keys(State.domains)
      .filter(domain => byDomain[domain])
      .map(domain => ({ label: I18N.domain(domain), value: byDomain[domain], color: State.domains[domain] }));
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
        return { label, sublabel: I18N.domain(domain), value, color: State.domains[domain] };
      })
      .sort((a, b) => b.value - a.value)
      .slice(0, 20);
    Charts.hbar(document.getElementById("chart-bars"), barData);

    this._renderCooccurrence(codes);
  },

  /* Co-ocurrencia (FR-043): dos códigos co-ocurren cuando sus citas se solapan
     en el mismo documento. Matrices código×código y documento×código.
     Barrido por documento ordenado por inicio: con miles de citas, comparar
     todos los pares era cuadrático. */
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
    const byDoc = new Map();
    for (const code of anchored) {
      if (!index.has(code.name)) continue;
      if (!byDoc.has(code.doc_id)) byDoc.set(code.doc_id, []);
      byDoc.get(code.doc_id).push(code);
    }
    for (const list of byDoc.values()) {
      list.sort((a, b) => a.start - b.start);
      for (let a = 0; a < list.length; a++) {
        const A = list[a];
        for (let b = a + 1; b < list.length && list[b].start < A.end; b++) {
          const B = list[b];
          if (A.name === B.name) continue;
          const i = index.get(A.name), j = index.get(B.name);
          matrix[i][j]++;
          matrix[j][i]++;
        }
      }
    }
    Charts.heatmap(document.getElementById("chart-cooc"), names, names, matrix);

    // Documento × código
    const docs = State.project.documents;
    const docMatrix = docs.map(doc => {
      const row = names.map(() => 0);
      for (const code of byDoc.get(doc.id) || []) row[index.get(code.name)]++;
      return row;
    });
    Charts.heatmap(
      document.getElementById("chart-doccode"),
      docs.map(d => d.filename), names, docMatrix
    );
  },

  // ---------- NLP (FR-017/018/034) ----------

  _nlpRun: 0,
  async renderNlp() {
    if (this.current !== "nlp") return;
    const run = ++this._nlpRun;
    const emptyNote = document.getElementById("nlp-empty");
    const hasCorpus = State.project.documents.length > 0;
    emptyNote.classList.toggle("hidden", hasCorpus);
    const lang = document.getElementById("nlp-lang").value;
    const minLen = document.getElementById("nlp-minlen").value;
    const progress = this._progress("nlp-progress");

    let words = [];
    if (hasCorpus) {
      try {
        const data = await API.nlp(lang, minLen, document.getElementById("nlp-pos").value, progress.update);
        if (run !== this._nlpRun) return; // hubo un cambio de filtro mientras tanto
        words = data.words;
        this._exclusions = data.exclusions || [];
        this._renderExclusionChips();
      } catch (error) {
        progress.hide();
        this.toast(error.message, true);
        return;
      }
    }
    progress.hide();
    // Tres visualizaciones simultáneas y coherentes (FR-018), todas clicables → KWIC
    WordCloud.render(document.getElementById("wordcloud"), words);
    Charts.hbar(
      document.getElementById("nlp-bars"),
      words.slice(0, 15).map(w => ({ label: w.word, value: w.count, color: "#FF3300" })),
      (d) => this.openKwic(d.label)
    );
    Charts.table(
      document.getElementById("nlp-table"),
      ["#", I18N.t("nlp.col.word"), I18N.t("nlp.col.freq")],
      words.map((w, i) => [i + 1, w.word, w.count])
    );
    const table = document.querySelector("#nlp-table table");
    if (table) {
      [...table.tBodies[0].rows].forEach((row, i) => {
        const cell = row.cells[1]; // columna "Palabra"
        cell.classList.add("clickable-word");
        cell.title = I18N.t("kwic.see");
        cell.addEventListener("click", () => this.openKwic(words[i].word));
      });
    }
  },

  /* Concordancias (KWIC): todas las ocurrencias de una palabra en contexto (FR-063).
     forcedPos: pásalo (p. ej. "all") cuando el origen no es la vista NLP —
     las palabras del léxico de sentimiento no están filtradas por categoría
     gramatical, así que buscarlas literalmente es lo correcto (FR-071). */
  async openKwic(word, forcedPos) {
    const dialog = document.getElementById("kwic-dialog");
    const body = document.getElementById("kwic-body");
    document.getElementById("kwic-title").textContent = I18N.t("kwic.title.word", { word: word.toUpperCase() });
    body.textContent = I18N.t("kwic.searching");
    dialog.showModal();
    try {
      const lang = document.getElementById("nlp-lang").value;
      const pos = forcedPos || document.getElementById("nlp-pos").value;
      const { count, occurrences } = await API.kwic(word, lang, pos,
        ({ done, total }) => { body.textContent = I18N.t("analysis.progress", { done, total }); });
      body.textContent = "";
      if (!count) {
        const p = document.createElement("p");
        p.className = "empty-note";
        p.textContent = I18N.t("kwic.none");
        body.appendChild(p);
        return;
      }
      const summary = document.createElement("p");
      summary.className = "empty-note";
      summary.style.paddingTop = "0";
      summary.textContent = I18N.t(count >= 300 ? "kwic.count.capped" : "kwic.count", { n: count });
      body.appendChild(summary);
      for (const occ of occurrences) {
        const line = document.createElement("div");
        line.className = "kwic-line";
        const text = document.createElement("div");
        text.className = "kwic-text";
        const mark = document.createElement("mark");
        mark.textContent = occ.match;
        text.append(`…${occ.before}`, mark, `${occ.after}…`);
        const meta = document.createElement("div");
        meta.className = "quote-meta";
        meta.textContent = occ.filename;
        line.append(text, meta,
          this._goToCanvasButton(dialog, { doc_id: occ.doc_id, start: occ.start, end: occ.end }));
        body.appendChild(line);
      }
    } catch (error) {
      body.textContent = error.message;
    }
  },

  _exclusions: [],
  _renderExclusionChips() {
    const box = document.getElementById("nlp-exclusion-chips");
    box.textContent = "";
    for (const word of this._exclusions) {
      const chip = document.createElement("button");
      chip.className = "filter-chip";
      chip.title = I18N.t("nlp.exclusions.remove", { word });
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
      ["exp.col.id", "exp.col.date", "exp.col.doc", "exp.col.domain", "exp.col.code",
       "exp.col.quote", "exp.col.memo"].map(key => I18N.t(key)),
      State.project.codes.map(code => [
        code.id,
        I18N.dateTime(code.created_at),
        code.doc_id ? (docNames[code.doc_id] || "?") : I18N.t("origin.manual"),
        I18N.domain(code.domain),
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
    results.textContent = I18N.t("lit.searching");
    try {
      const { results: works } = await API.literature(query);
      results.textContent = "";
      if (!works.length) {
        results.textContent = I18N.t("lit.none");
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
        meta.textContent = I18N.t("lit.meta", {
          year: work.year ?? "?", cites: (work.cited_by_count || 0).toLocaleString(I18N.locale),
        });
        card.append(title, meta);
        if (work.doi) {
          const link = document.createElement("a");
          link.href = work.doi;
          link.target = "_blank";
          link.rel = "noopener";
          link.textContent = I18N.t("lit.doi");
          card.appendChild(link);
          // Llevar la referencia a la biblioteca (FR-089)
          const add = document.createElement("button");
          add.className = "btn btn-small lit-add";
          add.textContent = I18N.t("lib.ref.add");
          add.addEventListener("click", () => Biblioteca.addReference(work.doi));
          card.appendChild(add);
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
        ok.onclick = cancel.onclick = dialog.oncancel = null;
        dialog.close();
        resolve(result);
      };
      ok.onclick = () => cleanup(true);
      cancel.onclick = () => cleanup(false);
      dialog.oncancel = (e) => { e.preventDefault(); cleanup(false); }; // Esc
      dialog.showModal();
    });
  },

  /* Pregunta de texto propia (reemplaza a prompt()): traducible, con el
     estilo de la app y sin bloquear el navegador. Devuelve el texto o null. */
  ask(message, value = "") {
    return new Promise(resolve => {
      const dialog = document.getElementById("ask-dialog");
      const form = document.getElementById("ask-form");
      const input = document.getElementById("ask-input");
      document.getElementById("ask-message").textContent = message;
      input.value = value;
      const finish = (result) => {
        form.onsubmit = dialog.oncancel = null;
        document.getElementById("ask-cancel").onclick = null;
        dialog.close();
        resolve(result);
      };
      form.onsubmit = (e) => { e.preventDefault(); finish(input.value.trim() || null); };
      document.getElementById("ask-cancel").onclick = () => finish(null);
      dialog.oncancel = (e) => { e.preventDefault(); finish(null); };
      dialog.showModal();
      input.focus();
      input.select();
    });
  },
};
