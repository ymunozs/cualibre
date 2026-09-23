/* Acuerdo entre codificadores (FR-078): compara este proyecto (A) con otro
   (B) sobre los documentos compartidos. Kappa de Cohen, alfa de Krippendorff
   y porcentaje de acuerdo por código, con el carácter como unidad, y la lista
   de fragmentos en desacuerdo para discutirlos. Solo lectura: nada se
   escribe en el banco de códigos (Principio VIII). */

const Acuerdo = {
  result: null,

  init() {
    document.getElementById("btn-agr-run").addEventListener("click", () => this.run());
    document.getElementById("agr-other").addEventListener("change", () => {
      this.result = null;
      this._draw();
    });
  },

  render() {
    const select = document.getElementById("agr-other");
    const previous = select.value;
    const others = (State.projects || []).filter(p => p.id !== State.project.id);
    select.textContent = "";
    for (const project of others) {
      const option = document.createElement("option");
      option.value = project.id;
      option.textContent = `${project.name} (${project.code_count})`;
      select.appendChild(option);
    }
    if (others.some(p => p.id === previous)) select.value = previous;
    const none = !others.length;
    document.getElementById("agr-empty").classList.toggle("hidden", !none);
    document.getElementById("btn-agr-run").disabled = none;
    if (this.result && (this.result.project_a.id !== State.project.id
        || this.result.project_b.id !== select.value)) this.result = null;
    this._draw();
  },

  async run() {
    const other = document.getElementById("agr-other").value;
    if (!other) return;
    try {
      this.result = await API.agreement(other);
      this._draw();
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  _fmt(value, percent = false) {
    if (value === null || value === undefined) return "—";
    return percent
      ? `${(value * 100).toLocaleString(I18N.locale, { maximumFractionDigits: 1 })} %`
      : value.toLocaleString(I18N.locale, { minimumFractionDigits: 2, maximumFractionDigits: 3 });
  },

  _draw() {
    const box = document.getElementById("agr-result");
    const csv = document.getElementById("btn-agr-csv");
    const r = this.result;
    box.classList.toggle("hidden", !r);
    csv.classList.toggle("hidden", !r);
    if (!r) return;
    csv.dataset.download = `/api/agreement.csv?other=${encodeURIComponent(r.project_b.id)}`;
    I18N.apply(csv.parentElement);

    const shared = document.getElementById("agr-shared");
    const lines = [r.shared_documents.length
      ? I18N.t("agr.shared", { n: r.shared_documents.length, a: r.project_a.codes, b: r.project_b.codes })
      : I18N.t("agr.noshared")];
    if (r.only_in_a.length) lines.push(I18N.t("agr.onlyA", { list: r.only_in_a.join(", ") }));
    if (r.only_in_b.length) lines.push(I18N.t("agr.onlyB", { list: r.only_in_b.join(", ") }));
    shared.textContent = lines.join(" · ");

    const kpis = document.getElementById("agr-kpis");
    kpis.textContent = "";
    for (const [key, value, percent] of [
      ["agr.mean", r.mean_kappa], ["agr.pooled_kappa", r.pooled.kappa],
      ["agr.pooled_alpha", r.pooled.alpha], ["agr.pooled_agreement", r.pooled.agreement, true],
    ]) {
      const card = document.createElement("div");
      card.className = "agr-kpi";
      const number = document.createElement("b");
      number.textContent = this._fmt(value, percent);
      const label = document.createElement("span");
      label.textContent = I18N.t(key);
      card.append(number, label);
      kpis.appendChild(card);
    }

    Charts.table(
      document.getElementById("agr-table"),
      ["agr.col.code", "agr.col.a", "agr.col.b", "agr.col.pct", "agr.col.kappa",
       "agr.col.alpha", "agr.col.band"].map(k => I18N.t(k)),
      r.codes.map(c => [c.name, c.count_a, c.count_b, this._fmt(c.agreement, true),
        this._fmt(c.kappa), this._fmt(c.alpha), I18N.t(`band.${c.band}`)])
    );
    const table = document.querySelector("#agr-table table");
    if (!table) return;
    [...table.tBodies[0].rows].forEach((row, i) => {
      row.classList.add("clickable-row", `band-${r.codes[i].band}`);
      row.addEventListener("click", () => this.showDisagreements(r.codes[i]));
    });
  },

  /* Fragmentos en desacuerdo de un código, con salto al Canvas. */
  showDisagreements(code) {
    const dialog = document.getElementById("quotes-dialog");
    const body = document.getElementById("quotes-body");
    document.getElementById("quotes-title").textContent =
      I18N.t("agr.dis.title", { name: code.name.toUpperCase() });
    body.textContent = "";
    if (!code.disagreements.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = I18N.t("agr.dis.none");
      body.appendChild(p);
    }
    for (const d of code.disagreements) {
      const item = document.createElement("div");
      item.className = "quote-item";
      const head = document.createElement("div");
      head.className = "quote-meta";
      const who = d.who === "a" ? this.result.project_a.name : this.result.project_b.name;
      head.textContent = `${I18N.t(d.who === "a" ? "agr.who.a" : "agr.who.b", { name: who })} · ${d.filename}`;
      const quote = document.createElement("div");
      quote.className = "quote-text";
      quote.textContent = `“${d.quote}”`;
      item.append(head, quote);
      if (d.who === "b") {
        const note = document.createElement("div");
        note.className = "quote-meta";
        note.textContent = I18N.t("agr.who.b.note");
        item.appendChild(note);
      }
      item.appendChild(Views._goToCanvasButton(dialog, { doc_id: d.doc_id, start: d.start, end: d.end }));
      body.appendChild(item);
    }
    dialog.showModal();
  },
};
