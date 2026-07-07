/* Reporte académico exportable (FR-060): documento HTML autocontenido e
   imprimible a PDF con el proyecto completo — libro de códigos, citas
   agrupadas, memos, matrices, organizador, sentimiento y metodología.
   Se genera 100% en el cliente reutilizando los renders existentes. */

const Reporte = {
  esc(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
  },

  async generar() {
    // Abrir la ventana ANTES de los await (los popup blockers exigen gesto directo)
    const win = window.open("", "_blank");
    if (!win) {
      Views.toast("El navegador bloqueó la ventana del reporte", true);
      return;
    }
    win.document.write("<p style='font-family:monospace;padding:2em'>Generando reporte…</p>");

    try {
      await State.reload();
      const project = State.project;
      const docNames = {};
      for (const d of project.documents) docNames[d.id] = d.filename;

      // Rellenar los contenedores existentes (aunque estén ocultos) y capturarlos
      Views.renderAnalytics();
      Relations.render();
      const sentiment = await API.sentiment();

      const frag = (id) => document.getElementById(id).innerHTML;
      const detached = (renderFn) => {
        const box = document.createElement("div");
        renderFn(box);
        return box.innerHTML;
      };

      // Sentimiento: renders frescos en contenedores sueltos
      const arcsHtml = sentiment.documents.map(doc => {
        const sign = doc.score > 0.05 ? "positivo" : doc.score < -0.05 ? "negativo" : "neutro";
        return `<h4>${this.esc(doc.filename)} — valencia ${doc.score > 0 ? "+" : ""}${doc.score} (${sign}; ${doc.matched} palabras con carga)</h4>`
          + detached(box => Charts.line(box, doc.arc));
      }).join("");
      const domainsHtml = detached(box => Charts.diverging(box,
        sentiment.domains.map(d => ({ label: d.domain, value: d.score, sublabel: `${d.n} citas`, color: State.domains[d.domain] }))));
      const emotionsHtml = detached(box => Charts.hbar(box,
        sentiment.emotions.map(e => ({ label: e.emotion, value: e.count, color: "#FF3300" }))));

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
        libro += `<h3>${chip} ${this.esc(domain)}</h3><table><tr><th>Código</th><th>Citas</th><th>Memos</th></tr>`;
        citas += `<h3>${chip} ${this.esc(domain)}</h3>`;
        for (const [name, instances] of byName) {
          const memos = instances.map(c => c.memo).filter(Boolean);
          libro += `<tr><td><strong>${this.esc(name)}</strong></td><td>${instances.filter(c => c.quote).length}</td><td>${memos.map(m => this.esc(m)).join("<br>") || "—"}</td></tr>`;
          const quoted = instances.filter(c => c.quote);
          if (quoted.length) {
            citas += `<h4>${this.esc(name)} (${quoted.length})</h4>`;
            for (const c of quoted) {
              citas += `<blockquote>“${this.esc(c.quote)}”<footer>${this.esc(docNames[c.doc_id] || "?")} · ${this.esc(c.created_at.replace("T", " "))}${c.memo ? ` · ✎ ${this.esc(c.memo)}` : ""}</footer></blockquote>`;
            }
          }
        }
        libro += "</table>";
      }

      // Relaciones: listado textual + organizador
      const relList = project.relations.map(r =>
        `<li>${this.esc(r.source)} <em>${this.esc(Relations.types[r.type] || r.type)}</em> ${this.esc(r.target)}</li>`).join("");

      const today = new Date().toLocaleDateString("es-CL", { year: "numeric", month: "long", day: "numeric" });
      const anchored = project.codes.filter(c => c.doc_id).length;
      const manual = project.codes.length - anchored;

      const html = `<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Reporte — ${this.esc(project.name)}</title>
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
<div class="no-print">⌘P / Ctrl+P para guardar como PDF · ⌘S para guardar el HTML</div>
<header>
  <h1>${this.esc(project.name)}</h1>
  <p class="meta">Reporte de análisis cualitativo · ${today} · Generado con CUA-LIBRE STUDIO<br>
  ${project.documents.length} documento(s) · ${project.codes.length} código(s) (${anchored} anclados, ${manual} manuales) · ${project.relations.length} relación(es)</p>
</header>

<h2>1. Nota metodológica</h2>
<p>El análisis fue realizado con CUA-LIBRE STUDIO, herramienta local de análisis cualitativo
(QDA). La codificación es íntegramente humana: toda entrada al banco de códigos requirió un
gesto deliberado del investigador; el programa no sugiere ni automatiza interpretación.
Los análisis automáticos de apoyo son
auditables: las frecuencias léxicas y el foco gramatical usan spaCy (Honnibal &amp; Montani)
con lematización; el análisis de sentimiento usa el NRC Word–Emotion Association Lexicon en
castellano (Mohammad &amp; Turney, 2013, <em>Computational Intelligence</em>, 29(3), 436–465;
5.094 entradas, polaridad ±1 y ocho emociones) con inversión por negación en ventana de tres
tokens; el arco emocional sigue la aproximación de trayectorias narrativas de Jockers
(<em>syuzhet</em>). Los dominios de codificación son nueve categorías fijas definidas por el
investigador.</p>

<h2>2. Libro de códigos</h2>
${libro || "<p>Sin códigos aún.</p>"}

<h2>3. Citas por código</h2>
${citas || "<p>Sin citas ancladas.</p>"}

<h2>4. Distribución y densidad</h2>
<div class="dos-col">
  <div class="grafico">${frag("chart-pie")}</div>
  <div class="grafico">${frag("chart-bars")}</div>
</div>

<h2>5. Co-ocurrencia de códigos</h2>
<div class="grafico">${frag("chart-cooc") || "<p>Se requieren 2+ códigos anclados.</p>"}</div>
<h3>Códigos por documento</h3>
<div class="grafico">${frag("chart-doccode")}</div>

<h2>6. Relaciones entre códigos</h2>
<div class="grafico">${frag("rel-graph")}</div>
${frag("rel-legend") ? `<p class="meta">${frag("rel-legend")}</p>` : ""}
<ul>${relList || "<li>Sin relaciones registradas.</li>"}</ul>
<h3>Árbol de jerarquía</h3>
${frag("rel-tree")}

<h2>7. Análisis de sentimiento (léxico NRC-es)</h2>
${arcsHtml || "<p>Sin documentos.</p>"}
<div class="dos-col">
  <div><h3>Tono por dominio</h3><div class="grafico">${domainsHtml}</div></div>
  <div><h3>Emociones detectadas</h3><div class="grafico">${emotionsHtml}</div></div>
</div>

<footer class="page"><hr>Generado con CUA-LIBRE STUDIO — análisis 100% humano · ${today}</footer>
</body></html>`;

      win.document.open();
      win.document.write(html);
      win.document.close();
      Views.toast("Reporte generado — ⌘P en la nueva pestaña para PDF");
    } catch (error) {
      win.close();
      Views.toast(error.message, true);
    }
  },
};
