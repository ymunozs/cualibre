/* Barra de música de foco (FR-040): pistas locales del investigador, offline.

   Nota histórica: la fuente "Claude FM" (stream de Anthropic en YouTube) se
   retiró el 2026-07-06 por decisión del investigador — el video tiene el
   embedding restringido y mostraba "video privado" al acoplarlo. El
   reproductor queda dedicado a la música propia del compositor de la casa. */

const Musica = {
  tracks: [],
  folder: "",
  index: 0,
  audio: null,

  async init() {
    this.audio = document.getElementById("mus-audio");
    this.audio.addEventListener("ended", () => this.next());

    document.getElementById("mus-toggle").addEventListener("click", () => this.toggle());
    document.getElementById("mus-next").addEventListener("click", () => this.next());
    document.getElementById("mus-title").addEventListener("click", () => this._showFolder());

    const vol = document.getElementById("mus-vol");
    vol.value = localStorage.getItem("cua-vol") || 70;
    this.audio.volume = vol.value / 100;
    vol.addEventListener("input", () => {
      this.audio.volume = vol.value / 100;
      localStorage.setItem("cua-vol", vol.value);
    });

    try {
      const data = await API.music();
      this.tracks = data.tracks;
      this.folder = data.folder;
    } catch (_) { /* la música nunca bloquea el análisis */ }
    this._renderTitle();
  },

  toggle() {
    if (!this.tracks.length) { this._showFolder(); return; }
    if (this.audio.paused) {
      if (!this.audio.src) this._load(this.index);
      this.audio.play();
    } else {
      this.audio.pause();
    }
    this._renderButton();
  },

  next() {
    if (!this.tracks.length) return;
    this.index = (this.index + 1) % this.tracks.length;
    this._load(this.index);
    this.audio.play();
    this._renderButton();
  },

  _load(i) {
    this.audio.src = `/api/music/${encodeURIComponent(this.tracks[i])}`;
    this._renderTitle();
  },

  _renderButton() {
    document.getElementById("mus-toggle").textContent = this.audio.paused ? "▶" : "⏸";
  },

  _renderTitle() {
    const title = document.getElementById("mus-title");
    if (!this.tracks.length) {
      title.textContent = "Sin pistas aún — clic aquí para ver dónde poner tu música";
      return;
    }
    const name = this.tracks[this.index].replace(/\.[^.]+$/, "");
    title.textContent = `♫ ${name}  ·  ${this.index + 1}/${this.tracks.length}`;
  },

  _showFolder() {
    if (this.folder) Views.toast(`Tu música va en: ${this.folder}`);
  },
};
