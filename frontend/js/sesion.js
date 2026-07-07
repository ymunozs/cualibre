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
      sessionStorage.setItem("cua-session-asked", "1");
    });
    document.getElementById("session-indicator").addEventListener("click", () => this.ask(true));
    if (!sessionStorage.getItem("cua-session-asked")) this.ask(false);
  },

  ask(manual) {
    if (manual) sessionStorage.removeItem("cua-session-asked");
    document.getElementById("session-goal").value = this.goal;
    document.getElementById("session-dialog").showModal();
  },

  _start() {
    const minutes = parseInt(document.getElementById("session-minutes").value, 10);
    this.goal = document.getElementById("session-goal").value.trim();
    this.startCodes = State.project ? State.project.codes.length : 0;
    this.endTime = Date.now() + minutes * 60_000;
    sessionStorage.setItem("cua-session-asked", "1");
    document.getElementById("session-dialog").close();
    clearInterval(this.timer);
    this.timer = setInterval(() => this._tick(), 1000);
    this._tick();
  },

  _tick() {
    const el = document.getElementById("session-indicator");
    const remaining = this.endTime - Date.now();
    const codes = (State.project ? State.project.codes.length : 0) - this.startCodes;
    if (remaining <= 0) {
      clearInterval(this.timer);
      this.endTime = null;
      el.textContent = `◷ ¡sesión cumplida! · ${codes} código(s)${this.goal ? ` · ${this.goal}` : ""}`;
      Views.toast("◷ Sesión cumplida — buen momento para una pausa");
      return;
    }
    const m = Math.floor(remaining / 60_000);
    const s = Math.floor((remaining % 60_000) / 1000).toString().padStart(2, "0");
    el.textContent = `◷ ${m}:${s} · ${codes} cód.${this.goal ? ` · ${this.goal}` : ""}`;
  },
};
