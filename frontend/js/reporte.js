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
      s6: "6. Relaciones entre códigos", noRels: "Sin relaciones registradas.",
      tree: "Árbol de jerarquía",
      s7: "7. Análisis de sentimiento (léxico NRC, {language})", noDocs: "Sin documentos.",
      toneDomain: "Tono por categoría", emotions: "Emociones detectadas",
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
      s6: "6. Relationships between codes", noRels: "No relationships recorded.",
      tree: "Hierarchy tree",
      s7: "7. Sentiment analysis (NRC lexicon, {language})", noDocs: "No documents.",
      toneDomain: "Tone by category", emotions: "Emotions detected",
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
      s6: "6. Relações entre códigos", noRels: "Nenhuma relação registrada.",
      tree: "Árvore de hierarquia",
      s7: "7. Análise de sentimento (léxico NRC, {language})", noDocs: "Sem documentos.",
      toneDomain: "Tom por categoria", emotions: "Emoções detectadas",
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

      // Libro de códigos y citas agrupadas por dominio → código
      const byDomain = new Map();
      for (const code of project.codes) {
        if (!byDomain.has(code.domain)) byDomain.set(code.domain, new Map());
        const byName = byDomain.get(code.domain);
        if (!byName.has(code.name)) byName.set(code.name, []);
        byName.get(code.name).push(code);
      }
      let libro = "", citas = "";
      for (const domain of Object.keys(State.domains)) {
        const byName = byDomain.get(domain);
        if (!byName) continue;
        const chip = `<span class="chip" style="background:${State.domains[domain]}"></span>`;
        const label = this.esc(I18N.domain(domain));
        libro += `<h3>${chip} ${label}</h3><table><tr><th>${r("colCode")}</th><th>${r("colQuotes")}</th><th>${r("colMemos")}</th></tr>`;
        citas += `<h3>${chip} ${label}</h3>`;
        for (const [name, instances] of byName) {
          const memos = instances.map(c => c.memo).filter(Boolean);
          libro += `<tr><td><strong>${this.esc(name)}</strong></td><td>${instances.filter(c => c.quote).length}</td><td>${memos.map(m => this.esc(m)).join("<br>") || "—"}</td></tr>`;
          const quoted = instances.filter(c => c.quote);
          if (quoted.length) {
            citas += `<h4>${this.esc(name)} (${quoted.length})</h4>`;
            for (const c of quoted) {
              citas += `<blockquote>“${this.esc(c.quote)}”<footer>${this.esc(docNames[c.doc_id] || "?")} · ${this.esc(I18N.dateTime(c.created_at))}${c.memo ? ` · ✎ ${this.esc(c.memo)}` : ""}</footer></blockquote>`;
            }
          }
        }
        libro += "</table>";
      }

      // Relaciones: listado textual + organizador
      const relList = project.relations.map(rel =>
        `<li>${this.esc(rel.source)} <em>${this.esc(I18N.relVerb(rel.type))}</em> ${this.esc(rel.target)}</li>`).join("");

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
<p>${r("method", lexiconParams)}</p>

<h2>${r("s2")}</h2>
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
<div class="grafico">${frag("rel-graph")}</div>
${frag("rel-legend") ? `<p class="meta">${frag("rel-legend")}</p>` : ""}
<ul>${relList || `<li>${r("noRels")}</li>`}</ul>
<h3>${r("tree")}</h3>
${frag("rel-tree")}

<h2>${r("s7", lexiconParams)}</h2>
${arcsHtml || `<p>${r("noDocs")}</p>`}
<div class="dos-col">
  <div><h3>${r("toneDomain")}</h3><div class="grafico">${domainsHtml}</div></div>
  <div><h3>${r("emotions")}</h3><div class="grafico">${emotionsHtml}</div></div>
</div>

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
