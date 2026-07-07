"""Arranque de CUA-LIBRE STUDIO: servidor local + navegador (SC-007).

Sirve también como punto de entrada de los instaladores (PyInstaller):
- importa la app directamente (sin import-string, requisito de app congelada);
- si ya hay una instancia corriendo, solo abre el navegador y termina.
"""

import sys
import threading
import time
import urllib.request
import webbrowser

import uvicorn

from backend.app import app

HOST = "127.0.0.1"
PORT = 8734
URL = f"http://{HOST}:{PORT}"


def is_running() -> bool:
    try:
        urllib.request.urlopen(URL + "/api/domains", timeout=1)
        return True
    except OSError:
        return False


def open_browser_when_ready() -> None:
    for _ in range(60):
        if is_running():
            webbrowser.open(URL)
            return
        time.sleep(0.5)


def main() -> None:
    if is_running():
        # Ya hay una instancia: reusar en lugar de chocar con el puerto
        webbrowser.open(URL)
        sys.exit(0)
    print(f"◰ CUA-LIBRE STUDIO — {URL}  (Ctrl-C para salir)")
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
