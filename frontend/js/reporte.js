/* Reporte académico exportable (FR-060): documento HTML autocontenido e
   imprimible a PDF con el proyecto completo — libro de códigos, citas
   agrupadas, memos, matrices, organizador, sentimiento y metodología.
   Se genera 100% en el cliente reutilizando los renders existentes, en el
   idioma de la interfaz. */

const Reporte = {
  TEXT: {
    es: {
      generating: "Generando reporte…",
      blocked: "El navegador bloqueó la ventana del reporte",
      done: "Reporte generado: {mod}P en la nueva pestaña para PDF",
      title: "Reporte",
      print: "{mod}P para guardar como PDF · {mod}S para guardar el HTML",
      meta: "Reporte de análisis cualitativo · {date} · Generado con CUA-LIBRE STUDIO",
      counts: "{docs} documento(s) · {codes} código(s) ({anchored} anclados, {manual} manuales) · {rels} relación(es)",
      s1: "1. Nota metodológica",
      method: "El análisis fue realizado con CUA-LIBRE STUDIO, herramienta local de análisis cualitativo (QDA). La codificación es íntegramente humana: toda entrada al banco de códigos requirió un gesto deliberado del investigador; el programa no sugiere ni automatiza interpretación. Los análisis automáticos de apoyo son auditables: las frecuencias léxicas y el foco gramatical usan spaCy (Honnibal &amp; Montani) con lematización; el análisis de sentimiento usa el NRC Word–Emotion Association Lexicon en {language} (Mohammad &amp; Turney, 2013, <em>Computational Intelligence</em>, 29(3), 436–465; {n} entradas, polaridad ±1 y ocho emociones) con inversión por negación en ventana de tres tokens; el arco emocional sigue la aproximación de trayectorias narrativas de Jockers (<em>syuzhet</em>). Los códigos se organizan en nueve categorías básicas fijas, más las categorías propias que haya definido el investigador.",
      s2: "2. Libro de códigos", colCode: "Código", colQuotes: "Citas", colMemos: "Memos",
      noCodes: "Sin códigos aún.",
      s3: "3. Citas por código", noQuotes: "Sin citas ancladas.",
      s4: "4. Distribución y densidad",
      s5: "5. Co-ocurrencia de códigos", coocNeed: "Se requieren 2+ códigos anclados.",
      byDoc: "Códigos por documento",
      s6: "6. Relaciones entre códigos y categorías", noRels: "Sin relaciones registradas.",
      tree: "Árbol de jerarquía",
      s7: "7. Análisis de sentimiento (léxico NRC, {language})", noDocs: "Sin documentos.",
      toneDomain: "Tono por categoría", emotions: "Emociones detectadas",
      book: "Cada código y categoría se describe con la estructura habitual de un libro de códigos (MacQueen et al., 1998, <em>CAM Journal</em>, 10(2), 31–36, https://doi.org/10.1177/1525822X980100020301): definición, cuándo usarlo, cuándo no y un ejemplo. Las descripciones son del investigador.",
      bookNone: "Sin descripción registrada.",
      bookOrphans: "Descripciones de códigos que ya no tienen citas",
      fDefinition: "Definición", fInclusion: "Cuándo usarlo", fExclusion: "Cuándo no usarlo", fExample: "Ejemplo",
      quotesN: "{n} cita(s)",
      boards: "Cuadros organizadores", boardsNote: "Cada cuadro es una vista del mismo conjunto de relaciones; los círculos son códigos y los cuadrados, categorías. Las posiciones y los colores son decisiones gráficas del investigador.",
      toneNote: "Sobre cada nodo: valencia media de sus citas (−1 a +1) y número de citas, con el léxico ajustado.",
      adjusted: "Para este corpus el investigador ajustó el léxico: {removed} palabra(s) descartada(s) y {added} sumada(s) en alguna emoción o polaridad (detalle en la sección 7). Las palabras sumadas se buscan por forma y por lema, con la misma regla de negación.",
      adjustments: "Ajustes del investigador al léxico", colCategory: "Emoción o polaridad", colRemoved: "Descartadas", colAdded: "Sumadas",
      positive: "positivas", negative: "negativas",
      footer: "Generado con CUA-LIBRE STUDIO · análisis 100% humano · {date}",
    },
    en: {
      generating: "Generating report…",
      blocked: "The browser blocked the report window",
      done: "Report generated: {mod}P in the new tab to save as PDF",
      title: "Report",
      print: "{mod}P to save as PDF · {mod}S to save the HTML",
      meta: "Qualitative analysis report · {date} · Generated with CUA-LIBRE STUDIO",
      counts: "{docs} document(s) · {codes} code(s) ({anchored} anchored, {manual} manual) · {rels} relationship(s)",
      s1: "1. Methodological note",
      method: "The analysis was carried out with CUA-LIBRE STUDIO, a local qualitative data analysis (QDA) tool. Coding is entirely human: every entry in the code bank required a deliberate action by the researcher; the software neither suggests nor automates interpretation. The supporting automatic analyses are auditable: lexical frequencies and grammatical focus use spaCy (Honnibal &amp; Montani) with lemmatisation; sentiment analysis uses the NRC Word–Emotion Association Lexicon in {language} (Mohammad &amp; Turney, 2013, <em>Computational Intelligence</em>, 29(3), 436–465; {n} entries, ±1 polarity and eight emotions) with negation reversal within a three-token window; the emotional arc follows Jockers’ narrative-trajectory approach (<em>syuzhet</em>). Codes are organised into nine fixed basic categories, plus any categories defined by the researcher.",
      s2: "2. Codebook", colCode: "Code", colQuotes: "Quotes", colMemos: "Memos",
      noCodes: "No codes yet.",
      s3: "3. Quotes by code", noQuotes: "No anchored quotes.",
      s4: "4. Distribution and density",
      s5: "5. Code co-occurrence", coocNeed: "At least 2 anchored codes are needed.",
      byDoc: "Codes by document",
      s6: "6. Relationships between codes and categories", noRels: "No relationships recorded.",
      tree: "Hierarchy tree",
      s7: "7. Sentiment analysis (NRC lexicon, {language})", noDocs: "No documents.",
      toneDomain: "Tone by category", emotions: "Emotions detected",
      book: "Each code and category is described with the usual codebook structure (MacQueen et al., 1998, <em>CAM Journal</em>, 10(2), 31–36, https://doi.org/10.1177/1525822X980100020301): definition, when to use it, when not to and an example. The descriptions are the researcher’s.",
      bookNone: "No description recorded.",
      bookOrphans: "Descriptions of codes that no longer have quotes",
      fDefinition: "Definition", fInclusion: "When to use it", fExclusion: "When not to use it", fExample: "Example",
      quotesN: "{n} quote(s)",
      boards: "Boards", boardsNote: "Each board is a view of the same set of relationships; circles are codes and squares are categories. Positions and colours are the researcher’s graphic choices.",
      toneNote: "On each node: mean valence of its quotes (−1 to +1) and number of quotes, with the adjusted lexicon.",
      adjusted: "For this corpus the researcher adjusted the lexicon: {removed} word(s) discarded and {added} added in some emotion or polarity (details in section 7). Added words are matched by form and by lemma, with the same negation rule.",
      adjustments: "Researcher’s adjustments to the lexicon", colCategory: "Emotion or polarity", colRemoved: "Discarded", colAdded: "Added",
      positive: "positive", negative: "negative",
      footer: "Generated with CUA-LIBRE STUDIO · 100% human analysis · {date}",
    },
    pt: {
      generating: "Gerando relatório…",
      blocked: "O navegador bloqueou a janela do relatório",
      done: "Relatório gerado: {mod}P na nova aba para salvar em PDF",
      title: "Relatório",
      print: "{mod}P para salvar como PDF · {mod}S para salvar o HTML",
      meta: "Relatório de análise qualitativa · {date} · Gerado com o CUA-LIBRE STUDIO",
      counts: "{docs} documento(s) · {codes} código(s) ({anchored} ancorados, {manual} manuais) · {rels} relação(ões)",
      s1: "1. Nota metodológica",
      method: "A análise foi realizada com o CUA-LIBRE STUDIO, ferramenta local de análise qualitativa de dados (QDA). A codificação é inteiramente humana: toda entrada no banco de códigos exigiu um gesto deliberado do pesquisador; o programa não sugere nem automatiza a interpretação. As análises automáticas de apoio são auditáveis: as frequências lexicais e o foco gramatical usam o spaCy (Honnibal &amp; Montani) com lematização; a análise de sentimento usa o NRC Word–Emotion Association Lexicon em {language} (Mohammad &amp; Turney, 2013, <em>Computational Intelligence</em>, 29(3), 436–465; {n} entradas, polaridade ±1 e oito emoções) com inversão por negação em janela de três tokens; o arco emocional segue a abordagem de trajetórias narrativas de Jockers (<em>syuzhet</em>). Os códigos se organizam em nove categorias básicas fixas, mais as categorias próprias definidas pelo pesquisador.",
      s2: "2. Livro de códigos", colCode: "Código", colQuotes: "Citações", colMemos: "Memos",
      noCodes: "Ainda não há códigos.",
      s3: "3. Citações por código", noQuotes: "Sem citações ancoradas.",
      s4: "4. Distribuição e densidade",
      s5: "5. Coocorrência de códigos", coocNeed: "São necessários 2 ou mais códigos ancorados.",
      byDoc: "Códigos por documento",
      s6: "6. Relações entre códigos e categorias", noRels: "Nenhuma relação registrada.",
      tree: "Árvore de hierarquia",
      s7: "7. Análise de sentimento (léxico NRC, {language})", noDocs: "Sem documentos.",
      toneDomain: "Tom por categoria", emotions: "Emoções detectadas",
      book: "Cada código e categoria é descrito com a estrutura habitual de um livro de códigos (MacQueen et al., 1998, <em>CAM Journal</em>, 10(2), 31–36, https://doi.org/10.1177/1525822X980100020301): definição, quando usar, quando não usar e um exemplo. As descrições são do pesquisador.",
      bookNone: "Sem descrição registrada.",
      bookOrphans: "Descrições de códigos que já não têm citações",
      fDefinition: "Definição", fInclusion: "Quando usar", fExclusion: "Quando não usar", fExample: "Exemplo",
      quotesN: "{n} citação(ões)",
      boards: "Quadros organizadores", boardsNote: "Cada quadro é uma vista do mesmo conjunto de relações; os círculos são códigos e os quadrados, categorias. Posições e cores são escolhas gráficas do pesquisador.",
      toneNote: "Sobre cada nó: valência média das suas citações (−1 a +1) e número de citações, com o léxico ajustado.",
      adjusted: "Para este corpus o pesquisador ajustou o léxico: {removed} palavra(s) descartada(s) e {added} somada(s) em alguma emoção ou polaridade (detalhe na seção 7). As palavras somadas são buscadas por forma e por lema, com a mesma regra de negação.",
      adjustments: "Ajustes do pesquisador ao léxico", colCategory: "Emoção ou polaridade", colRemoved: "Descartadas", colAdded: "Somadas",
      positive: "positivas", negative: "negativas",
      footer: "Gerado com o CUA-LIBRE STUDIO · análise 100% humana · {date}",
    },
  },

  r(key, params = {}) {
    const text = (this.TEXT[I18N.lang] || this.TEXT.es)[key] ?? this.TEXT.es[key];
    const values = { mod: I18N.mod, ...params };
    return text.replace(/\{(\w+)\}/g, (m, name) => (name in values ? values[name] : m));
  },

  esc(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
  },

  async generar() {
    // En el navegador: abrir la pestaña ANTES de los await (los bloqueadores de
    // ventanas exigen un gesto directo). En la ventana propia no hay pestañas:
    // el reporte se guarda y se abre en el navegador del sistema (FR-081).
    const win = Files.inWindow ? null : window.open("", "_blank");
    if (!Files.inWindow && !win) {
      Views.toast(this.r("blocked"), true);
      return;
    }
    if (win) win.document.write(`<p style='font-family:monospace;padding:2em'>${this.r("generating")}</p>`);

    try {
      await State.reload();
      const project = State.project;
      const docNames = {};
      for (const d of project.documents) docNames[d.id] = d.filename;

      // Rellenar los contenedores existentes (aunque estén ocultos) y capturarlos
      Views.renderAnalytics();
      Relations.render();
      const lexiconLang = Views.corpusLang;
      const raw = await API.sentiment(lexiconLang);
      // Sin léxico instalado para el idioma del corpus, la sección queda vacía
      const sentiment = raw.lexicon_missing
        ? { documents: [], domains: [], emotions: [], lexicon_size: 0 } : raw;
      const overrides = (raw && raw.overrides) || { removed: {}, added: {} };
      const lexiconParams = { language: I18N.t(`langname.${lexiconLang}`),
        n: (sentiment.lexicon_size || 0).toLocaleString(I18N.locale) };
      const r = (key, params) => this.r(key, params);

      const frag = (id) => document.getElementById(id).innerHTML;
      const detached = (renderFn) => {
        const box = document.createElement("div");
        renderFn(box);
        return box.innerHTML;
      };

      // Sentimiento: renders frescos en contenedores sueltos
      const arcsHtml = sentiment.documents.map(doc =>
        `<h4>${this.esc(Views.sentimentHead(doc))}</h4>` + detached(box => Charts.line(box, doc.arc))
      ).join("");
      const domainsHtml = detached(box => Charts.diverging(box, Views.sentimentDomains(sentiment)));
      const emotionsHtml = detached(box => Charts.hbar(box, Views.sentimentEmotions(sentiment)));

      // Libro de códigos (FR-084) y citas agrupadas por dominio → código
      const byDomain = new Map();
      for (const code of project.codes) {
        if (!byDomain.has(code.domain)) byDomain.set(code.domain, new Map());
        const byName = byDomain.get(code.domain);
        if (!byName.has(code.name)) byName.set(code.name, []);
        byName.get(code.name).push(code);
      }
      const codebook = project.codebook || {};
      const notes = project.category_notes || {};
      const entryHtml = (entry, fields) => {
        if (!entry) return "";
        const rows = fields.filter(f => (entry[f] || "").trim()).map(f =>
          `<dt>${r("f" + f[0].toUpperCase() + f.slice(1))}</dt><dd>${this.esc(entry[f].trim()).replace(/\n/g, "<br>")}</dd>`);
        return rows.length ? `<dl class="libro">${rows.join("")}</dl>` : "";
      };
      const allFields = ["definition", "inclusion", "exclusion", "example"];
      let libro = "", citas = "";
      const written = new Set(); // un código en dos categorías: su descripción una sola vez
      const domainKeys = [...Object.keys(State.domains), ...[...byDomain.keys()].filter(k => !(k in State.domains))];
      for (const domain of domainKeys) {
        const byName = byDomain.get(domain);
        if (!byName && !notes[domain]) continue;
        const chip = `<span class="chip" style="background:${State.domains[domain] || "#999"}"></span>`;
        const label = this.esc(I18N.domain(domain));
        libro += `<h3>${chip} ${label}</h3>${entryHtml(notes[domain], ["definition", "inclusion", "exclusion"])}`;
        if (!byName) continue;
        citas += `<h3>${chip} ${label}</h3>`;
        for (const [name, instances] of byName) {
          const memos = instances.map(c => c.memo).filter(Boolean);
          const quoted = instances.filter(c => c.quote);
          const description = written.has(name) ? "" : entryHtml(codebook[name], allFields);
          written.add(name);
          libro += `<div class="codigo"><h4>${this.esc(name)} <span class="meta">· ${r("quotesN", { n: quoted.length })}</span></h4>`
            + (description || `<p class="meta">${r("bookNone")}</p>`)
            + (memos.length ? `<p class="memos"><strong>${r("colMemos")}:</strong> ${memos.map(m => this.esc(m)).join(" · ")}</p>` : "")
            + "</div>";
          if (quoted.length) {
            citas += `<h4>${this.esc(name)} (${quoted.length})</h4>`;
            for (const c of quoted) {
              citas += `<blockquote>“${this.esc(c.quote)}”<footer>${this.esc(docNames[c.doc_id] || "?")} · ${this.esc(I18N.dateTime(c.created_at))}${c.memo ? ` · ✎ ${this.esc(c.memo)}` : ""}</footer></blockquote>`;
            }
          }
        }
      }
      const codeNames = new Set(project.codes.map(c => c.name));
      const orphans = Object.keys(codebook).filter(n => !codeNames.has(n));
      if (orphans.length) {
        libro += `<h3>${r("bookOrphans")}</h3>` + orphans.map(n =>
          `<div class="codigo"><h4>${this.esc(n)}</h4>${entryHtml(codebook[n], allFields)}</div>`).join("");
      }

      // Cuadros organizadores (FR-085): cada uno dibujado aparte, con su tono si lo muestra
      let tones = null;
      if (Relations.boards().some(b => b.show_tone)) {
        try { tones = await Relations.fetchTones(); } catch (_) { tones = null; }
      }
      const boardsHtml = Relations.boards()
        .filter(b => Relations.members(b).length)
        .map(b => {
          const withTone = !!(b.show_tone && tones && !tones.missing);
          const svg = detached(box => Relations.drawBoard(box, b, { interactive: false, tones: withTone ? tones : null }));
          return `<h3>${this.esc(Relations.boardName(b))}</h3><div class="grafico">${svg}</div>`
            + `<div class="meta leyenda">${Relations.legendHtml(withTone, b)}</div>`
            + (withTone ? `<p class="meta">${r("toneNote")}</p>` : "");
        }).join("");

      // Ajustes del léxico (FR-086): transparencia sobre lo que el investigador cambió
      const catLabel = (c) => c === "positivo" ? r("positive") : c === "negativo" ? r("negative") : I18N.emotion(c);
      const adjCats = [...new Set([...Object.keys(overrides.removed || {}), ...Object.keys(overrides.added || {})])];
      const count = (group) => Object.values(overrides[group] || {}).reduce((n, w) => n + w.length, 0);
      const adjustedNote = adjCats.length ? " " + r("adjusted", { removed: count("removed"), added: count("added") }) : "";
      const adjustmentsHtml = adjCats.length
        ? `<h3>${r("adjustments")}</h3><table><tr><th>${r("colCategory")}</th><th>${r("colRemoved")}</th><th>${r("colAdded")}</th></tr>`
          + adjCats.map(c => `<tr><td>${this.esc(catLabel(c))}</td><td>${this.esc(((overrides.removed || {})[c] || []).join(", ")) || "—"}</td><td>${this.esc(((overrides.added || {})[c] || []).join(", ")) || "—"}</td></tr>`).join("")
          + "</table>"
        : "";

      // Relaciones: listado textual + organizador
      const relList = project.relations.map(rel =>
        `<li>${this.esc(Relations.nodeLabel(rel.source_kind, rel.source))} <em>${this.esc(I18N.relVerb(rel.type))}</em> ${this.esc(Relations.nodeLabel(rel.target_kind, rel.target))}</li>`).join("");

      const today = new Date().toLocaleDateString(I18N.locale, { year: "numeric", month: "long", day: "numeric" });
      const anchored = project.codes.filter(c => c.doc_id).length;
      const manual = project.codes.length - anchored;

      const html = `<!DOCTYPE html>
<html lang="${I18N.locale}"><head><meta charset="utf-8">
<title>${r("title")}: ${this.esc(project.name)}</title>
<style>
  body { font-family: Georgia, "Times New Roman", serif; max-width: 820px; margin: 0 auto;
         padding: 40px 30px; color: #111; line-height: 1.55; }
  header { border-bottom: 4px solid #000; padding-bottom: 14px; margin-bottom: 24px; }
  h1 { font-size: 1.7rem; margin: 0; } h2 { font-size: 1.15rem; border-left: 5px solid #FF3300;
  padding-left: 10px; margin-top: 34px; page-break-after: avoid; }
  h3 { font-size: 1rem; margin-top: 20px; } h4 { font-size: 0.9rem; margin: 14px 0 4px; }
  .meta, footer.page { font-family: "Courier New", monospace; font-size: 0.75rem; color: #555; }
  table { border-collapse: collapse; width: 100%; font-size: 0.85rem; margin: 8px 0; }
  th, td { border: 1px solid #999; padding: 5px 8px; text-align: left; vertical-align: top; }
  th { background: #eee; }
  blockquote { margin: 10px 0 10px 14px; padding: 6px 12px; border-left: 3px solid #999;
               font-size: 0.92rem; page-break-inside: avoid; }
  blockquote footer { font-family: "Courier New", monospace; font-size: 0.7rem; color: #666; margin-top: 4px; }
  .chip { display: inline-block; width: 11px; height: 11px; border: 1px solid #000; }
  svg { max-width: 100%; height: auto; }
  .grafico { border: 1px solid #ccc; padding: 10px; margin: 8px 0; page-break-inside: avoid; }
  .dos-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  .codigo { margin: 8px 0 14px; padding-left: 12px; border-left: 2px solid #ccc; page-break-inside: avoid; }
  .codigo h4 { margin-top: 6px; } .codigo .meta { font-weight: normal; }
  dl.libro { margin: 4px 0; font-size: 0.9rem; }
  dl.libro dt { font-family: "Courier New", monospace; font-size: 0.72rem; font-weight: bold;
                text-transform: uppercase; letter-spacing: 0.05em; color: #444; margin-top: 6px; }
  dl.libro dd { margin: 2px 0 0 0; }
  .memos { font-size: 0.85rem; color: #333; }
  .rel-legend-item { margin-right: 14px; }
  .leyenda .rel-legend-row { display: flex; align-items: center; gap: 8px; margin: 3px 0; }
  .leyenda .rel-sample { flex-shrink: 0; }
  .leyenda .rel-legend-guide { color: #666; }
  @media print { .no-print { display: none; } body { padding: 0; } }
  .no-print { background: #000; color: #fff; padding: 10px 16px; font-family: monospace;
              font-size: 0.8rem; margin-bottom: 20px; }
</style></head><body>
<div class="no-print">${r("print")}</div>
<header>
  <h1>${this.esc(project.name)}</h1>
  <p class="meta">${r("meta", { date: today })}<br>
  ${r("counts", { docs: project.documents.length, codes: project.codes.length, anchored, manual, rels: project.relations.length })}</p>
</header>

<h2>${r("s1")}</h2>
<p>${r("method", lexiconParams)}${adjustedNote}</p>

<h2>${r("s2")}</h2>
<p>${r("book")}</p>
${libro || `<p>${r("noCodes")}</p>`}

<h2>${r("s3")}</h2>
${citas || `<p>${r("noQuotes")}</p>`}

<h2>${r("s4")}</h2>
<div class="dos-col">
  <div class="grafico">${frag("chart-pie")}</div>
  <div class="grafico">${frag("chart-bars")}</div>
</div>

<h2>${r("s5")}</h2>
<div class="grafico">${frag("chart-cooc") || `<p>${r("coocNeed")}</p>`}</div>
<h3>${r("byDoc")}</h3>
<div class="grafico">${frag("chart-doccode")}</div>

<h2>${r("s6")}</h2>
${boardsHtml ? `<p class="meta">${r("boardsNote")}</p>${boardsHtml}` : ""}
<ul>${relList || `<li>${r("noRels")}</li>`}</ul>
<h3>${r("tree")}</h3>
${frag("rel-tree")}

<h2>${r("s7", lexiconParams)}</h2>
${arcsHtml || `<p>${r("noDocs")}</p>`}
<div class="dos-col">
  <div><h3>${r("toneDomain")}</h3><div class="grafico">${domainsHtml}</div></div>
  <div><h3>${r("emotions")}</h3><div class="grafico">${emotionsHtml}</div></div>
</div>
${adjustmentsHtml}

<footer class="page"><hr>${r("footer", { date: today })}</footer>
</body></html>`;

      if (!win) {
        const { path } = await API.openReport(`${this.r("title")} ${project.name}`, html);
        Views.toast(I18N.t("report.opened", { path }));
        return;
      }
      win.document.open();
      win.document.write(html);
      win.document.close();
      Views.toast(this.r("done"));
    } catch (error) {
      if (win) win.close();
      Views.toast(error.message, true);
    }
  },
};
