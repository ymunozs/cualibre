#!/bin/bash
# Construye el instalador de macOS: CUA-LIBRE Studio.app + DMG arrastrable.
# Requisitos: uv (las dependencias y PyInstaller se instalan solos).
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="${1:-1.0}"
APP_NAME="CUA-LIBRE Studio"

echo "▶ PyInstaller (.app)…"
uv run pyinstaller --noconfirm --clean --windowed \
  --name "$APP_NAME" \
  --icon packaging/cualibre.icns \
  --add-data "frontend:frontend" \
  --add-data "MANUAL.md:." \
  --add-data "backend/data_nrc_es.json:." \
  --collect-all es_core_news_sm \
  --collect-all en_core_web_sm \
  --osx-bundle-identifier cl.cualibre.studio \
  run.py

echo "▶ DMG…"
STAGING="$(mktemp -d)"
cp -R "dist/$APP_NAME.app" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING" -ov -format UDZO \
  "dist/CUA-LIBRE-Studio-$VERSION-mac.dmg"
rm -rf "$STAGING"

echo "✔ Listo: dist/CUA-LIBRE-Studio-$VERSION-mac.dmg"
echo "  (App sin firmar: la primera vez, clic derecho → Abrir)"
