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
  },
};

// Arranque de la SPA
(async function boot() {
  try {
    State.domains = await API.getDomains();
  } catch (error) {
    document.body.insertAdjacentText("afterbegin", "No se pudo conectar con el servidor de CUA-LIBRE.");
    return;
  }
  Canvas.init();
  Nube.init();
  Paleta.init();
  Views.init();
  Nube.populateDomains();
  Paleta.populateDomains();
  await State.reload();
})();
