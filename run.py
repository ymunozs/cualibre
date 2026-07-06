"""Arranque de CUA-LIBRE STUDIO: servidor local + navegador (SC-007)."""

import threading
import time
import urllib.request
import webbrowser

import uvicorn

HOST = "127.0.0.1"
PORT = 8734
URL = f"http://{HOST}:{PORT}"


def open_browser_when_ready() -> None:
    for _ in range(60):
        try:
            urllib.request.urlopen(URL, timeout=1)
            webbrowser.open(URL)
            return
        except OSError:
            time.sleep(0.5)


if __name__ == "__main__":
    print(f"◰ CUA-LIBRE STUDIO — {URL}  (Ctrl-C para salir)")
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    uvicorn.run("backend.app:app", host=HOST, port=PORT, log_level="warning")
