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

  /* Barras horizontales. data: [{label, value, color, sublabel?}]
     onClick(datum) opcional: hace la fila clicable (usado por KWIC, FR-063). */
  hbar(container, data, onClick) {
    container.textContent = "";
    if (!data.length) return;

    const rowH = 34, labelH = 15, width = 560;
    const height = data.length * rowH + 6;
    const max = Math.max(...data.map(d => d.value));
    const barArea = width - 60;
    const svg = this._svg(width, height);

    data.forEach((d, i) => {
      const y = i * rowH;
      const row = document.createElementNS("http://www.w3.org/2000/svg", "g");
      if (onClick) {
        row.style.cursor = "pointer";
        row.addEventListener("click", () => onClick(d));
      }

      // Etiqueta en tinta sobre la barra (identidad nunca solo por color)
      const label = this._el("text", {
        x: 0, y: y + labelH - 4, "font-size": 11,
        "font-family": "IBM Plex Mono, monospace", fill: "currentColor",
      });
      label.textContent = d.sublabel ? `${d.label} · ${d.sublabel}` : d.label;
      row.appendChild(label);

      const barW = Math.max(3, (d.value / max) * barArea);
      const bar = this._el("rect", {
        x: 0, y: y + labelH, width: barW, height: rowH - labelH - 6,
        fill: d.color, stroke: "#000", "stroke-width": 2,
      });
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = onClick ? `${d.label}: ${d.value} (clic para ver concordancias)` : `${d.label}: ${d.value}`;
      bar.appendChild(title);
      row.appendChild(bar);

      const value = this._el("text", {
        x: barW + 8, y: y + labelH + (rowH - labelH - 6) / 2 + 4,
        "font-size": 12, "font-weight": "700",
        "font-family": "IBM Plex Mono, monospace", fill: "currentColor",
      });
      value.textContent = d.value;
      row.appendChild(value);

      svg.appendChild(row);
    });

    container.appendChild(svg);
  },

  /* Heatmap secuencial (un solo tono: canvas → acento) con valores en tinta.
     rows/cols: etiquetas; values: matriz [fila][col]. */
  heatmap(container, rows, cols, values) {
    container.textContent = "";
    const max = Math.max(1, ...values.flat());
    const table = document.createElement("table");
    table.className = "data-table heatmap";

    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    headRow.appendChild(document.createElement("th"));
    for (const col of cols) {
      const th = document.createElement("th");
      th.textContent = col;
      th.title = col;
      headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    rows.forEach((rowLabel, i) => {
      const tr = document.createElement("tr");
      const th = document.createElement("th");
      th.textContent = rowLabel;
      th.title = rowLabel;
      tr.appendChild(th);
      cols.forEach((colLabel, j) => {
        const td = document.createElement("td");
        const value = values[i][j];
        td.textContent = value || "";
        td.title = `${rowLabel} × ${colLabel}: ${value}`;
        if (value) {
          const t = value / max; // rampa #FDFDF7 → #FF3300
          const mix = (a, b) => Math.round(a + (b - a) * t);
          td.style.backgroundColor = `rgb(${mix(253, 255)}, ${mix(253, 51)}, ${mix(247, 0)})`;
          td.style.color = t > 0.55 ? "#fff" : "#000";
          td.style.fontWeight = "700";
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    container.appendChild(table);
  },

  /* Arco emocional (FR-059): línea de valencia -1..1 con eje cero. */
  line(container, points) {
    container.textContent = "";
    if (points.length < 2) {
      const p = document.createElement("span");
      p.className = "empty-note";
      p.textContent = "Se necesitan 2+ párrafos para trazar el arco.";
      container.appendChild(p);
      return;
    }
    const width = 560, height = 110, pad = 8;
    const svg = this._svg(width, height);
    const x = (i) => pad + (i / (points.length - 1)) * (width - 2 * pad);
    const y = (s) => height / 2 - s * (height / 2 - pad);
    svg.appendChild(this._el("line", {
      x1: pad, y1: height / 2, x2: width - pad, y2: height / 2,
      stroke: "currentColor", "stroke-width": 1, "stroke-dasharray": "3,4", opacity: 0.5,
    }));
    const path = points.map((p, i) => `${i ? "L" : "M"} ${x(i).toFixed(1)} ${y(p.score).toFixed(1)}`).join(" ");
    svg.appendChild(this._el("path", {
      d: path, fill: "none", stroke: "#FF3300", "stroke-width": 3,
      "stroke-linejoin": "round", "stroke-linecap": "round",
    }));
    points.forEach((p, i) => {
      const dot = this._el("circle", {
        cx: x(i), cy: y(p.score), r: 3.5,
        fill: p.score >= 0 ? "#00CC66" : "#CC0000", stroke: "#000", "stroke-width": 1.5,
      });
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `Tramo ${i + 1}: ${p.score > 0 ? "+" : ""}${p.score} (${p.matched} palabras con carga)`;
      dot.appendChild(title);
      svg.appendChild(dot);
    });
    container.appendChild(svg);
  },

  /* Barras divergentes (FR-059): valencia -1..1 desde un eje central. */
  diverging(container, data) {
    container.textContent = "";
    if (!data.length) return;
    const rowH = 30, width = 560, center = width / 2, span = width / 2 - 70;
    const height = data.length * rowH + 4;
    const svg = this._svg(width, height);
    svg.appendChild(this._el("line", {
      x1: center, y1: 0, x2: center, y2: height,
      stroke: "currentColor", "stroke-width": 1, opacity: 0.5,
    }));
    data.forEach((d, i) => {
      const yPos = i * rowH + 5;
      const barW = Math.abs(d.value) * span;
      const bar = this._el("rect", {
        x: d.value >= 0 ? center : center - barW, y: yPos,
        width: Math.max(2, barW), height: rowH - 11,
        fill: d.color, stroke: "#000", "stroke-width": 2,
      });
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${d.label}: ${d.value > 0 ? "+" : ""}${d.value}${d.sublabel ? ` (${d.sublabel})` : ""}`;
      bar.appendChild(title);
      svg.appendChild(bar);
      const label = this._el("text", {
        x: d.value >= 0 ? center - 8 : center + 8, y: yPos + rowH - 17,
        "text-anchor": d.value >= 0 ? "end" : "start",
        "font-size": 11, "font-family": "IBM Plex Mono, monospace", fill: "currentColor",
      });
      label.textContent = `${d.label} ${d.value > 0 ? "+" : ""}${d.value}`;
      svg.appendChild(label);
    });
    container.appendChild(svg);
  },

  /* ---- Exportación de organizadores gráficos (FR-049) ---- */

  _download(blob, filename) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  },

  downloadSvg(svgEl, filename) {
    const clone = svgEl.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const source = new XMLSerializer().serializeToString(clone);
    this._download(new Blob([source], { type: "image/svg+xml;charset=utf-8" }), filename);
  },

  downloadSvgAsPng(svgEl, filename, scale = 2) {
    const clone = svgEl.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const vb = svgEl.viewBox.baseVal;
    const width = (vb && vb.width) || svgEl.clientWidth || 800;
    const height = (vb && vb.height) || svgEl.clientHeight || 600;
    const source = new XMLSerializer().serializeToString(clone);
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = width * scale;
      canvas.height = height * scale;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#FDFDF7";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(blob => this._download(blob, filename), "image/png");
    };
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
  },

  downloadCanvas(canvasEl, filename) {
    canvasEl.toBlob(blob => this._download(blob, filename), "image/png");
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
