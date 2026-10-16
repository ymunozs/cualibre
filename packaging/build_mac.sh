#!/bin/bash
# Construye el instalador de macOS: CUA-LIBRE Studio.app + DMG arrastrable.
# Requisitos: uv (las dependencias y PyInstaller se instalan solos).
set -euo pipefail
cd "$(dirname "$0")/.."

# La versión sale de pyproject.toml: un solo lugar que actualizar
VERSION="${1:-$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)}"
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
  --add-data "MANUAL.en.md:." \
  --add-data "MANUAL.pt.md:." \
  --add-data "LICENSE:." \
  --add-data "AVISOS-DE-TERCEROS.md:." \
  --add-data "licencias:licencias" \
  --collect-all es_core_news_sm \
  --collect-all en_core_web_sm \
  --collect-all pt_core_news_sm \
  --collect-all webview \
  --hidden-import Vision \
  --osx-bundle-identifier cl.cualibre.studio \
  run.py

echo "▶ Declarando versión $VERSION y compatibilidad mínima (macOS $MACOS_MIN) en Info.plist…"
plutil -replace LSMinimumSystemVersion -string "$MACOS_MIN" "dist/$APP_NAME.app/Contents/Info.plist"
plutil -replace CFBundleShortVersionString -string "$VERSION" "dist/$APP_NAME.app/Contents/Info.plist"
plutil -replace CFBundleVersion -string "$VERSION" "dist/$APP_NAME.app/Contents/Info.plist"

# CRÍTICO: PyInstaller ya firmó el bundle (ad-hoc) al construirlo. Tocar el
# Info.plist DESPUÉS invalida esa firma ("invalid Info.plist (plist or
# signature have been modified)", verificable con codesign --verify) — y
# eso es justo lo que Gatekeeper reporta como "app dañada, muévela a la
# papelera" en vez del aviso normal de "desarrollador no identificado".
# Hay que volver a firmar (ad-hoc) después de cualquier cambio al bundle.
echo "▶ Re-firmando (ad-hoc) tras modificar Info.plist…"
codesign --force --deep --sign - "dist/$APP_NAME.app"
codesign --verify --deep --strict "dist/$APP_NAME.app"
echo "  ✔ Firma ad-hoc válida"

echo "▶ Probando la app empaquetada (arranca, importa un .doc, guarda)…"
./packaging/smoke_test.sh "dist/$APP_NAME.app"

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

# Nombre fijo, sin versión: así los enlaces de descarga del README
# (releases/latest/download/…) sirven para todas las versiones.
DMG="dist/CUA-LIBRE-Studio-$TAG.dmg"
echo "▶ DMG ($ARCH → $TAG, versión $VERSION)…"
STAGING="$(mktemp -d)"
cp -R "dist/$APP_NAME.app" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING" -ov -format UDZO "$DMG"
rm -rf "$STAGING"

echo "✔ Listo: $DMG (versión $VERSION)"
echo "  (App sin firma de Apple: la primera vez hay que autorizarla, ver README)"
