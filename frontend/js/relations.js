/* Vista Relaciones (FR-038/039): crear/eliminar relaciones entre códigos y
   visualizarlas como organizador (grafo circular SVG) y árbol de jerarquía.

   Las aristas se distinguen por TIPO con trazo + marcador + etiqueta, nunca
   solo por color (compensación de accesibilidad, dataviz). */

const Relations = {
  types: {}, // {tipo: verbo} — cargado del backend

  STROKES: {
    "jerarquía":     { dash: "",       width: 3, label: "J" },
    "asociación":    { dash: "6,5",    width: 2, label: "A" },
    "causalidad":    { dash: "",       width: 2, label: "C" },
    "contradicción": { dash: "2,4",    width: 3, label: "T" },
  },

  init() {
    document.getElementById("btn-rel-create").addEventListener("click", () => this._create());
  },

  /* Nombres únicos de código con el dominio de su instancia más reciente. */
  _uniqueCodes() {
    const map = new Map();
    for (const code of State.project.codes) map.set(code.name, code.domain);
    return map;
  },

  render() {
    const unique = this._uniqueCodes();
    const canBuild = unique.size >= 2;
    document.getElementById("rel-empty").classList.toggle("hidden", canBuild);
    document.getElementById("rel-builder").classList.toggle("hidden", !canBuild);
    document.getElementById("rel-body").classList.toggle("hidden", !canBuild && !State.project.relations.length);

    this._fillSelect("rel-source", [...unique.keys()]);
    this._fillSelect("rel-target", [...unique.keys()]);
    const typeSelect = document.getElementById("rel-type");
    const previous = typeSelect.value;
    typeSelect.textContent = "";
    for (const [type, verb] of Object.entries(this.types)) {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = `${type} (${verb})`;
      typeSelect.appendChild(option);
    }
    if (previous) typeSelect.value = previous;

    this._renderList();
    this._renderGraph(unique);
    this._renderTree(unique);
  },

  _fillSelect(id, names) {
    const select = document.getElementById(id);
    const previous = select.value;
    select.textContent = "";
    for (const name of names) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      select.appendChild(option);
    }
    if (names.includes(previous)) select.value = previous;
  },

  async _create() {
    const source = document.getElementById("rel-source").value;
    const target = document.getElementById("rel-target").value;
    const type = document.getElementById("rel-type").value;
    if (source === target) {
      Views.toast("Elige dos códigos distintos", true);
      return;
    }
    try {
      await API.createRelation({ source, target, type });
      await State.reload();
      Views.toast(`Relación creada: ${source} ${this.types[type]} ${target}`);
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  _renderList() {
    const list = document.getElementById("rel-list");
    list.textContent = "";
    const relations = State.project.relations;
    if (!relations.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = "Sin relaciones aún.";
      list.appendChild(p);
      return;
    }
    const ul = document.createElement("ul");
    ul.className = "plain-list";
    for (const relation of relations) {
      const li = document.createElement("li");
      const text = document.createElement("span");
      text.textContent = `${relation.source} —${this.types[relation.type] || relation.type}→ ${relation.target}`;
      const del = document.createElement("button");
      del.className = "icon-btn";
      del.title = "Eliminar relación";
      del.textContent = "🗑";
      del.addEventListener("click", async () => {
        try {
          await API.deleteRelation(relation.id);
          await State.reload();
          Views.toast("Relación eliminada");
        } catch (error) {
          Views.toast(error.message, true);
        }
      });
      li.append(text, del);
      ul.appendChild(li);
    }
    list.appendChild(ul);
  },

  /* Organizador: nodos en círculo, aristas con estilo por tipo + letra central. */
  _renderGraph(unique) {
    const container = document.getElementById("rel-graph");
    const legend = document.getElementById("rel-legend");
    container.textContent = "";
    legend.textContent = "";
    const relations = State.project.relations;
    if (!relations.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = "Crea relaciones para ver el organizador.";
      container.appendChild(p);
      return;
    }

    // Solo los códigos que participan en alguna relación
    const involved = [...new Set(relations.flatMap(r => [r.source, r.target]))];
    const size = 560, cx = size / 2, cy = size / 2;
    const radius = size / 2 - 90;
    const positions = new Map();
    involved.forEach((name, i) => {
      const angle = (i / involved.length) * Math.PI * 2 - Math.PI / 2;
      positions.set(name, { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) });
    });

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    svg.setAttribute("width", "100%");
    svg.style.cssText = "display:block;background:#FDFDF7;border:3px solid #000;";

    // Punta de flecha (dirección de la relación)
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.innerHTML = `<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
      markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#000"/></marker>`;
    svg.appendChild(defs);

    const el = (name, attrs) => {
      const node = document.createElementNS("http://www.w3.org/2000/svg", name);
      for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
      return node;
    };

    // Aristas (acortadas para no tapar los nodos)
    for (const relation of relations) {
      const a = positions.get(relation.source);
      const b = positions.get(relation.target);
      if (!a || !b) continue;
      const style = this.STROKES[relation.type] || this.STROKES["asociación"];
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.hypot(dx, dy) || 1;
      const trim = 26;
      const x1 = a.x + (dx / dist) * trim, y1 = a.y + (dy / dist) * trim;
      const x2 = b.x - (dx / dist) * trim, y2 = b.y - (dy / dist) * trim;

      const line = el("line", {
        x1, y1, x2, y2, stroke: "#000",
        "stroke-width": style.width,
        "marker-end": "url(#arrow)",
      });
      if (style.dash) line.setAttribute("stroke-dasharray", style.dash);
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${relation.source} ${this.types[relation.type]} ${relation.target}`;
      line.appendChild(title);
      svg.appendChild(line);

      // Letra del tipo sobre fondo blanco en el punto medio
      const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
      svg.appendChild(el("circle", { cx: mx, cy: my, r: 9, fill: "#fff", stroke: "#000", "stroke-width": 1.5 }));
      const tag = el("text", {
        x: mx, y: my + 3.5, "text-anchor": "middle",
        "font-size": 10, "font-weight": 700,
        "font-family": "IBM Plex Mono, monospace", fill: "#000",
      });
      tag.textContent = style.label;
      svg.appendChild(tag);
    }

    // Nodos (color de dominio + etiqueta en tinta)
    for (const name of involved) {
      const pos = positions.get(name);
      const domain = unique.get(name);
      svg.appendChild(el("circle", {
        cx: pos.x, cy: pos.y, r: 17,
        fill: State.domains[domain] || "#999", stroke: "#000", "stroke-width": 2.5,
      }));
      const label = el("text", {
        x: pos.x, y: pos.y + (pos.y < cy ? -26 : 36), "text-anchor": "middle",
        "font-size": 12, "font-weight": 700,
        "font-family": "IBM Plex Mono, monospace", fill: "#000",
      });
      label.textContent = name.length > 22 ? name.slice(0, 22) + "…" : name;
      svg.appendChild(label);
    }
    container.appendChild(svg);

    // Leyenda de tipos (letra + trazo + nombre)
    for (const [type, style] of Object.entries(this.STROKES)) {
      if (!this.types[type]) continue;
      const row = document.createElement("span");
      row.style.cssText = "display:inline-flex;align-items:center;gap:6px;font-size:11px;margin:6px 14px 0 0;font-weight:700;";
      row.textContent = `(${style.label}) ${type} — ${this.types[type]}`;
      legend.appendChild(row);
    }
  },

  /* Árbol: bosque construido desde las relaciones de jerarquía (contiene a). */
  _renderTree(unique) {
    const container = document.getElementById("rel-tree");
    container.textContent = "";
    const edges = State.project.relations.filter(r => r.type === "jerarquía");
    if (!edges.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = "Crea relaciones de jerarquía («contiene a») para armar el árbol.";
      container.appendChild(p);
      return;
    }
    const children = new Map();
    const targets = new Set();
    for (const edge of edges) {
      if (!children.has(edge.source)) children.set(edge.source, []);
      children.get(edge.source).push(edge.target);
      targets.add(edge.target);
    }
    let roots = [...children.keys()].filter(name => !targets.has(name));
    if (!roots.length) roots = [edges[0].source]; // ciclo puro: entrar por algún lado

    const buildNode = (name, visited) => {
      const li = document.createElement("li");
      li.className = "tree-node";
      const chip = document.createElement("span");
      chip.className = "dom-chip";
      chip.style.backgroundColor = State.domains[unique.get(name)] || "#999";
      const label = document.createElement("span");
      label.textContent = visited.has(name) ? `${name} ↺` : name;
      li.append(chip, label);
      if (!visited.has(name) && children.has(name)) {
        const next = new Set(visited).add(name);
        const ul = document.createElement("ul");
        ul.className = "tree-branch";
        for (const child of children.get(name)) ul.appendChild(buildNode(child, next));
        li.appendChild(ul);
      }
      return li;
    };

    const rootList = document.createElement("ul");
    rootList.className = "tree-branch tree-root";
    for (const root of roots) rootList.appendChild(buildNode(root, new Set()));
    container.appendChild(rootList);
  },
};
