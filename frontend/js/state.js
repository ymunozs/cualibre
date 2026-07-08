/* Estado del cliente y orquestación de render. El estado durable vive SIEMPRE
   en el backend (FR-025): aquí solo se refleja. */

const State = {
  project: null,
  basicDomains: {}, // Categorías Básicas (fijas, FR-016)
  customDomains: {}, // Categorías personalizadas del proyecto activo (FR-064)
  domains: {}, // basicDomains + customDomains fusionados (para consumo general)

  async _loadDomains() {
    const { basic, custom } = await API.getDomains();
    this.basicDomains = basic;
    this.customDomains = custom;
    this.domains = { ...basic, ...custom };
  },

  async reload() {
    const [project, projects] = await Promise.all([
      API.getProject(),
      API.listProjects(),
      this._loadDomains(), // por si otra sesión/ventana agregó categorías
    ]);
    this.project = project;
    this.renderAll(projects);
  },

  renderAll(projects) {
    Canvas.render();
    Paleta.render();
    Nube.populateDomains(); // categorías personalizadas pueden haber cambiado
    if (projects) Views.renderProjectBar(projects);
    Views.refreshCurrent(); // Analytics/NLP/Exportar al día si están visibles (FR-020)
    Views.pulseSaved(); // el estado quedó persistido en disco (FR-047)
  },
};

// Arranque de la SPA
(async function boot() {
  try {
    await Promise.all([State._loadDomains(), API.getRelationTypes().then(t => { Relations.types = t; })]);
  } catch (error) {
    document.body.insertAdjacentText("afterbegin", "No se pudo conectar con el servidor de CUA-LIBRE.");
    return;
  }
  Canvas.init();
  Nube.init();
  Paleta.init();
  Relations.init();
  Views.init();
  Musica.init();
  Sesion.init();
  Paleta.populateDomains();
  await State.reload();
})();
