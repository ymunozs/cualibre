"""Arranque de CUA-LIBRE STUDIO: servidor local + ventana propia (SC-007, FR-081).

Sirve también como punto de entrada de los instaladores (PyInstaller):
- importa la app directamente (sin import-string, requisito de app congelada);
- abre la interfaz en una ventana propia (WKWebView en Mac, WebView2 en
  Windows). Si el sistema no puede crearla (p. ej., un Windows sin el runtime
  WebView2), usa el navegador de siempre, con un botón SALIR en la cabecera;
- `--navegador` (o CUALIBRE_BROWSER=1) fuerza el modo navegador;
- `--servidor` levanta solo el servidor, sin ventana ni navegador, y
  CUALIBRE_PORT fija el puerto: así se prueban los instaladores (packaging/);
- si ya hay una instancia corriendo, la reutiliza en vez de levantar otra;
- si el puerto 8734 está tomado por OTRO programa (o reservado: en Windows,
  Hyper-V/WSL reservan rangos de puertos y el bind falla con WinError 10013),
  usa el siguiente puerto libre en vez de cerrarse sin avisar.
"""

import json
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

HOST = "127.0.0.1"
PORTS = range(8734, 8744)
TITLE = "CUA-LIBRE STUDIO"


def _redirect_output_if_windowed() -> None:
    """App sin consola (Windows --windowed): stdout/stderr son None y el
    primer mensaje de log haría caer la app. Se redirigen a un archivo en la
    carpeta de datos, útil además para diagnosticar problemas."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    from backend import storage

    log_dir = storage.base_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stream = open(log_dir / "cualibre.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or stream
    sys.stderr = sys.stderr or stream


_redirect_output_if_windowed()

import uvicorn  # noqa: E402

from backend.app import app  # noqa: E402


def url_for(port: int) -> str:
    return f"http://{HOST}:{port}"


def is_cualibre(port: int) -> bool:
    """¿Responde una instancia de Cua-libre en ese puerto?"""
    try:
        with urllib.request.urlopen(url_for(port) + "/api/version", timeout=1) as r:
            return "version" in json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError):
        return False


def is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, port))
            return True
        except OSError:
            return False


def wait_until_ready(port: int, seconds: float = 30) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if is_cualibre(port):
            return True
        time.sleep(0.25)
    return False


def window_engine_ok() -> bool:
    """En Windows, si falta el componente WebView2, pywebview recurre sin
    avisar al motor de Internet Explorer, donde la interfaz no funciona (queda
    una ventana en blanco). En ese caso es mejor el navegador."""
    if sys.platform != "win32":
        return True
    from webview.platforms import winforms

    return getattr(winforms, "renderer", "") == "edgechromium"


def open_window(url: str) -> bool:
    """Ventana propia; devuelve False si el sistema no pudo crearla."""
    try:
        import webview
        from backend import storage

        if not window_engine_ok():
            raise RuntimeError("falta el componente WebView2 de Windows")
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True  # GitHub, Ko-fi, DOI
        window = webview.create_window(
            TITLE, url, width=1440, height=920, min_size=(900, 600),
            text_select=True,  # imprescindible: codificar ES seleccionar texto
            zoomable=True, background_color="#FAFAFA",
        )
        app.state.window = window
        app.state.mode = "window"
        # private_mode=False + carpeta propia: idioma, modo oscuro y posición de
        # lectura (localStorage) sobreviven entre sesiones
        storage_path = storage.base_dir() / "webview"
        storage_path.mkdir(parents=True, exist_ok=True)
        webview.start(private_mode=False, storage_path=str(storage_path))
        return True
    except Exception as exc:  # sin WebView2, sin pyobjc, etc.
        print(f"[cualibre] ventana propia no disponible ({exc!r}); se usa el navegador")
        app.state.window = None
        return False


def main() -> None:
    use_browser = "--navegador" in sys.argv or "--browser" in sys.argv \
        or os.environ.get("CUALIBRE_BROWSER") == "1"
    server_only = "--servidor" in sys.argv or "--server" in sys.argv
    fixed_port = os.environ.get("CUALIBRE_PORT")
    ports = [int(fixed_port)] if fixed_port else PORTS

    for port in ports:
        if is_cualibre(port) and not server_only:
            # Ya hay una instancia (con su ventana): se reutiliza en el navegador,
            # sin levantar un segundo servidor que compita por el mismo proyecto
            webbrowser.open(url_for(port))
            sys.exit(0)

    port = next((p for p in ports if is_free(p)), None)
    if port is None:
        print(f"✖ CUA-LIBRE STUDIO: no hay puertos libres entre {ports[0]} y {ports[-1]}.")
        sys.exit(1)

    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=port, log_level="warning"))
    app.state.shutdown = lambda: setattr(server, "should_exit", True)
    print(f"◰ {TITLE} · {url_for(port)}  (Ctrl-C para salir)")

    if server_only:
        server.run()
        return

    if not use_browser:
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        if wait_until_ready(port) and open_window(url_for(port)):
            server.should_exit = True  # se cerró la ventana: se apaga todo
            thread.join(timeout=5)
            return
        # La ventana no pudo abrirse: el servidor sigue, ahora con el navegador
        app.state.mode = "browser"
        webbrowser.open(url_for(port))
        thread.join()
        return

    app.state.mode = "browser"
    threading.Thread(target=lambda: wait_until_ready(port) and webbrowser.open(url_for(port)),
                     daemon=True).start()
    server.run()


if __name__ == "__main__":
    main()
