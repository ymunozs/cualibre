@echo off
REM Construye el instalador de Windows en una máquina Windows.
REM Requisitos: Python 3.12+ (python.org) e Inno Setup 6 (jrsoftware.org).
cd /d "%~dp0\..\.."

echo === Dependencias ===
python -m pip install --quiet fastapi uvicorn pymupdf python-docx python-multipart httpx pyinstaller "spacy>=3.8,<3.9" "numpy==1.26.4" https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.8.0/es_core_news_sm-3.8.0-py3-none-any.whl https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl || goto :error

echo === PyInstaller ===
python -m PyInstaller --noconfirm --clean ^
  --name "CUA-LIBRE Studio" ^
  --icon packaging\cualibre.ico ^
  --add-data "frontend;frontend" ^
  --add-data "MANUAL.md;." ^
  --add-data "backend\data_nrc_es.json;." ^
  --collect-all es_core_news_sm ^
  --collect-all en_core_web_sm ^
  run.py || goto :error

echo === Inno Setup ===
set CUALIBRE_VERSION=1.0
"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" packaging\windows\cualibre.iss || goto :error

echo.
echo OK: dist\CUA-LIBRE-Studio-1.0-windows-setup.exe
goto :eof

:error
echo FALLO la construccion (revisa el mensaje anterior)
exit /b 1
