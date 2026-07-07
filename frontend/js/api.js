/* Capa de comunicación con el backend (contracts/api.md).
   Canal oficial HTTP/JSON — sin bridges, sin iframes (Principio IV). */

const API = {
  async _fetch(url, options = {}) {
    const response = await fetch(url, options);
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
    return response.json();
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
  resetProject: () => API._json("POST", "/api/project/reset", { confirm: true }),
  saveProject: () => API._json("POST", "/api/project/save", {}),

  // Respaldos con historial (FR-062)
  getSnapshots: () => API._fetch("/api/snapshots"),
  restoreSnapshot: (name) => API._json("POST", `/api/snapshots/${encodeURIComponent(name)}/restore`, { confirm: true }),

  // Dominios (fuente única: backend/models.py)
  getDomains: () => API._fetch("/api/domains"),

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
  deleteCode: (id) => API._fetch(`/api/codes/${id}`, { method: "DELETE" }),

  // Relaciones (FR-038)
  getRelationTypes: () => API._fetch("/api/relation-types"),
  createRelation: (payload) => API._json("POST", "/api/relations", payload),
  deleteRelation: (id) => API._fetch(`/api/relations/${id}`, { method: "DELETE" }),

  // Música de foco (FR-040)
  music: () => API._fetch("/api/music"),

  // Análisis
  sentiment: () => API._fetch("/api/sentiment"),
  nlp: (lang, minLen, pos = "all") =>
    API._fetch(`/api/nlp?lang=${lang}&min_len=${minLen}&top=60&pos=${pos}`),
  setNlpExclusions: (words) => API._json("PUT", "/api/nlp/exclusions", { words }),
  literature: (q) => API._fetch(`/api/literature?q=${encodeURIComponent(q)}`),
};
