/* Barra de música de foco (FR-040): pistas locales del investigador (offline,
   fuente por defecto) o Claude FM, el stream lo-fi 24/7 de Anthropic en
   YouTube (online, opcional). Preferencias de UI en localStorage. */

const Musica = {
  CLAUDE_FM_ID: "YmQ7jRgf4f0", // youtube.com/watch?v=YmQ7jRgf4f0
  tracks: [],
  folder: "",
  index: 0,
  source: "local", // "local" | "fm"
  audio: null,

  async init() {
    this.audio = document.getElementById("mus-audio");
    this.audio.addEventListener("ended", () => this.next());

    document.getElementById("mus-toggle").addEventListener("click", () => this.toggle());
    document.getElementById("mus-next").addEventListener("click", () => this.next());
    document.getElementById("mus-src-local").addEventListener("click", () => this.setSource("local"));
    document.getElementById("mus-src-fm").addEventListener("click", () => this.setSource("fm"));
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

  setSource(source) {
    if (this.source === source) return;
    this.source = source;
    this._stopAll();
    document.getElementById("mus-src-local").classList.toggle("active", source === "local");
    document.getElementById("mus-src-fm").classList.toggle("active", source === "fm");
    document.getElementById("mus-vol").disabled = source === "fm"; // volumen: en el mini-player de YouTube
    this._renderTitle();
  },

  toggle() {
    if (this.source === "fm") {
      this._fmPlaying() ? this._fmStop() : this._fmStart();
    } else {
      if (!this.tracks.length) { this._showFolder(); return; }
      if (this.audio.paused) {
        if (!this.audio.src) this._load(this.index);
        this.audio.play();
      } else {
        this.audio.pause();
      }
    }
    this._renderButton();
  },

  next() {
    if (this.source !== "local" || !this.tracks.length) return;
    this.index = (this.index + 1) % this.tracks.length;
    this._load(this.index);
    this.audio.play();
    this._renderButton();
  },

  _load(i) {
    this.audio.src = `/api/music/${encodeURIComponent(this.tracks[i])}`;
    this._renderTitle();
  },

  _stopAll() {
    this.audio.pause();
    this._fmStop();
    this._renderButton();
  },

  // --- Claude FM (iframe acoplado sobre la barra; requiere internet) ---

  _fmPlaying() {
    return !document.getElementById("fm-dock").classList.contains("hidden");
  },

  _fmStart() {
    const dock = document.getElementById("fm-dock");
    dock.textContent = "";
    const iframe = document.createElement("iframe");
    iframe.src = `https://www.youtube.com/embed/${this.CLAUDE_FM_ID}?autoplay=1`;
    iframe.allow = "autoplay; encrypted-media";
    iframe.title = "Claude FM — música para pensar y construir";
    dock.appendChild(iframe);
    dock.classList.remove("hidden");
    this._renderTitle();
  },

  _fmStop() {
    const dock = document.getElementById("fm-dock");
    dock.textContent = ""; // quitar el iframe detiene el stream
    dock.classList.add("hidden");
  },

  _renderButton() {
    const playing = this.source === "fm" ? this._fmPlaying() : !this.audio.paused;
    document.getElementById("mus-toggle").textContent = playing ? "⏸" : "▶";
  },

  _renderTitle() {
    const title = document.getElementById("mus-title");
    if (this.source === "fm") {
      title.textContent = "Claude FM — lo-fi para pensar y construir (YouTube)";
      return;
    }
    if (!this.tracks.length) {
      title.textContent = "Sin pistas — clic aquí para ver dónde poner tu música";
      return;
    }
    const name = this.tracks[this.index].replace(/\.[^.]+$/, "");
    title.textContent = `♫ ${name}  ·  ${this.index + 1}/${this.tracks.length}`;
  },

  _showFolder() {
    if (this.source === "local" && this.folder) {
      Views.toast(`Tu música va en: ${this.folder}`);
    }
  },
};
