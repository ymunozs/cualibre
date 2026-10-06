@echo off
REM CUA-LIBRE STUDIO en Windows desde el codigo fuente (equivalente a start.sh).
REM Este archivo es para quienes desarrollan. Para USAR la app no hace falta:
REM se descarga el instalador y se abre con doble clic.
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 goto :sin_uv
uv run run.py %*
if errorlevel 1 pause
goto :eof

:sin_uv
echo.
echo  Este archivo abre CUA-LIBRE STUDIO desde su codigo fuente y necesita
echo  una herramienta de programacion llamada "uv", que no esta en este equipo.
echo.
echo  Para usar la app NO necesitas nada de esto. Descarga el instalador:
echo.
echo      https://github.com/ymunozs/cualibre/releases/latest
echo.
echo  Elige el archivo CUA-LIBRE-Studio-windows-setup.exe y abrelo con doble clic.
echo.
echo  (Si quieres trabajar con el codigo: https://docs.astral.sh/uv/)
echo.
pause
exit /b 1
