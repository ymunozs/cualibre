/* Capa de comunicación con el backend (contracts/api.md).
   Canal oficial HTTP/JSON — sin bridges, sin iframes (Principio IV). */

const API = {
  async _fetch(url, options = {}) {
    // Idioma de la interfaz: mensajes de error, demo, manual y exportaciones
    const headers = { ...(options.headers || {}), "X-Cua-Lang": I18N.lang };
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      let detail = `Error ${response.status}`;
      try {
        const body = await response.json();
        if (body.detail) {
          detail = typeof body.detail === "string"
            ? body.detail
            : body.detail.map(d => d.msg).join("; ");
        }
      } catch (_) { /* cuerpo no-JSON */ }
      const error = new Error(detail);
      error.status = response.status;
      error.headers = response.headers;
      throw error;
    }
    if (response.status === 204) return null;
    const body = await response.json();
    if (response.status === 202 && body && body.pending) body.__pending = true;
    return body;
  },

  /* Análisis de corpus grandes (202 + avance): sondea hasta que esté listo,
     informando el progreso con onProgress({done, total}). */
  async _poll(url, onProgress) {
    for (;;) {
      const body = await API._fetch(url);
      if (!body || !body.__pending) return body;
      if (onProgress) onProgress(body);
      await new Promise(resolve => setTimeout(resolve, 1500));
    }
  },

  _json(method, url, body) {
    return this._fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  },

  // Proyectos
  getProject: () => API._fetch("/api/project"),
  listProjects: () => API._fetch("/api/projects"),
  createProject: (name) => API._json("POST", "/api/projects", { name }),
  renameProject: (id, name) => API._json("PATCH", `/api/projects/${id}`, { name }),
  activateProject: (id) => API._json("POST", `/api/projects/${id}/activate`, {}),
  deleteProject: (id) => API._fetch(`/api/projects/${id}?confirm=true`, { method: "DELETE" }),
  importProject(file) {
    const form = new FormData();
    form.append("file", file);
    return API._fetch("/api/projects/import", { method: "POST", body: form });
  },
  createExample: () => API._fetch("/api/projects/example", { method: "POST" }),
  setCorpusLang: (lang) => API._json("PUT", "/api/project/corpus-lang", { lang }),

  // Aplicación de escritorio (FR-081)
  appInfo: () => API._fetch("/api/app-info"),
  openReport: (name, html) => API._json("POST", "/api/app/open-report", { name, html }),
  quit: () => API._json("POST", "/api/app/quit", { confirm: true }),

  // Léxicos de sentimiento (FR-077) y acuerdo entre codificadores (FR-078)
  downloadLexicons: () => API._fetch("/api/lexicons/download", { method: "POST" }),
  importLexicons(file) {
    const form = new FormData();
    form.append("file", file);
    return API._fetch("/api/lexicons/import", { method: "POST", body: form });
  },
  agreement: (other) => API._fetch(`/api/agreement?other=${encodeURIComponent(other)}`),
  resetProject: () => API._json("POST", "/api/project/reset", { confirm: true }),
  saveProject: () => API._json("POST", "/api/project/save", {}),

  // Respaldos con historial (FR-062)
  getSnapshots: () => API._fetch("/api/snapshots"),
  restoreSnapshot: (name) => API._json("POST", `/api/snapshots/${encodeURIComponent(name)}/restore`, { confirm: true }),

  // Dominios (fuente única: backend/models.py)
  getDomains: () => API._fetch("/api/domains"),
  createCustomDomain: (name, color) => API._json("POST", "/api/domains/custom", { name, color }),
  deleteCustomDomain: (name, confirm = false) =>
    API._fetch(`/api/domains/custom/${encodeURIComponent(name)}${confirm ? "?confirm=true" : ""}`, { method: "DELETE" }),

  // Documentos
  uploadDocument(file) {
    const form = new FormData();
    form.append("file", file);
    return API._fetch("/api/documents", { method: "POST", body: form });
  },
  deleteDocument: (id, confirm = false) =>
    API._fetch(`/api/documents/${id}${confirm ? "?confirm=true" : ""}`, { method: "DELETE" }),

  // Códigos
  createCode: (payload) => API._json("POST", "/api/codes", payload),
  updateCode: (id, payload) => API._json("PATCH", `/api/codes/${id}`, payload),
  deleteCode: (id, confirm = false) =>
    API._fetch(`/api/codes/${id}${confirm ? "?confirm=true" : ""}`, { method: "DELETE" }),
  mergeCodes: (fromName, toName) =>
    API._json("POST", "/api/codes/merge", { from_name: fromName, to_name: toName }),

  // Relaciones (FR-038)
  getRelationTypes: () => API._fetch("/api/relation-types"),
  createRelation: (payload) => API._json("POST", "/api/relations", payload),
  deleteRelation: (id) => API._fetch(`/api/relations/${id}`, { method: "DELETE" }),
  bringRelation: (boardId, relationId) =>
    API._fetch(`/api/boards/${boardId}/relations/${relationId}`, { method: "POST" }),
  reverseRelation: (id) => API._fetch(`/api/relations/${id}/reverse`, { method: "POST" }),

  // Libro de códigos (FR-084)
  saveCodebook: (payload) => API._json("PUT", "/api/codebook", payload),
  deleteCodebook: (kind, name) => API._fetch(
    `/api/codebook?kind=${encodeURIComponent(kind)}&name=${encodeURIComponent(name)}&confirm=true`,
    { method: "DELETE" }),

  // Cuadros organizadores (FR-085)
  createBoard: (name) => API._json("POST", "/api/boards", { name }),
  updateBoard: (id, payload) => API._json("PUT", `/api/boards/${id}`, payload),
  deleteBoard: (id) => API._fetch(`/api/boards/${id}?confirm=true`, { method: "DELETE" }),

  // Ajustes del léxico de sentimiento (FR-086)
  setSentimentOverrides: (lang, removed, added) =>
    API._json("PUT", "/api/sentiment/overrides", { lang, removed, added }),

  // Biblioteca de literatura (FR-089..092)
  library: () => API._fetch("/api/library"),
  addLibraryItem(file) {
    const form = new FormData();
    form.append("file", file);
    return API._fetch("/api/library/items", { method: "POST", body: form });
  },
  addReference: (doi) => API._json("POST", "/api/library/refs", { doi }),
  updateLibraryItem: (id, payload) => API._json("PATCH", `/api/library/items/${id}`, payload),
  lookupLibraryItem: (id, doi) => API._json("POST", `/api/library/items/${id}/lookup`, { doi }),
  deleteLibraryItem: (id, confirm = false) =>
    API._fetch(`/api/library/items/${id}${confirm ? "?confirm=true" : ""}`, { method: "DELETE" }),
  libraryText: (id) => API._fetch(`/api/library/items/${id}/text`),
  libraryAnnotations: (id) => API._fetch(`/api/library/items/${id}/annotations`),
  createAnnotation: (payload) => API._json("POST", "/api/library/annotations", payload),
  updateAnnotation: (id, payload) => API._json("PATCH", `/api/library/annotations/${id}`, payload),
  deleteAnnotation: (id) => API._fetch(`/api/library/annotations/${id}`, { method: "DELETE" }),
  createLitCoding: (payload) => API._json("POST", "/api/lit-codings", payload),
  updateLitCoding: (id, memo) => API._json("PATCH", `/api/lit-codings/${id}`, { memo }),
  deleteLitCoding: (id) => API._fetch(`/api/lit-codings/${id}`, { method: "DELETE" }),
  dictionaryStatus: () => API._fetch("/api/dictionary/status"),
  dictionaryDownload: () => API._fetch("/api/dictionary/download", { method: "POST" }),
  dictionaryLookup: (word, lang = "", itemId = "") => API._fetch(
    `/api/dictionary/lookup?word=${encodeURIComponent(word)}&lang=${lang}&item_id=${encodeURIComponent(itemId)}`),
  bibliography: (scope = "all") => API._fetch(`/api/library/bibliography?scope=${scope}`),

  // Música de foco (FR-040)
  music: () => API._fetch("/api/music"),

  // Análisis
  sentiment: (lang, onProgress) => API._poll(`/api/sentiment?lang=${lang}`, onProgress),
  nlp: (lang, minLen, pos = "all", onProgress) =>
    API._poll(`/api/nlp?lang=${lang}&min_len=${minLen}&top=60&pos=${pos}`, onProgress),
  kwic: (q, lang = "es", pos = "all", onProgress) =>
    API._poll(`/api/kwic?q=${encodeURIComponent(q)}&lang=${lang}&pos=${pos}`, onProgress),
  setNlpExclusions: (words) => API._json("PUT", "/api/nlp/exclusions", { words }),
  literature: (q) => API._fetch(`/api/literature?q=${encodeURIComponent(q)}`),
};
