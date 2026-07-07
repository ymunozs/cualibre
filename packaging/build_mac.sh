#!/bin/bash
# Construye el instalador de macOS: CUA-LIBRE Studio.app + DMG arrastrable.
# Requisitos: uv (las dependencias y PyInstaller se instalan solos).
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="${1:-1.0}"
APP_NAME="CUA-LIBRE Studio"

# Piso real de compatibilidad, verificado con otool -l sobre los binarios
# compilados (numpy/thinc/blis/pymupdf/Python): macOS 10.15 Catalina.
# numpy>=2 exige macOS 14+ (Sonoma) — por eso se fija <2 en pyproject.toml.
MACOS_MIN="10.15"

echo "▶ PyInstaller (.app)…"
MACOSX_DEPLOYMENT_TARGET="$MACOS_MIN" uv run pyinstaller --noconfirm --clean --windowed \
  --name "$APP_NAME" \
  --icon packaging/cualibre.icns \
  --add-data "frontend:frontend" \
  --add-data "MANUAL.md:." \
  --add-data "backend/data_nrc_es.json:." \
  --collect-all es_core_news_sm \
  --collect-all en_core_web_sm \
  --osx-bundle-identifier cl.cualibre.studio \
  run.py

echo "▶ Declarando compatibilidad mínima (macOS $MACOS_MIN) en Info.plist…"
plutil -replace LSMinimumSystemVersion -string "$MACOS_MIN" "dist/$APP_NAME.app/Contents/Info.plist"

# El binario resultante SOLO corre en la arquitectura donde se compiló
# (PyInstaller empaqueta las wheels nativas ya instaladas, de un solo arco).
# Cada DMG debe nombrarse según su arquitectura real — verificado con lipo,
# nunca asumido — para no distribuir un arm64 a quien tiene Intel o viceversa.
ARCH="$(lipo -archs "dist/$APP_NAME.app/Contents/MacOS/$APP_NAME")"
case "$ARCH" in
  arm64)  TAG="mac-applesilicon" ;;
  x86_64) TAG="mac-intel" ;;
  *) echo "⚠ Arquitectura inesperada: $ARCH — abortando para no publicar un DMG mal etiquetado"; exit 1 ;;
esac

echo "▶ DMG ($ARCH → $TAG)…"
STAGING="$(mktemp -d)"
cp -R "dist/$APP_NAME.app" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING" -ov -format UDZO \
  "dist/CUA-LIBRE-Studio-$VERSION-$TAG.dmg"
rm -rf "$STAGING"

echo "✔ Listo: dist/CUA-LIBRE-Studio-$VERSION-$TAG.dmg"
echo "  (App sin firmar: la primera vez, clic derecho → Abrir)"
