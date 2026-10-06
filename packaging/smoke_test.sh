#!/bin/bash
# Prueba de la app empaquetada (macOS): la levanta sin ventana ni navegador,
# con datos temporales, e importa un documento de Word antiguo (.doc).
# Uso: packaging/smoke_test.sh ["dist/CUA-LIBRE Studio.app"]
set -euo pipefail
cd "$(dirname "$0")/.."

APP="${1:-dist/CUA-LIBRE Studio.app}"
BIN="$APP/Contents/MacOS/CUA-LIBRE Studio"
PORT=8760
URL="http://127.0.0.1:$PORT"
DATA="$(mktemp -d)/Datos de María Peña/cualibre"   # espacios, tildes y ñ en la ruta
VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)"

fail() { echo "FALLO: $1"; exit 1; }
ok() { echo "  ok  $1"; }

CUALIBRE_PORT=$PORT CUALIBRE_DATA_DIR="$DATA" "$BIN" --servidor &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT

for _ in $(seq 1 120); do
  curl -sf "$URL/api/app-info" >/dev/null 2>&1 && break
  kill -0 $PID 2>/dev/null || fail "la app se cerró al arrancar"
  sleep 1
done
INFO="$(curl -sf "$URL/api/app-info")" || fail "la app empaquetada no responde"
echo "  $INFO"
[[ "$INFO" == *"\"version\":\"$VERSION\""* ]] || fail "la app no dice ser la versión $VERSION"
ok "arranca y dice ser la versión $VERSION"

curl -sf "$URL/" | grep -q "CUA-LIBRE" || fail "no se sirve la interfaz"
ok "la interfaz viaja dentro de la app"
[[ "$(curl -sf "$URL/api/manual" | wc -c)" -gt 1000 ]] || fail "falta el manual"
ok "el manual viaja dentro de la app"

TEXT="$(curl -sf -F "file=@backend/tests/data/entrevista.doc;filename=Entrevista 07.doc" "$URL/api/documents")" \
  || fail "no importó el .doc"
[[ "$TEXT" == *"pingüino del afiche"* ]] || fail "el texto del .doc llegó sin tildes o incompleto"
[[ "$TEXT" == *"Entrevistador | ¿Cómo recuerda"* ]] || fail "las tablas del .doc no quedaron como hablante | intervención"
ok "importa un .doc con tildes y tablas"

for _ in $(seq 1 90); do
  NOUNS="$(curl -sf "$URL/api/nlp?lang=es&pos=noun" || true)"
  [[ "$NOUNS" == *'"word"'* ]] && break
  sleep 1
done
[[ "$NOUNS" == *'"word"'* ]] || fail "el foco gramatical no respondió (¿falta el modelo de lenguaje?)"
ok "el foco gramatical funciona (modelo de lenguaje incluido)"
[[ -d "$DATA/projects" ]] || fail "no se guardó el proyecto en la carpeta de datos"
ok "guarda en una carpeta con espacios, tildes y ñ"

curl -sf -X POST -H "Content-Type: application/json" -d '{"confirm": true}' "$URL/api/app/quit" >/dev/null
for _ in $(seq 1 20); do kill -0 $PID 2>/dev/null || break; sleep 0.5; done
kill -0 $PID 2>/dev/null && fail "la app no se cerró al pedírselo"
ok "se cierra limpiamente"
echo "TODO BIEN: la app empaquetada funciona."
