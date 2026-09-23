/* Estado del cliente y orquestación de render. El estado durable vive SIEMPRE
   en el backend (FR-025): aquí solo se refleja. */

const State = {
  project: null,
  basicDomains: {}, // Categorías Básicas (fijas, FR-016)
  customDomains: {}, // Categorías personalizadas del proyecto activo (FR-064)
  domains: {}, // basicDomains + customDomains fusionados (para consumo general)
  projects: [], // resumen de todos los proyectos (selector, acuerdo entre codificadores)

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
    this.projects = projects;
    this.renderAll(projects);
  },

  renderAll(projects, pulse = true) {
    Canvas.render();
    Paleta.populateDomains(); // etiquetas de categoría (idioma) y personalizadas nuevas
    Paleta.render();
    Nube.populateDomains(); // categorías personalizadas pueden haber cambiado
    if (projects) Views.renderProjectBar(projects);
    Views._syncCorpusLang(); // idioma del corpus del proyecto activo (FR-077)
    Views.refreshCurrent(); // Analytics/NLP/Exportar al día si están visibles (FR-020)
    if (pulse) Views.pulseSaved(); // el estado quedó persistido en disco (FR-047)
  },
};

// Arranque de la SPA
(async function boot() {
  I18N.init(); // antes de todo: los módulos leen el idioma al dibujar
  try {
    await Promise.all([State._loadDomains(), API.getRelationTypes().then(t => { Relations.types = t; })]);
  } catch (error) {
    document.body.insertAdjacentText("afterbegin", I18N.t("boot.error"));
    return;
  }
  await Files.init(); // modo ventana/navegador y OCR disponible
  Canvas.init();
  Nube.init();
  Paleta.init();
  Relations.init();
  Acuerdo.init();
  Views.init();
  Musica.init();
  Sesion.init();
  Paleta.populateDomains();
  // Cambio de idioma en caliente: se redibuja todo con el mismo estado
  I18N.onChange(() => { if (State.project) State.renderAll(null, false); });
  await State.reload();
})();
