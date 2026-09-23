/* Guardar archivos (CSV, ZIP, QDPX, PNG, SVG…) en cualquier modo (FR-081).

   En el navegador, una descarga normal. En la ventana propia (pywebview) no
   hay gestor de descargas: el archivo se envía por HTTP al servidor local,
   que muestra el diálogo «Guardar como» del sistema. Sin puentes JS↔Python
   fuera de HTTP (Principio IV). */

const Files = {
  mode: "server", // "window" | "browser" | "server" (lo informa /api/app-info)
  ocr: null, // motor de OCR del sistema, o null

  async init() {
    try {
      const info = await API.appInfo();
      this.mode = info.mode;
      this.ocr = info.ocr;
    } catch (_) { /* servidor antiguo o sin conexión: se asume navegador */ }
    // Enlaces de descarga (<a data-download>): en la ventana propia se desvían
    document.addEventListener("click", (event) => {
      const link = event.target.closest && event.target.closest("a[data-download]");
      if (!link || !this.inWindow) return;
      event.preventDefault();
      this.download(link.href);
    });
  },

  get inWindow() { return this.mode === "window"; },

  async save(blob, filename) {
    if (!this.inWindow) {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 5000);
      return;
    }
    const form = new FormData();
    form.append("file", blob, filename);
    try {
      const { saved } = await API._fetch(
        `/api/app/save-file?filename=${encodeURIComponent(filename)}`, { method: "POST", body: form });
      if (saved) Views.toast(I18N.t("file.saved", { path: saved }));
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  async download(url) {
    try {
      const response = await fetch(url, { headers: { "X-Cua-Lang": I18N.lang } });
      if (!response.ok) throw new Error(`Error ${response.status}`);
      const name = this._filename(response.headers.get("Content-Disposition")) || "cualibre";
      await this.save(await response.blob(), name);
    } catch (error) {
      Views.toast(error.message, true);
    }
  },

  /* Nombre del archivo desde Content-Disposition (prefiere filename* UTF-8). */
  _filename(header) {
    if (!header) return null;
    const utf8 = header.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf8) return decodeURIComponent(utf8[1]);
    const plain = header.match(/filename="([^"]+)"/i);
    return plain ? plain[1] : null;
  },
};
