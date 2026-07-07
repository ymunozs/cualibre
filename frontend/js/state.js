/* Estado del cliente y orquestación de render. El estado durable vive SIEMPRE
   en el backend (FR-025): aquí solo se refleja. */

const State = {
  project: null,
  domains: {},

  async reload() {
    const [project, projects] = await Promise.all([
      API.getProject(),
      API.listProjects(),
    ]);
    this.project = project;
    this.renderAll(projects);
  },

  renderAll(projects) {
    Canvas.render();
    Paleta.render();
    if (projects) Views.renderProjectBar(projects);
    Views.refreshCurrent(); // Analytics/NLP/Exportar al día si están visibles (FR-020)
    Views.pulseSaved(); // el estado quedó persistido en disco (FR-047)
  },
};

// Arranque de la SPA
(async function boot() {
  try {
    [State.domains, Relations.types] = await Promise.all([
      API.getDomains(),
      API.getRelationTypes(),
    ]);
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
  Nube.populateDomains();
  Paleta.populateDomains();
  await State.reload();
})();
