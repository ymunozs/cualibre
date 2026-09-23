@echo off
REM Construye el instalador de Windows en una máquina Windows.
REM Requisitos: Python 3.12+ (python.org) e Inno Setup 6 (jrsoftware.org).
cd /d "%~dp0\..\.."

echo === Dependencias ===
python -m pip install --quiet fastapi uvicorn pymupdf python-docx python-multipart httpx pyinstaller "spacy>=3.8,<3.9" "numpy==1.26.4" "pywebview>=5.3" "winrt-runtime>=2.2" "winrt-Windows.Media.Ocr>=2.2" "winrt-Windows.Graphics.Imaging>=2.2" "winrt-Windows.Storage.Streams>=2.2" "winrt-Windows.Globalization>=2.2" "winrt-Windows.Foundation>=2.2" "winrt-Windows.Foundation.Collections>=2.2" https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.8.0/es_core_news_sm-3.8.0-py3-none-any.whl https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl https://github.com/explosion/spacy-models/releases/download/pt_core_news_sm-3.8.0/pt_core_news_sm-3.8.0-py3-none-any.whl || goto :error

echo === PyInstaller ===
REM --windowed: sin consola (la app tiene ventana propia; los mensajes van a
REM %APPDATA%\cualibre\logs\cualibre.log)
python -m PyInstaller --noconfirm --clean --windowed ^
  --name "CUA-LIBRE Studio" ^
  --icon packaging\cualibre.ico ^
  --add-data "frontend;frontend" ^
  --add-data "MANUAL.md;." ^
  --add-data "MANUAL.en.md;." ^
  --add-data "MANUAL.pt.md;." ^
  --collect-all es_core_news_sm ^
  --collect-all en_core_web_sm ^
  --collect-all pt_core_news_sm ^
  --collect-all webview ^
  --collect-all winrt ^
  run.py || goto :error

echo === Inno Setup ===
set CUALIBRE_VERSION=1.12.1
"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" packaging\windows\cualibre.iss || goto :error

echo.
echo OK: dist\CUA-LIBRE-Studio-1.12.1-windows-setup.exe
goto :eof

:error
echo FALLO la construccion (revisa el mensaje anterior)
exit /b 1
