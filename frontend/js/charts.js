/* Gráficos SVG propios, estilo brutalista, sin dependencias (research.md D3).

   Compensaciones de accesibilidad para la paleta fija (FR-016): todas las marcas
   llevan borde de tinta 2px (releva el bajo contraste de #FFCC00/#00CC66),
   las etiquetas van SIEMPRE en tinta (nunca en el color de la serie) y cada
   vista con gráfico ofrece los valores exactos en texto/tabla. */

const Charts = {
  _svg(width, height) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("width", "100%");
    svg.style.display = "block";
    return svg;
  },

  _el(name, attrs) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", name);
    for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
    return el;
  },

  /* Torta de distribución por dominios (FR-019). data: [{label, value, color}] */
  pie(container, data) {
    container.textContent = "";
    const total = data.reduce((sum, d) => sum + d.value, 0);
    if (!total) return;

    const size = 300, cx = size / 2, cy = size / 2, r = 118;
    const svg = this._svg(size, size);
    let angle = -Math.PI / 2;

    for (const d of data) {
      const sweep = (d.value / total) * Math.PI * 2;
      const x1 = cx + r * Math.cos(angle);
      const y1 = cy + r * Math.sin(angle);
      const x2 = cx + r * Math.cos(angle + sweep);
      const y2 = cy + r * Math.sin(angle + sweep);
      const large = sweep > Math.PI ? 1 : 0;
      const path = data.length === 1
        ? this._el("circle", { cx, cy, r, fill: d.color, stroke: "#000", "stroke-width": 2 })
        : this._el("path", {
            d: `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`,
            fill: d.color, stroke: "#000", "stroke-width": 2,
          });
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${d.label}: ${d.value} (${Math.round((d.value / total) * 100)}%)`;
      path.appendChild(title);
      svg.appendChild(path);
      angle += sweep;
    }
    container.appendChild(svg);

    // Leyenda con chips bordeados y valores exactos en tinta
    const legend = document.createElement("div");
    legend.style.marginTop = "10px";
    for (const d of data) {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:8px;font-size:12px;padding:2px 0;";
      const chip = document.createElement("span");
      chip.className = "dom-chip";
      chip.style.backgroundColor = d.color;
      const label = document.createElement("span");
      label.textContent = `${d.label} — ${d.value} (${Math.round((d.value / total) * 100)}%)`;
      row.append(chip, label);
      legend.appendChild(row);
    }
    container.appendChild(legend);
  },

  /* Barras horizontales. data: [{label, value, color, sublabel?}] */
  hbar(container, data) {
    container.textContent = "";
    if (!data.length) return;

    const rowH = 34, labelH = 15, width = 560;
    const height = data.length * rowH + 6;
    const max = Math.max(...data.map(d => d.value));
    const barArea = width - 60;
    const svg = this._svg(width, height);

    data.forEach((d, i) => {
      const y = i * rowH;
      // Etiqueta en tinta sobre la barra (identidad nunca solo por color)
      const label = this._el("text", {
        x: 0, y: y + labelH - 4, "font-size": 11,
        "font-family": "IBM Plex Mono, monospace", fill: "#000",
      });
      label.textContent = d.sublabel ? `${d.label} · ${d.sublabel}` : d.label;
      svg.appendChild(label);

      const barW = Math.max(3, (d.value / max) * barArea);
      const bar = this._el("rect", {
        x: 0, y: y + labelH, width: barW, height: rowH - labelH - 6,
        fill: d.color, stroke: "#000", "stroke-width": 2,
      });
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${d.label}: ${d.value}`;
      bar.appendChild(title);
      svg.appendChild(bar);

      const value = this._el("text", {
        x: barW + 8, y: y + labelH + (rowH - labelH - 6) / 2 + 4,
        "font-size": 12, "font-weight": "700",
        "font-family": "IBM Plex Mono, monospace", fill: "#000",
      });
      value.textContent = d.value;
      svg.appendChild(value);
    });

    container.appendChild(svg);
  },

  /* Tabla de datos genérica. headers: [..], rows: [[..], ...] */
  table(container, headers, rows) {
    container.textContent = "";
    const table = document.createElement("table");
    table.className = "data-table";
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    for (const h of headers) {
      const th = document.createElement("th");
      th.textContent = h;
      headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);
    const tbody = document.createElement("tbody");
    for (const row of rows) {
      const tr = document.createElement("tr");
      for (const cell of row) {
        const td = document.createElement("td");
        td.textContent = cell;
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    container.appendChild(table);
  },
};
