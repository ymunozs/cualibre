@echo off
REM CUA-LIBRE STUDIO en Windows desde el codigo fuente (equivalente a start.sh).
REM Requiere uv: https://docs.astral.sh/uv/  (el instalador .exe no lo necesita)
cd /d "%~dp0"
uv run run.py %*
