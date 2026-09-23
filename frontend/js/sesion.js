/* Sesión de foco con meta y pomodoro (FR-053): al abrir la app pregunta la
   meta y los minutos (omitible); indicador discreto en la barra inferior.
   Nada interrumpe con alarmas: al terminar, un aviso suave. */

const Sesion = {
  endTime: null,
  goal: "",
  startCodes: 0,
  timer: null,

  init() {
    document.getElementById("btn-session-start").addEventListener("click", () => this._start());
    document.getElementById("btn-session-skip").addEventListener("click", () => {
      document.getElementById("session-dialog").close();
      this._remember(true);
    });
    document.getElementById("session-indicator").addEventListener("click", () => this.ask(true));
    I18N.onChange(() => { if (this.endTime || this.done) this._tick(); });
    let asked = false;
    try { asked = !!sessionStorage.getItem("cua-session-asked"); } catch (_) { /* sin almacenamiento */ }
    if (!asked) this.ask(false);
  },

  ask(manual) {
    if (manual) this._remember(false);
    document.getElementById("session-goal").value = this.goal;
    document.getElementById("session-dialog").showModal();
  },

  _start() {
    const minutes = parseInt(document.getElementById("session-minutes").value, 10);
    this.goal = document.getElementById("session-goal").value.trim();
    this.startCodes = State.project ? State.project.codes.length : 0;
    this.endTime = Date.now() + minutes * 60_000;
    this._remember(true);
    this.done = false;
    document.getElementById("session-dialog").close();
    clearInterval(this.timer);
    this.timer = setInterval(() => this._tick(), 1000);
    this._tick();
  },

  _remember(asked) {
    try {
      asked ? sessionStorage.setItem("cua-session-asked", "1")
            : sessionStorage.removeItem("cua-session-asked");
    } catch (_) { /* sin almacenamiento: vuelve a preguntar al recargar */ }
  },

  _tick() {
    const el = document.getElementById("session-indicator");
    const codes = (State.project ? State.project.codes.length : 0) - this.startCodes;
    const goal = this.goal ? ` · ${this.goal}` : "";
    if (this.done) {
      el.textContent = I18N.t("ses.done", { n: codes }) + goal;
      return;
    }
    const remaining = this.endTime - Date.now();
    if (remaining <= 0) {
      clearInterval(this.timer);
      this.endTime = null;
      this.done = true;
      el.textContent = I18N.t("ses.done", { n: codes }) + goal;
      Views.toast(I18N.t("ses.done.toast"));
      return;
    }
    const m = Math.floor(remaining / 60_000);
    const s = Math.floor((remaining % 60_000) / 1000).toString().padStart(2, "0");
    el.textContent = `◷ ${m}:${s} · ${I18N.t("ses.codes", { n: codes })}${goal}`;
  },
};
