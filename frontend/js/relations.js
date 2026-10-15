/* Vista Relaciones (FR-038/039, FR-085): crear/eliminar relaciones entre
   códigos y categorías y verlas como organizador (grafo SVG) y árbol de
   jerarquía.

   Cuadros organizadores: el cuadro general muestra siempre todas las
   relaciones (el organizador de siempre); el investigador puede crear otros
   cuadros con solo los nodos que elija. En cada cuadro los nodos se arrastran
   y se recolorean; eso es solo vista: las relaciones y los colores de las
   categorías no cambian.

   Las aristas se distinguen por TIPO con trazo + marcador + letra, nunca solo
   por color (compensación de accesibilidad, dataviz): el color de una
   relación es un añadido del investigador.

   Simbología nativa de Cua-libre (FR-087): códigos en círculo, categorías en
   cuadrado con borde grueso y nombre en mayúsculas. Es la forma por defecto;
   el investigador puede elegir otra por nodo (rombo, hexágono, caja con el
   nombre adentro…) y «Nativa» la restaura. También puede seleccionar varios
   nodos, moverlos juntos, deshacer movimientos y bloquear nodos o el cuadro. */

const SVG_NS = "http://www.w3.org/2000/svg";

const Relations = {
  types: {}, // {tipo: verbo} — cargado del backend
  W: 900,
  H: 620,
  selection: null, // {type: "nodes", keys: Set} | {type: "edge", id}
  _tones: null, // tono emocional por nodo (FR-086), o {missing: true}
  _toneRun: 0,
  _undo: {}, // "proyecto:cuadro" -> pilas de posiciones previas (FR-087)
  expanded: false,

  // Trazo por tipo (FR-087): cada tipo se reconoce sin color. La jerarquía
  // lleva un rombo en el origen (A contiene a B, no es un flujo); la
  // contradicción, una marca de choque al centro. La letra depende del idioma.
  STROKES: {
    "jerarquía":     { dash: "",    width: 4,   start: "diamond", end: null },
    "asociación":    { dash: "8,6", width: 2,   start: null, end: "arrow" },
    "causalidad":    { dash: "",    width: 2.5, start: null, end: "arrow" },
    "contradicción": { dash: "2,5", width: 3,   start: null, end: "arrow", tick: true },
  },

  SHAPES: ["circle", "square", "diamond", "hexagon", "box"],
  SHAPE_SYMBOLS: { circle: "●", square: "■", diamond: "◆", hexagon: "⬢", box: "▭" },

  init() {
    document.getElementById("btn-rel-create").addEventListener("click", () => this._create());
    document.getElementById("board-select").addEventListener("change", (e) => {
      this._setActiveBoard(Number(e.target.value));
      this.selection = null;
      this.render();
    });
    document.getElementById("btn-board-new").addEventListener("click", () => this._newBoard());
    document.getElementById("btn-board-rename").addEventListener("click", () => this._renameBoard());
    document.getElementById("btn-board-delete").addEventListener("click", () => this._deleteBoard());
    document.getElementById("btn-board-add").addEventListener("click", () => this._addNode());
    document.getElementById("btn-board-layout").addEventListener("click", () => this._resetLayout());
    document.getElementById("board-tone").addEventListener("change", (e) => this._toggleTone(e.target.checked));
    document.getElementById("btn-board-undo").addEventListener("click", () => this._undoMove());
    document.getElementById("btn-board-bring").addEventListener("click", () => this._bringRelation());
    document.getElementById("btn-board-lock").addEventListener("click", () => this._toggleBoardLock());
    document.getElementById("btn-rel-expand").addEventListener("click", () => this.setExpanded(!this.expanded));
    document.getElementById("rel-type").addEventListener("change", () => this._renderGuide());
    // Esc sale de la vista ampliada, salvo que haya un diálogo abierto encima
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && this.expanded && !document.querySelector("dialog[open]")) {
        this.setExpanded(false);
      }
    });
  },

  /* Vista ampliada del organizador, casi a pantalla completa (FR-087). */
  setExpanded(on) {
    this.expanded = on;
    const organizer = document.getElementById("rel-organizer");
    const builder = document.getElementById("rel-builder");
    const guide = document.getElementById("rel-guide");
    // Ampliado: crear relaciones sin salir; normal: el creador en su fila de siempre
    if (on) organizer.prepend(builder, guide);
    else document.getElementById("rel-builder-home").append(builder, guide);
    organizer.classList.toggle("rel-expanded", on);
    document.body.classList.toggle("rel-expanded-open", on);
    const button = document.getElementById("btn-rel-expand");
    button.textContent = I18N.t(on ? "board.collapse" : "board.expand");
  },

  _renderGuide() {
    const type = document.getElementById("rel-type").value;
    document.getElementById("rel-guide").textContent = type ? I18N.t(`rel.guide.${type}`) : "";
  },

  /* ---------- Nodos: códigos y categorías ---------- */

  key(kind, name) { return `${kind}\u0000${name}`; },

  /* Etiqueta en texto corrido: las categorías llevan ▣ delante. */
  nodeLabel(kind, name) {
    return (kind || "code") === "category" ? `▣ ${I18N.domain(name)}` : name;
  },

  /* Nombres únicos de código con el dominio de su instancia más reciente. */
  _uniqueCodes() {
    const map = new Map();
    for (const code of State.project.codes) map.set(code.name, code.domain);
    return map;
  },

  _categoryColor(kind, name, unique) {
    if (kind === "category") return State.domains[name] || "#999999";
    return State.domains[unique.get(name)] || "#999999";
  },

  /* ---------- Cuadros ---------- */

  boards() {
    const p = State.project;
    return [p.general_board || { id: 0, name: "", nodes: [], edge_colors: {}, show_tone: false },
            ...(p.boards || [])];
  },

  boardName(board) { return board.id === 0 ? I18N.t("board.general") : board.name; },

  _storageKey() { return `cua-board-${State.project.id}`; },

  activeBoard() {
    let id = 0;
    try { id = Number(localStorage.getItem(this._storageKey()) || 0); } catch (_) { /* sin almacenamiento */ }
    return this.boards().find(b => b.id === id) || this.boards()[0];
  },

  _setActiveBoard(id) {
    try { localStorage.setItem(this._storageKey(), String(id)); } catch (_) { /* preferencia no persistente */ }
  },

  /* Quiénes aparecen en un cuadro: en el general, todo extremo de relación
     (sus nodos guardados solo aportan posición y color: al borrar una
     relación, sus extremos sueltos salen del organizador, como siempre); en
     los propios, lo que el investigador eligió. */
  members(board) {
    const seen = new Set();
    const list = [];
    const push = (kind, name) => {
      const k = this.key(kind, name);
      if (seen.has(k)) return;
      seen.add(k);
      list.push({ kind, name });
    };
    if (board.id === 0) {
      for (const r of State.project.relations) {
        push(r.source_kind || "code", r.source);
        push(r.target_kind || "code", r.target);
      }
      return list;
    }
    for (const n of board.nodes) push(n.kind, n.name);
    return list;
  },

  _edges(board, members) {
    const present = new Set(members.map(m => this.key(m.kind, m.name)));
    return State.project.relations.filter(r =>
      present.has(this.key(r.source_kind || "code", r.source))
      && present.has(this.key(r.target_kind || "code", r.target)));
  },

  /* Posición de cada nodo: la guardada o, si no tiene, en círculo (como el
     organizador de siempre). */
  _positions(board, members) {
    const stored = new Map(board.nodes.map(n => [this.key(n.kind, n.name), n]));
    const positions = new Map();
    const auto = members.filter(m => {
      const n = stored.get(this.key(m.kind, m.name));
      return !(n && n.x != null && n.y != null);
    });
    const cx = this.W / 2, cy = this.H / 2;
    const radius = Math.min(this.W, this.H) / 2 - 90;
    for (const m of members) {
      const n = stored.get(this.key(m.kind, m.name));
      if (n && n.x != null && n.y != null) positions.set(this.key(m.kind, m.name), { x: n.x, y: n.y });
    }
    if (!positions.size) {
      auto.forEach((m, i) => {
        const angle = (i / auto.length) * Math.PI * 2 - Math.PI / 2;
        positions.set(this.key(m.kind, m.name),
          { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) });
      });
      return positions;
    }
    // Cuadro ya ordenado a mano: cada nodo nuevo va al hueco más alejado de
    // los demás (en una grilla fija), para no caer encima de otro
    const candidates = [];
    for (let x = 70; x <= this.W - 70; x += 40) {
      for (let y = 50; y <= this.H - 80; y += 40) candidates.push({ x, y });
    }
    for (const m of auto) {
      let best = candidates[0], bestScore = -1;
      for (const c of candidates) {
        let near = Infinity;
        for (const p of positions.values()) near = Math.min(near, Math.hypot((p.x - c.x) * 0.8, p.y - c.y));
        if (near > bestScore + 0.01) { bestScore = near; best = c; }
      }
      positions.set(this.key(m.kind, m.name), { ...best });
    }
    return positions;
  },

  /* ---------- Render ---------- */

  render() {
    const unique = this._uniqueCodes();
    // Siempre hay al menos las nueve Categorías Básicas: se puede relacionar
    document.getElementById("rel-empty").classList.add("hidden");
    document.getElementById("rel-builder").classList.remove("hidden");
    document.getElementById("rel-body").classList.remove("hidden");

    this._fillNodeSelect("rel-source", unique);
    this._fillNodeSelect("rel-target", unique);
    const typeSelect = document.getElementById("rel-type");
    const previous = typeSelect.value;
    typeSelect.textContent = "";
    for (const type of Object.keys(this.types)) {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = `${I18N.relType(type)} (${I18N.relVerb(type)})`;
      typeSelect.appendChild(option);
    }
    if (previous) typeSelect.value = previous;
    this._renderGuide();
    document.getElementById("btn-rel-expand").textContent =
      I18N.t(this.expanded ? "board.collapse" : "board.expand");

    this._renderBoardBar(unique);
    this._renderList();
    this._renderGraph(unique);
    this._renderTree(unique);
    this._loadTones();
  },

  /* Selector con dos grupos: códigos y categorías (FR-085). */
  _fillNodeSelect(id, unique, exclude = null) {
    const select = document.getElementById(id);
    const previous = select.value;
    select.textContent = "";
    const codes = [...unique.keys()].sort((a, b) => a.localeCompare(b, I18N.locale));
    const groups = [
      ["code", I18N.t("rel.group.codes"), codes],
      ["category", I18N.t("rel.group.categories"), Object.keys(State.domains)],
    ];
    for (const [kind, label, names] of groups) {
      const options = names.filter(n => !exclude || !exclude.has(this.key(kind, n)));
      if (!options.length) continue;
      const group = document.createElement("optgroup");
      group.label = label;
      for (const name of options) {
        const option = document.createElement("option");
        option.value = this.key(kind, name);
        option.textContent = kind === "category" ? I18N.domain(name) : name;
        group.appendChild(option);
      }
      select.appendChild(group);
    }
    if ([...select.options].some(o => o.value === previous)) select.value = previous;
  },

  _parse(value) {
    const [kind, ...rest] = value.split("\u0000");
    return { kind, name: rest.join("\u0000") };
  },

  _renderBoardBar(unique) {
    const board = this.activeBoard();
    const select = document.getElementById("board-select");
    select.textContent = "";
    for (const b of this.boards()) {
      const option = document.createElement("option");
      option.value = String(b.id);
      option.textContent = this.boardName(b);
      select.appendChild(option);
    }
    select.value = String(board.id);
    document.getElementById("btn-board-rename").disabled = board.id === 0;
    document.getElementById("btn-board-delete").disabled = board.id === 0;
    document.getElementById("board-tone").checked = !!board.show_tone;
    const members = this.members(board);
    this._fillNodeSelect("board-add", unique, new Set(members.map(m => this.key(m.kind, m.name))));
    document.getElementById("board-add-group").classList.toggle("hidden", board.id === 0);
    // Relaciones del proyecto que este cuadro propio aún no muestra (FR-088)
    const present = new Set(members.map(m => this.key(m.kind, m.name)));
    const missing = board.id === 0 ? [] : State.project.relations.filter(r =>
      !(present.has(this.key(r.source_kind || "code", r.source))
        && present.has(this.key(r.target_kind || "code", r.target))));
    const bring = document.getElementById("board-bring");
    bring.textContent = "";
    for (const r of missing) {
      const option = document.createElement("option");
      option.value = String(r.id);
      option.textContent = this.relationText(r);
      bring.appendChild(option);
    }
    document.getElementById("board-bring-group").classList.toggle("hidden", !missing.length);
    document.getElementById("board-hint").textContent = board.locked ? I18N.t("board.locked.hint")
      : I18N.t(board.id === 0 ? "board.hint.general" : "board.hint.custom");
    const lock = document.getElementById("btn-board-lock");
    lock.textContent = I18N.t(board.locked ? "board.unlockboard" : "board.lockboard");
    lock.classList.toggle("btn-locked", !!board.locked);
    document.getElementById("btn-board-layout").disabled = !!board.locked;
    this._syncUndoButton(board);
  },

  async _create() {
    const source = this._parse(document.getElementById("rel-source").value);
    const target = this._parse(document.getElementById("rel-target").value);
    const type = document.getElementById("rel-type").value;
    if (!source.name || !target.name) return;
    if (source.kind === target.kind && source.name === target.name) {
      Views.toast(I18N.t("rel.same"), true);
      return;
    }
    const board = this.activeBoard();
    try {
      const result = await API.createRelation({
        source: source.name, target: target.name, type,
        source_kind: source.kind, target_kind: target.kind,
        board_id: board.id || null,
      });
      await State.reload();
      // Ya existía en el proyecto: se trajo a este cuadro, sin duplicarla (FR-088)
      if (result && result.existed) {
        Views.toast(I18N.t("rel.existed.added", { text: this.relationText(result) }));
        return;
      }
      Views.toast(I18N.t("rel.created", {
        source: this.nodeLabel(source.kind, source.name), verb: I18N.relVerb(type),
        target: this.nodeLabel(target.kind, target.name) }));
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
      p.textContent = I18N.t("rel.none");
      list.appendChild(p);
      return;
    }
    const ul = document.createElement("ul");
    ul.className = "plain-list";
    for (const relation of relations) {
      const li = document.createElement("li");
      const text = document.createElement("span");
      text.textContent = this.relationText(relation);
      const del = document.createElement("button");
      del.className = "icon-btn";
      del.title = I18N.t("rel.delete.title");
      del.textContent = "🗑";
      del.addEventListener("click", () => this._deleteRelation(relation));
      li.append(text, del);
      ul.appendChild(li);
    }
    list.appendChild(ul);
  },

  relationText(relation) {
    return `${this.nodeLabel(relation.source_kind, relation.source)} —${I18N.relVerb(relation.type)}→ `
      + this.nodeLabel(relation.target_kind, relation.target);
  },

  async _deleteRelation(relation) {
    try {
      await API.deleteRelation(relation.id);
      if (this.selection && this.selection.type === "edge" && this.selection.id === relation.id) {
        this.selection = null;
      }
      await State.reload();
      Views.toast(I18N.t("rel.deleted"));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  /* ---------- Organizador ---------- */

  _renderGraph(unique) {
    const container = document.getElementById("rel-graph");
    const legend = document.getElementById("rel-legend");
    container.textContent = "";
    legend.textContent = "";
    const board = this.activeBoard();
    const members = this.members(board);
    this._pruneSelection(board, members);
    if (!members.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = I18N.t(board.id === 0 ? "rel.graph.empty" : "board.empty");
      container.appendChild(p);
      this._renderSelection(board, unique);
      return;
    }
    this.drawBoard(container, board, { interactive: true, tones: board.show_tone ? this._tones : null });
    legend.innerHTML = this.legendHtml(board.show_tone && this._tones && !this._tones.missing, board);
    this._renderSelection(board, unique);
  },

  /* La selección pierde lo que ya no está (fusiones, borrados, otro cuadro). */
  _pruneSelection(board, members) {
    const sel = this.selection;
    if (!sel) return;
    if (sel.type === "edge") {
      if (!this._edges(board, members).some(r => r.id === sel.id)) this.selection = null;
      return;
    }
    const present = new Set(members.map(m => this.key(m.kind, m.name)));
    for (const k of [...sel.keys]) if (!present.has(k)) sel.keys.delete(k);
    if (!sel.keys.size) this.selection = null;
  },

  _isSelected(k) {
    return !!this.selection && this.selection.type === "nodes" && this.selection.keys.has(k);
  },

  /* Geometría de cada forma: medio ancho y medio alto (para recortar las
     aristas en el borde, dibujar el anillo de selección y ubicar etiquetas). */
  _geom(shape, label) {
    if (shape === "box") {
      const width = Math.max(70, Math.min(230, label.length * 7.4 + 24));
      return { shape, hw: width / 2, hh: 16 };
    }
    if (shape === "diamond") return { shape, hw: 23, hh: 23 };
    if (shape === "hexagon") return { shape, hw: 21, hh: 18.2 };
    if (shape === "square") return { shape, hw: 17, hh: 17 };
    return { shape: "circle", hw: 18, hh: 18 };
  },

  /* Distancia del centro al borde de la forma en la dirección (ux, uy). */
  _edgeDistance(g, ux, uy) {
    const ax = Math.abs(ux), ay = Math.abs(uy);
    if (g.shape === "square" || g.shape === "box") {
      return Math.min(ax ? g.hw / ax : Infinity, ay ? g.hh / ay : Infinity);
    }
    if (g.shape === "diamond") return 1 / (ax / g.hw + ay / g.hh);
    return g.hw;
  },

  _nodeShape(m, node) {
    return (node && node.shape) || (m.kind === "category" ? "square" : "circle");
  },

  _nodeText(m) {
    const text = m.kind === "category" ? I18N.domain(m.name).toLocaleUpperCase(I18N.locale) : m.name;
    return text;
  },

  /* Dibuja un cuadro en container. opts.interactive: arrastre y selección
     (en la pestaña); sin él, una imagen fija (reporte académico). */
  drawBoard(container, board, opts = {}) {
    const unique = this._uniqueCodes();
    const members = this.members(board);
    const edges = this._edges(board, members);
    const positions = this._positions(board, members);
    const stored = new Map(board.nodes.map(n => [this.key(n.kind, n.name), n]));
    const tones = opts.tones && !opts.tones.missing ? opts.tones : null;

    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${this.W} ${this.H}`);
    svg.setAttribute("width", "100%");
    svg.style.cssText = "display:block;background:#FDFDF7;border:3px solid #000;touch-action:none;user-select:none;-webkit-user-select:none;";
    const el = (name, attrs) => {
      const node = document.createElementNS(SVG_NS, name);
      for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
      return node;
    };

    // Marcadores: flecha (y rombo de la jerarquía) por color en uso: la punta
    // toma el color de su arista
    const edgeColor = (r) => (board.edge_colors && board.edge_colors[String(r.id)]) || "#000000";
    const defs = el("defs", {});
    for (const color of new Set(edges.map(edgeColor))) {
      const arrow = el("marker", {
        id: `arrow-${color.slice(1)}`, viewBox: "0 0 10 10", refX: 9, refY: 5,
        markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse",
      });
      arrow.appendChild(el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: color }));
      const diamond = el("marker", {
        id: `diamond-${color.slice(1)}`, viewBox: "0 0 12 12", refX: 0, refY: 6,
        markerWidth: 18, markerHeight: 18, markerUnits: "userSpaceOnUse", orient: "auto",
      });
      diamond.appendChild(el("path", { d: "M 0 6 L 6 1 L 12 6 L 6 11 z", fill: color }));
      defs.append(arrow, diamond);
    }
    svg.appendChild(defs);
    if (opts.interactive) {
      // Fondo: clic en vacío quita la selección; arrastrar dibuja un rectángulo
      svg.appendChild(el("rect", { x: 0, y: 0, width: this.W, height: this.H, fill: "transparent",
        class: "no-export", "data-bg": "1" }));
    }

    // Varias relaciones entre el mismo par se curvan para no encimarse
    const pairCount = new Map();
    const pairIndex = new Map();
    const pairKey = (r) => {
      const a = this.key(r.source_kind || "code", r.source), b = this.key(r.target_kind || "code", r.target);
      return a < b ? `${a}\u0001${b}` : `${b}\u0001${a}`;
    };
    for (const r of edges) pairCount.set(pairKey(r), (pairCount.get(pairKey(r)) || 0) + 1);

    const edgeLayer = el("g", {});
    const nodeLayer = el("g", {});
    svg.append(edgeLayer, nodeLayer);
    const edgeParts = [];
    for (const relation of edges) {
      const pk = pairKey(relation);
      const k = pairIndex.get(pk) || 0;
      pairIndex.set(pk, k + 1);
      const offset = (k - (pairCount.get(pk) - 1) / 2) * 40;
      const style = this.STROKES[relation.type] || this.STROKES["asociación"];
      const color = edgeColor(relation);
      const selected = this.selection && this.selection.type === "edge" && this.selection.id === relation.id;
      const group = el("g", {});
      const halo = el("path", { fill: "none", stroke: "#FF3300", "stroke-width": style.width + 7,
        "stroke-opacity": 0.35, class: "no-export" });
      const path = el("path", { fill: "none", stroke: color, "stroke-width": style.width });
      if (style.end) path.setAttribute("marker-end", `url(#arrow-${color.slice(1)})`);
      if (style.start) path.setAttribute("marker-start", `url(#diamond-${color.slice(1)})`);
      if (style.dash) path.setAttribute("stroke-dasharray", style.dash);
      // Contradicción: marca de choque perpendicular a la línea, al centro
      const tick = style.tick ? el("path", { stroke: color, "stroke-width": 3, fill: "none" }) : null;
      const title = document.createElementNS(SVG_NS, "title");
      title.textContent = `${this.nodeLabel(relation.source_kind, relation.source)} ${I18N.relVerb(relation.type)} ${this.nodeLabel(relation.target_kind, relation.target)}`;
      path.appendChild(title);
      const tagCircle = el("circle", { r: 9, fill: "#fff", stroke: color, "stroke-width": 1.5 });
      const tag = el("text", { "text-anchor": "middle", "font-size": 10, "font-weight": 700,
        "font-family": "IBM Plex Mono, monospace", fill: "#000" });
      tag.textContent = I18N.relLetter(relation.type);
      if (selected) group.appendChild(halo);
      group.appendChild(path);
      if (tick) group.appendChild(tick);
      group.append(tagCircle, tag);
      group.setAttribute("data-edge", String(relation.id));
      if (opts.interactive) {
        const hit = el("path", { fill: "none", stroke: "rgba(0,0,0,0)", "stroke-width": 14,
          "pointer-events": "stroke", class: "no-export", style: "cursor:pointer" });
        hit.appendChild(title.cloneNode(true));
        group.appendChild(hit);
        const pick = () => { this.selection = { type: "edge", id: relation.id }; this._refreshGraph(); };
        hit.addEventListener("click", pick);
        tagCircle.addEventListener("click", pick);
        tag.addEventListener("click", pick);
        tagCircle.style.cursor = tag.style.cursor = "pointer";
        edgeParts.push({ relation, offset, parts: [halo, path, hit], tagCircle, tag, tick });
      } else {
        edgeParts.push({ relation, offset, parts: [path], tagCircle, tag, tick });
      }
      edgeLayer.appendChild(group);
    }

    const geoms = new Map();
    for (const m of members) {
      const node = stored.get(this.key(m.kind, m.name));
      geoms.set(this.key(m.kind, m.name), this._geom(this._nodeShape(m, node), this._nodeText(m)));
    }
    const layoutEdges = () => {
      for (const { relation, offset, parts, tagCircle, tag, tick } of edgeParts) {
        const ka = this.key(relation.source_kind || "code", relation.source);
        const kb = this.key(relation.target_kind || "code", relation.target);
        const a = positions.get(ka), b = positions.get(kb);
        if (!a || !b) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.hypot(dx, dy) || 1;
        // Normal fija para el par (sin importar el sentido): las curvas no se cruzan
        const forward = this.key(relation.source_kind || "code", relation.source)
          < this.key(relation.target_kind || "code", relation.target) ? 1 : -1;
        const nx = (-dy / dist) * forward, ny = (dx / dist) * forward;
        const cx = (a.x + b.x) / 2 + nx * offset * 2, cy = (a.y + b.y) / 2 + ny * offset * 2;
        // Recorte en el borde real de cada forma (una caja ancha no es un círculo)
        const ua = Math.hypot(cx - a.x, cy - a.y) || 1, ub = Math.hypot(cx - b.x, cy - b.y) || 1;
        const ta = this._edgeDistance(geoms.get(ka), (cx - a.x) / ua, (cy - a.y) / ua) + 5;
        const tb = this._edgeDistance(geoms.get(kb), (cx - b.x) / ub, (cy - b.y) / ub) + 5;
        const x1 = a.x + ((cx - a.x) / ua) * ta, y1 = a.y + ((cy - a.y) / ua) * ta;
        const x2 = b.x + ((cx - b.x) / ub) * tb, y2 = b.y + ((cy - b.y) / ub) * tb;
        const d = offset ? `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}` : `M ${x1} ${y1} L ${x2} ${y2}`;
        for (const part of parts) part.setAttribute("d", d);
        const mx = offset ? 0.25 * x1 + 0.5 * cx + 0.25 * x2 : (x1 + x2) / 2;
        const my = offset ? 0.25 * y1 + 0.5 * cy + 0.25 * y2 : (y1 + y2) / 2;
        tagCircle.setAttribute("cx", mx);
        tagCircle.setAttribute("cy", my);
        tag.setAttribute("x", mx);
        tag.setAttribute("y", my + 3.5);
        if (tick) { // tangente en el punto medio: (x2 − x1, y2 − y1) también en la curva
          const tx = x2 - x1, ty = y2 - y1, tl = Math.hypot(tx, ty) || 1;
          const px = (-ty / tl) * 15, py = (tx / tl) * 15;
          tick.setAttribute("d", `M ${mx - px} ${my - py} L ${mx + px} ${my + py}`);
        }
      }
    };

    const groups = new Map();
    for (const m of members) {
      const k = this.key(m.kind, m.name);
      const pos = positions.get(k);
      const node = stored.get(k);
      const color = (node && node.color) || this._categoryColor(m.kind, m.name, unique);
      const g = geoms.get(k);
      const isCategory = m.kind === "category";
      // La clave lleva un separador nulo, inválido en XML: va codificada para que
      // el SVG exportado siga siendo un archivo válido
      const group = el("g", { transform: `translate(${pos.x},${pos.y})`, "data-key": encodeURIComponent(k),
        "data-kind": m.kind, "data-shape": g.shape });
      if (opts.interactive && this._isSelected(k)) {
        const pad = 8;
        group.appendChild(g.shape === "square" || g.shape === "box"
          ? el("rect", { x: -g.hw - pad, y: -g.hh - pad, width: 2 * (g.hw + pad), height: 2 * (g.hh + pad),
              fill: "none", stroke: "#FF3300", "stroke-width": 3, "stroke-dasharray": "5,3", class: "no-export" })
          : el("circle", { r: Math.max(g.hw, g.hh) + pad, fill: "none", stroke: "#FF3300", "stroke-width": 3,
              "stroke-dasharray": "5,3", class: "no-export" }));
      }
      // Las categorías llevan borde más grueso: se distinguen aunque cambien de forma
      const stroke = isCategory ? 4 : 2.5;
      let shape;
      if (g.shape === "box") {
        // Caja con el nombre adentro: fondo claro y borde de color (la etiqueta va
        // siempre en tinta, legible aunque la categoría sea oscura)
        shape = el("g", {});
        shape.appendChild(el("rect", { x: -g.hw - 2.5, y: -g.hh - 2.5, width: 2 * g.hw + 5, height: 2 * g.hh + 5,
          fill: "none", stroke: "#000", "stroke-width": isCategory ? 3 : 1.5 }));
        shape.appendChild(el("rect", { x: -g.hw, y: -g.hh, width: 2 * g.hw, height: 2 * g.hh,
          fill: "#FFFFFF", stroke: color, "stroke-width": 4 }));
      } else if (g.shape === "square") {
        shape = el("rect", { x: -g.hw, y: -g.hh, width: 2 * g.hw, height: 2 * g.hh, fill: color, stroke: "#000", "stroke-width": stroke });
      } else if (g.shape === "diamond") {
        shape = el("polygon", { points: `0,${-g.hh} ${g.hw},0 0,${g.hh} ${-g.hw},0`, fill: color, stroke: "#000", "stroke-width": stroke });
      } else if (g.shape === "hexagon") {
        const pts = [0, 60, 120, 180, 240, 300].map(a => {
          const r = (a * Math.PI) / 180;
          return `${(g.hw * Math.cos(r)).toFixed(1)},${(g.hw * Math.sin(r)).toFixed(1)}`;
        });
        shape = el("polygon", { points: pts.join(" "), fill: color, stroke: "#000", "stroke-width": stroke });
      } else {
        shape = el("circle", { r: g.hw, fill: color, stroke: "#000", "stroke-width": stroke });
      }
      const title = document.createElementNS(SVG_NS, "title");
      title.textContent = this.nodeLabel(m.kind, m.name);
      shape.appendChild(title);
      group.appendChild(shape);
      const full = this._nodeText(m);
      const max = g.shape === "box" ? 28 : 24;
      const label = el("text", { x: 0, y: g.shape === "box" ? 4 : g.hh + 18, "text-anchor": "middle",
        "font-size": 12, "font-weight": 700, "font-family": "IBM Plex Mono, monospace", fill: "#000",
        "paint-order": "stroke", stroke: g.shape === "box" ? "#FFFFFF" : "#FDFDF7", "stroke-width": 3 });
      label.textContent = full.length > max ? full.slice(0, max) + "…" : full;
      group.appendChild(label);
      if (opts.interactive && (node && node.locked)) {
        const icon = el("text", { x: g.hw + 4, y: -g.hh + 2, "font-size": 12, class: "no-export",
          "font-family": "Apple Color Emoji, Segoe UI Emoji, sans-serif" });
        icon.textContent = "🔒";
        group.appendChild(icon);
      }
      if (tones) this._drawTone(group, el, tones, m, g.shape === "box" ? g.hh + 18 : g.hh + 34);
      if (opts.interactive) group.style.cursor = board.locked || (node && node.locked) ? "pointer" : "grab";
      groups.set(k, group);
      nodeLayer.appendChild(group);
    }
    if (opts.interactive) this._wireInteraction(svg, board, members, positions, groups, layoutEdges);
    layoutEdges();
    container.appendChild(svg);
    return svg;
  },

  /* Tono emocional sobre el nodo (FR-086): valencia media de sus citas. */
  _drawTone(group, el, tones, m, y = 52) {
    const info = m.kind === "category" ? tones.category[m.name] : tones.code[m.name];
    const text = info ? `◑ ${info.score > 0 ? "+" : ""}${info.score.toFixed(2)} (${info.n})` : "◑ —";
    const color = !info ? "#BBBBBB" : info.score > 0.05 ? "#00CC66" : info.score < -0.05 ? "#CC0000" : "#BBBBBB";
    const width = text.length * 6.6 + 18;
    const badge = el("g", { transform: `translate(0,${y})` });
    badge.appendChild(el("rect", { x: -width / 2, y: -9, width, height: 17, fill: "#fff", stroke: "#000", "stroke-width": 1.5 }));
    badge.appendChild(el("rect", { x: -width / 2 + 4, y: -5, width: 9, height: 9, fill: color, stroke: "#000", "stroke-width": 1 }));
    const label = el("text", { x: 7, y: 4, "text-anchor": "middle", "font-size": 10, "font-weight": 700,
      "font-family": "IBM Plex Mono, monospace", fill: "#000" });
    label.textContent = text;
    const title = document.createElementNS(SVG_NS, "title");
    title.textContent = info ? I18N.t("board.tone.title", { score: info.score, n: info.n }) : I18N.t("board.tone.none");
    badge.appendChild(title);
    badge.appendChild(label);
    group.appendChild(badge);
  },

  /* Interacción del organizador (FR-087), con un solo manejador de puntero:
     - clic en un nodo: lo selecciona; Shift + clic: lo suma o lo quita;
     - arrastrar un nodo: lo mueve; si está en una selección de varios, se
       mueve el grupo entero (los bloqueados quedan quietos);
     - arrastrar sobre el fondo: rectángulo de selección (Shift suma);
     - clic en el fondo: quita la selección. */
  _wireInteraction(svg, board, members, positions, groups, layoutEdges) {
    const stored = new Map(board.nodes.map(n => [this.key(n.kind, n.name), n]));
    const isLocked = (k) => !!board.locked || !!(stored.get(k) && stored.get(k).locked);
    const point = (e) => {
      const p = svg.createSVGPoint();
      p.x = e.clientX;
      p.y = e.clientY;
      return p.matrixTransform(svg.getScreenCTM().inverse());
    };
    let action = null;
    const band = document.createElementNS(SVG_NS, "rect");
    band.setAttribute("class", "no-export");
    band.setAttribute("fill", "rgba(255,51,0,0.08)");
    band.setAttribute("stroke", "#FF3300");
    band.setAttribute("stroke-dasharray", "4,3");
    band.setAttribute("pointer-events", "none");
    band.style.display = "none";
    svg.appendChild(band);

    svg.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 || e.target.closest("[data-edge]")) return; // las relaciones usan clic
      const start = point(e);
      const nodeEl = e.target.closest("[data-key]");
      e.preventDefault();
      svg.setPointerCapture(e.pointerId);
      if (!nodeEl) {
        action = { type: "band", start, x0: e.clientX, y0: e.clientY, shift: e.shiftKey, moved: false };
        return;
      }
      const k = decodeURIComponent(nodeEl.getAttribute("data-key"));
      const group = this._isSelected(k) && this.selection.keys.size > 1 ? [...this.selection.keys] : [k];
      const moving = group.filter(key => !isLocked(key));
      action = { type: "node", key: k, shift: e.shiftKey, start, x0: e.clientX, y0: e.clientY, moved: false,
        moving, origin: new Map(moving.map(key => [key, { ...positions.get(key) }])),
        before: new Map(members.map(m => { const key = this.key(m.kind, m.name); return [key, { ...positions.get(key) }]; })) };
    });
    svg.addEventListener("pointermove", (e) => {
      if (!action) return;
      if (!action.moved && Math.hypot(e.clientX - action.x0, e.clientY - action.y0) < 4) return;
      const p = point(e);
      if (action.type === "band") {
        action.moved = true;
        const x = Math.min(p.x, action.start.x), y = Math.min(p.y, action.start.y);
        band.setAttribute("x", x);
        band.setAttribute("y", y);
        band.setAttribute("width", Math.abs(p.x - action.start.x));
        band.setAttribute("height", Math.abs(p.y - action.start.y));
        band.style.display = "";
        return;
      }
      if (action.shift) return; // Shift + clic solo selecciona
      if (!action.moving.length) {
        if (!action.warned) {
          action.warned = true;
          Views.toast(I18N.t(board.locked ? "board.locked.board" : "board.locked.node"), true);
        }
        return;
      }
      action.moved = true;
      // Un solo desplazamiento para todo el grupo, acotado para que nadie salga del cuadro
      let dx = p.x - action.start.x, dy = p.y - action.start.y;
      for (const o of action.origin.values()) {
        dx = Math.max(24 - o.x, Math.min(this.W - 24 - o.x, dx));
        dy = Math.max(24 - o.y, Math.min(this.H - 60 - o.y, dy));
      }
      for (const [key, o] of action.origin) {
        const pos = { x: o.x + dx, y: o.y + dy };
        positions.set(key, pos);
        groups.get(key).setAttribute("transform", `translate(${pos.x},${pos.y})`);
      }
      layoutEdges();
    });
    const finish = (e) => {
      if (!action) return;
      const done = action;
      action = null;
      try { svg.releasePointerCapture(e.pointerId); } catch (_) { /* ya liberado */ }
      band.style.display = "none";
      if (done.type === "band") {
        if (done.moved) {
          const x1 = Number(band.getAttribute("x")), y1 = Number(band.getAttribute("y"));
          const x2 = x1 + Number(band.getAttribute("width")), y2 = y1 + Number(band.getAttribute("height"));
          const inside = members.map(m => this.key(m.kind, m.name)).filter(key => {
            const pos = positions.get(key);
            return pos.x >= x1 && pos.x <= x2 && pos.y >= y1 && pos.y <= y2;
          });
          const keys = done.shift && this.selection && this.selection.type === "nodes"
            ? new Set([...this.selection.keys, ...inside]) : new Set(inside);
          this.selection = keys.size ? { type: "nodes", keys } : null;
        } else if (!done.shift) {
          this.selection = null;
        }
        this._refreshGraph();
        return;
      }
      if (done.moved) {
        // El cuadro vigente (no el de cuando se dibujó): tras un arrastre previo,
        // sus posiciones guardadas ya cambiaron
        const current = this.boards().find(b => b.id === board.id) || board;
        this._pushUndo(current, done.before);
        this._savePositions(current, members, positions);
        return;
      }
      if (done.shift) {
        const keys = this.selection && this.selection.type === "nodes" ? new Set(this.selection.keys) : new Set();
        if (keys.has(done.key)) keys.delete(done.key); else keys.add(done.key);
        this.selection = keys.size ? { type: "nodes", keys } : null;
      } else {
        this.selection = { type: "nodes", keys: new Set([done.key]) };
      }
      this._refreshGraph();
    };
    svg.addEventListener("pointerup", finish);
    svg.addEventListener("pointercancel", (e) => {
      if (!action) return;
      // Cancelado por el sistema: nada se guarda y el cuadro se redibuja como estaba
      action = null;
      band.style.display = "none";
      try { svg.releasePointerCapture(e.pointerId); } catch (_) { /* ya liberado */ }
      this._refreshGraph();
    });
  },

  /* ---------- Deshacer movimientos (FR-087) ----------
     Pila por proyecto y cuadro, solo con posiciones: deshacer un movimiento
     nunca revierte un color o una forma elegidos después. */

  _undoKey(board) { return `${State.project.id}:${board.id}`; },

  _pushUndo(board, before) {
    const key = this._undoKey(board);
    const stack = this._undo[key] || (this._undo[key] = []);
    const stored = new Map(board.nodes.map(n => [this.key(n.kind, n.name), n]));
    // Lo que había guardado (null = automático) y, si no había, lo que se veía
    const snapshot = new Map();
    for (const [k, pos] of before) {
      const n = stored.get(k);
      snapshot.set(k, n ? { x: n.x, y: n.y } : { x: null, y: null, seen: pos });
    }
    stack.push(snapshot);
    if (stack.length > 30) stack.shift();
    this._syncUndoButton(board);
  },

  _syncUndoButton(board) {
    const stack = this._undo[this._undoKey(board)] || [];
    document.getElementById("btn-board-undo").disabled = !stack.length || !!board.locked;
  },

  async _undoMove() {
    const board = this.activeBoard();
    const stack = this._undo[this._undoKey(board)] || [];
    const snapshot = stack.pop();
    if (!snapshot || board.locked) { this._syncUndoButton(board); return; }
    const nodes = board.nodes.map(n => {
      const s = snapshot.get(this.key(n.kind, n.name));
      return s ? { ...this._nodeOut(n), x: s.x, y: s.y } : this._nodeOut(n);
    });
    await this._saveBoard(board, { ...this._payload(board), nodes });
    this.render();
    Views.toast(I18N.t("board.undone"));
  },

  /* Leyenda con muestras dibujadas de cada trazo (en currentColor: se lee en
     modo claro y oscuro) y la simbología de los nodos. */
  legendHtml(withTone, board = null) {
    const esc = (t) => Reporte.esc(t);
    const sample = (type) => {
      const st = this.STROKES[type];
      const dash = st.dash ? ` stroke-dasharray="${st.dash}"` : "";
      let svg = `<svg class="rel-sample" viewBox="0 0 70 16" width="70" height="16" aria-hidden="true">`
        + `<line x1="${st.start ? 14 : 3}" y1="8" x2="${st.end ? 58 : 67}" y2="8" stroke="currentColor" stroke-width="${st.width}"${dash}/>`;
      if (st.start) svg += `<path d="M 2 8 L 8 3 L 14 8 L 8 13 z" fill="currentColor"/>`;
      if (st.end) svg += `<path d="M 57 3 L 67 8 L 57 13 z" fill="currentColor"/>`;
      if (st.tick) svg += `<line x1="35" y1="1" x2="35" y2="15" stroke="currentColor" stroke-width="3"/>`;
      return svg + "</svg>";
    };
    const rows = [];
    for (const type of Object.keys(this.STROKES)) {
      if (!this.types[type]) continue;
      rows.push(`<div class="rel-legend-row">${sample(type)}<span><strong>(${esc(I18N.relLetter(type))}) ${esc(I18N.relType(type))}</strong>: ${esc(I18N.relVerb(type))}. <span class="rel-legend-guide">${esc(I18N.t(`rel.guide.${type}.short`))}</span></span></div>`);
    }
    rows.push(`<div class="rel-legend-row">${esc(I18N.t("rel.legend.native"))}</div>`);
    if (board) {
      const custom = [...new Set(board.nodes.map(n => n.shape).filter(Boolean))];
      if (custom.length) {
        const names = custom.map(sh => `${this.SHAPE_SYMBOLS[sh]} ${I18N.t(`shape.${sh}`).toLocaleLowerCase(I18N.locale)}`).join(", ");
        rows.push(`<div class="rel-legend-row">${esc(I18N.t("rel.legend.custom", { shapes: names }))}</div>`);
      }
    }
    if (withTone) rows.push(`<div class="rel-legend-row">◑ ${esc(I18N.t("board.tone.legend"))}</div>`);
    return rows.join("");
  },

  _refreshGraph() {
    this._renderGraph(this._uniqueCodes());
  },

  /* ---------- Edición del cuadro (solo vista) ---------- */

  /* Un nodo del cuadro con TODOS sus campos: el cuadro se guarda entero y un
     campo omitido se perdería (forma, candado…). */
  _nodeOut(n) {
    return { kind: n.kind, name: n.name, x: n.x ?? null, y: n.y ?? null, color: n.color ?? null,
             shape: n.shape ?? null, locked: !!n.locked };
  },

  _payload(board) {
    return {
      nodes: board.nodes.map(n => this._nodeOut(n)),
      edge_colors: { ...(board.edge_colors || {}) },
      show_tone: !!board.show_tone,
      locked: !!board.locked,
    };
  },

  async _saveBoard(board, payload) {
    try {
      const saved = await API.updateBoard(board.id, payload);
      if (saved.id === 0) State.project.general_board = saved;
      else State.project.boards = State.project.boards.map(b => (b.id === saved.id ? saved : b));
      Views.pulseSaved();
      return saved;
    } catch (error) {
      Views.toast(error.message, true);
      return null;
    }
  },

  /* Al mover un nodo se fijan TODAS las posiciones visibles: si solo se fijara
     el movido, los demás se reacomodarían en el círculo y saltarían. */
  async _savePositions(board, members, positions) {
    const stored = new Map(board.nodes.map(n => [this.key(n.kind, n.name), n]));
    const nodes = members.map(m => {
      const k = this.key(m.kind, m.name);
      const pos = positions.get(k);
      const prev = stored.get(k);
      return { ...this._nodeOut(prev || { kind: m.kind, name: m.name }),
               x: Math.round(pos.x), y: Math.round(pos.y) };
    });
    await this._saveBoard(board, { ...this._payload(board), nodes });
  },

  _renderSelection(board, unique) {
    const box = document.getElementById("rel-selection");
    box.textContent = "";
    const sel = this.selection;
    const members = this.members(board);
    if (!sel) { box.classList.add("hidden"); return; }
    box.classList.remove("hidden");
    const head = document.createElement("div");
    head.className = "mini-label";
    const row = document.createElement("div");
    row.className = "rel-selection-row";

    if (sel.type === "nodes") {
      const keys = [...sel.keys];
      const items = keys.map(k => ({ k, ...this._parse(k) }));
      const stored = new Map(board.nodes.map(n => [this.key(n.kind, n.name), n]));
      const first = items[0];
      const firstNode = stored.get(first.k);
      if (items.length === 1) {
        head.textContent = `${I18N.t(first.kind === "category" ? "rel.legend.category" : "rel.legend.code").toUpperCase()}: ${first.kind === "category" ? I18N.domain(first.name) : first.name}`;
      } else {
        head.textContent = I18N.t("board.selected.n", { n: items.length });
      }
      // Color (para todos los seleccionados)
      const base = (firstNode && firstNode.color) || this._categoryColor(first.kind, first.name, unique);
      const color = this._colorInput(base, (value, final) =>
        this._setNodesProp(board, keys, { color: value.toUpperCase() }, final));
      const reset = this._button(I18N.t("board.color.reset"), () => this._setNodesProp(board, keys, { color: null }, true));
      reset.disabled = !keys.some(k => stored.get(k) && stored.get(k).color);
      row.append(this._labelled(I18N.t("board.color"), color), reset);
      // Forma: nativa o una elegida
      const shape = document.createElement("select");
      shape.className = "rel-shape-select";
      const shapes = new Set(keys.map(k => (stored.get(k) && stored.get(k).shape) || ""));
      for (const value of ["", ...this.SHAPES]) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value ? `${this.SHAPE_SYMBOLS[value]} ${I18N.t(`shape.${value}`)}` : I18N.t("shape.native");
        shape.appendChild(option);
      }
      if (shapes.size === 1) shape.value = [...shapes][0];
      else {
        const mixed = document.createElement("option");
        mixed.value = "__mixed";
        mixed.textContent = I18N.t("shape.mixed");
        mixed.disabled = true;
        shape.prepend(mixed);
        shape.value = "__mixed";
      }
      shape.addEventListener("change", () => this._setNodesProp(board, keys, { shape: shape.value || null }, true));
      row.appendChild(this._labelled(I18N.t("board.shape"), shape));
      // Candado
      const allLocked = keys.every(k => stored.get(k) && stored.get(k).locked);
      const lock = this._button(I18N.t(allLocked ? "board.unlock" : "board.lock"),
        () => this._setNodesProp(board, keys, { locked: !allLocked }, true));
      row.appendChild(lock);
      // En el general todo nodo es extremo de una relación: no se quita
      if (board.id !== 0) row.appendChild(this._button(I18N.t("board.remove"), () => this._removeNodes(board, keys)));
      if (items.length === 1 && first.kind === "code") {
        row.appendChild(this._button(I18N.t("board.book"), () => {
          this.setExpanded(false);
          Views.show("libro");
          Libro.open("code", first.name);
        }));
      }
    } else {
      const relation = State.project.relations.find(r => r.id === sel.id);
      if (!relation) { this.selection = null; box.classList.add("hidden"); return; }
      head.textContent = `${I18N.t("board.edge").toUpperCase()}: ${this.relationText(relation)}`;
      const current = (board.edge_colors || {})[String(relation.id)] || "#000000";
      const color = this._colorInput(current, (value, final) => this._setEdgeColor(board, relation, value, final));
      const reset = this._button(I18N.t("board.color.black"), () => this._setEdgeColor(board, relation, null, true));
      reset.disabled = current === "#000000";
      row.append(this._labelled(I18N.t("board.color"), color), reset,
        this._button(I18N.t("rel.reverse"), () => this._reverseRelation(relation)),
        this._button(I18N.t("board.edge.delete"), () => this._deleteRelation(relation)));
    }
    const close = this._button("✕", () => { this.selection = null; this._refreshGraph(); });
    close.title = I18N.t("board.deselect");
    row.appendChild(close);
    box.append(head, row);
  },

  _button(text, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "btn btn-small";
    b.textContent = text;
    b.addEventListener("click", onClick);
    return b;
  },

  _labelled(text, input) {
    const label = document.createElement("label");
    label.className = "mini-label rel-color-label";
    label.append(document.createTextNode(text), input);
    return label;
  },

  /* Selector de color visible (nunca encadenado a un diálogo: ver v1.8). */
  _colorInput(value, onChange) {
    const input = document.createElement("input");
    input.type = "color";
    input.value = /^#[0-9a-f]{6}$/i.test(value) ? value : "#999999";
    input.addEventListener("input", () => onChange(input.value, false));
    input.addEventListener("change", () => onChange(input.value, true));
    return input;
  },

  /* Aplica un cambio (color, forma, candado) a todos los nodos elegidos. Un
     nodo sin ficha en el cuadro la recibe con su posición actual si el cuadro
     ya está ordenado a mano (así no salta de lugar). */
  _setNodesProp(board, keys, patch, final) {
    const members = this.members(board);
    const anyFixed = board.nodes.some(n => n.x != null && n.y != null);
    const positions = anyFixed ? this._positions(board, members) : null;
    const nodes = board.nodes.map(n => this._nodeOut(n));
    for (const k of keys) {
      let node = nodes.find(n => this.key(n.kind, n.name) === k);
      if (!node) {
        const { kind, name } = this._parse(k);
        const pos = positions && positions.get(k);
        node = this._nodeOut({ kind, name, x: pos ? Math.round(pos.x) : null, y: pos ? Math.round(pos.y) : null });
        nodes.push(node);
      }
      Object.assign(node, patch);
    }
    const draft = { ...board, nodes };
    if (!final) { // vista previa mientras se elige el color
      this._previewBoard(draft);
      return;
    }
    this._saveBoard(board, this._payload(draft)).then(() => this._refreshGraph());
  },

  _setEdgeColor(board, relation, color, final) {
    const edgeColors = { ...(board.edge_colors || {}) };
    if (color && color.toUpperCase() !== "#000000") edgeColors[String(relation.id)] = color.toUpperCase();
    else delete edgeColors[String(relation.id)];
    const draft = { ...board, edge_colors: edgeColors };
    if (!final) { this._previewBoard(draft); return; }
    this._saveBoard(board, this._payload(draft)).then(() => this._refreshGraph());
  },

  _previewBoard(draft) {
    const container = document.getElementById("rel-graph");
    container.textContent = "";
    this.drawBoard(container, draft, { interactive: false, tones: draft.show_tone ? this._tones : null });
  },

  async _removeNodes(board, keys) {
    const drop = new Set(keys);
    const nodes = board.nodes.filter(n => !drop.has(this.key(n.kind, n.name))).map(n => this._nodeOut(n));
    this.selection = null;
    await this._saveBoard(board, { ...this._payload(board), nodes });
    this.render();
  },

  async _bringRelation() {
    const board = this.activeBoard();
    const id = Number(document.getElementById("board-bring").value);
    const relation = State.project.relations.find(r => r.id === id);
    if (!relation || board.id === 0) return;
    try {
      await API.bringRelation(board.id, id);
      await State.reload();
      Views.toast(I18N.t("board.brought", { text: this.relationText(relation) }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _reverseRelation(relation) {
    try {
      const reversed = await API.reverseRelation(relation.id);
      await State.reload();
      Views.toast(I18N.t("rel.reversed", { text: this.relationText(reversed) }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _toggleBoardLock() {
    const board = this.activeBoard();
    await this._saveBoard(board, { ...this._payload(board), locked: !board.locked });
    this.render();
    Views.toast(I18N.t(board.locked ? "board.unlocked.done" : "board.locked.done"));
  },

  async _addNode() {
    const value = document.getElementById("board-add").value;
    if (!value) return;
    const { kind, name } = this._parse(value);
    const board = this.activeBoard();
    let nodes = [...board.nodes.map(n => this._nodeOut(n)), this._nodeOut({ kind, name })];
    if (board.nodes.some(n => n.x != null && n.y != null)) {
      // Cuadro ya ordenado a mano: se fija dónde queda todo, y el nuevo va
      // al hueco más alejado de los demás (ver _positions)
      const draft = { ...board, nodes };
      const positions = this._positions(draft, this.members(draft));
      nodes = nodes.map(n => {
        const p = positions.get(this.key(n.kind, n.name));
        return { ...n, x: Math.round(p.x), y: Math.round(p.y) };
      });
    }
    await this._saveBoard(board, { ...this._payload(board), nodes });
    this.render();
  },

  /* Vuelve al círculo; los nodos bloqueados se quedan donde están. */
  async _resetLayout() {
    const board = this.activeBoard();
    if (board.locked) return;
    const members = this.members(board);
    const positions = this._positions(board, members);
    this._pushUndo(board, positions);
    const nodes = board.nodes.map(n => (n.locked ? this._nodeOut(n) : { ...this._nodeOut(n), x: null, y: null }));
    await this._saveBoard(board, { ...this._payload(board), nodes });
    this.render();
  },

  async _toggleTone(on) {
    const board = this.activeBoard();
    await this._saveBoard(board, { ...this._payload(board), show_tone: on });
    this.render();
  },

  async _newBoard() {
    const name = await Views.ask(I18N.t("board.ask.new"));
    if (!name) return;
    try {
      const board = await API.createBoard(name);
      this._setActiveBoard(board.id);
      this.selection = null;
      await State.reload();
      Views.toast(I18N.t("board.created", { name }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async _renameBoard() {
    const board = this.activeBoard();
    if (board.id === 0) return;
    const name = await Views.ask(I18N.t("board.ask.rename"), board.name);
    if (!name || name === board.name) return;
    if (await this._saveBoard(board, { ...this._payload(board), name })) this.render();
  },

  async _deleteBoard() {
    const board = this.activeBoard();
    if (board.id === 0) return;
    if (!await Views.confirm(I18N.t("board.delete.confirm", { name: board.name }))) return;
    try {
      await API.deleteBoard(board.id);
      delete this._undo[this._undoKey(board)];
      this._setActiveBoard(0);
      this.selection = null;
      await State.reload();
      Views.toast(I18N.t("board.deleted", { name: board.name }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  /* ---------- Tono emocional (FR-086) ---------- */

  /* El organizador se dibuja primero; el tono llega después (el análisis de
     un corpus grande puede tardar o faltar el léxico) y se superpone. */
  async _loadTones() {
    const board = this.activeBoard();
    const note = document.getElementById("board-tone-note");
    note.textContent = "";
    if (!board.show_tone) return;
    const run = ++this._toneRun;
    note.textContent = I18N.t("board.tone.loading");
    try {
      this._tones = await this.fetchTones(({ done, total }) => {
        if (run === this._toneRun) note.textContent = I18N.t("analysis.progress", { done, total });
      });
    } catch (error) {
      this._tones = null;
      if (run === this._toneRun) note.textContent = error.message;
      return;
    }
    if (run !== this._toneRun || Views.current !== "relaciones") return;
    note.textContent = this._tones.missing ? I18N.t("board.tone.missing") : "";
    this._refreshGraph();
  },

  async fetchTones(onProgress) {
    const data = await API.sentiment(Views.corpusLang, onProgress);
    if (data.lexicon_missing) return { missing: true };
    const category = {};
    for (const d of data.domains || []) category[d.domain] = { score: d.score, n: d.n };
    return { code: data.code_tones || {}, category };
  },

  /* ---------- Árbol ---------- */

  /* Bosque construido desde las relaciones de jerarquía (contiene a). */
  _renderTree(unique) {
    const container = document.getElementById("rel-tree");
    container.textContent = "";
    const edges = State.project.relations.filter(r => r.type === "jerarquía");
    if (!edges.length) {
      const p = document.createElement("p");
      p.className = "empty-note";
      p.textContent = I18N.t("rel.tree.empty");
      container.appendChild(p);
      return;
    }
    const children = new Map();
    const targets = new Set();
    const info = new Map();
    for (const edge of edges) {
      const s = this.key(edge.source_kind || "code", edge.source);
      const t = this.key(edge.target_kind || "code", edge.target);
      info.set(s, { kind: edge.source_kind || "code", name: edge.source });
      info.set(t, { kind: edge.target_kind || "code", name: edge.target });
      if (!children.has(s)) children.set(s, []);
      children.get(s).push(t);
      targets.add(t);
    }
    let roots = [...children.keys()].filter(k => !targets.has(k));
    if (!roots.length) roots = [this.key(edges[0].source_kind || "code", edges[0].source)]; // ciclo puro

    const buildNode = (k, visited) => {
      const { kind, name } = info.get(k);
      const li = document.createElement("li");
      li.className = "tree-node";
      const chip = document.createElement("span");
      chip.className = kind === "category" ? "dom-chip tree-category" : "dom-chip";
      chip.style.backgroundColor = this._categoryColor(kind, name, unique);
      const label = document.createElement("span");
      const text = kind === "category" ? I18N.domain(name) : name;
      label.textContent = visited.has(k) ? `${text} ↺` : text;
      li.append(chip, label);
      if (!visited.has(k) && children.has(k)) {
        const next = new Set(visited).add(k);
        const ul = document.createElement("ul");
        ul.className = "tree-branch";
        for (const child of children.get(k)) ul.appendChild(buildNode(child, next));
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
