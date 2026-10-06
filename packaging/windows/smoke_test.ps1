# Prueba del instalador de Windows. La corre el workflow después de compilarlo;
# a mano: powershell -ExecutionPolicy Bypass -File packaging\windows\smoke_test.ps1
#
# Hace lo que haría una persona: instala sin permisos de administrador, abre la
# app instalada, importa un documento de Word antiguo (.doc), actualiza encima y
# desinstala. Luego repite todo en carpetas con espacios, tildes y ñ, como las
# de un perfil de Windows llamado «María Peña».

param(
  [string]$Setup = "dist\CUA-LIBRE-Studio-windows-setup.exe",
  [string]$Version = ""
)
$ErrorActionPreference = "Stop"

$Port = 8760
$Exe = "CUA-LIBRE Studio.exe"
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{7C4A9B12-3E5D-4F81-9A2B-CUALIBRE0001}_is1"
$Doc = (Resolve-Path (Join-Path $PSScriptRoot "..\..\backend\tests\data\entrevista.doc")).Path
$Setup = (Resolve-Path $Setup).Path
$Url = "http://127.0.0.1:$Port"

function Assert([bool]$Condition, [string]$Message) {
  if (-not $Condition) { throw "FALLO: $Message" }
  Write-Host "  ok  $Message"
}

function Install([string]$Dir) {
  $log = Join-Path $env:TEMP "cualibre-setup.log"
  $setupArgs = @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=`"$log`"")
  if ($Dir) { $setupArgs += "/DIR=`"$Dir`"" }
  $process = Start-Process -FilePath $Setup -ArgumentList $setupArgs -Wait -PassThru
  if ($process.ExitCode -ne 0) {
    Get-Content $log -Tail 40 -ErrorAction SilentlyContinue
    throw "FALLO: el instalador terminó con código $($process.ExitCode)"
  }
}

function Test-Scenario([string]$Name, [string]$Dir, [string]$DataDir) {
  Write-Host "`n=== $Name ==="
  Install $Dir
  $entry = Get-ItemProperty $UninstallKey
  $where = $entry.InstallLocation.TrimEnd("\")
  Write-Host "  instalado en: $where"
  $expected = if ($Dir) { $Dir } else { Join-Path $env:LOCALAPPDATA "Programs\CUA-LIBRE Studio" }
  Assert ($where -eq $expected) "carpeta de instalación esperada, sin pedir administrador"
  Assert (Test-Path -LiteralPath (Join-Path $where $Exe)) "el ejecutable existe"
  Assert ($entry.Publisher -eq "Yerko Muñoz-Salinas") "nombre del autor con ñ intacta («$($entry.Publisher)»)"
  if ($Version) { Assert ($entry.DisplayVersion -eq $Version) "versión $Version en «Aplicaciones instaladas»" }
  $desktop = Join-Path ([Environment]::GetFolderPath("Desktop")) "CUA-LIBRE Studio.lnk"
  $menu = Join-Path ([Environment]::GetFolderPath("Programs")) "CUA-LIBRE Studio\CUA-LIBRE Studio.lnk"
  Assert (Test-Path -LiteralPath $desktop) "acceso directo en el Escritorio"
  Assert (Test-Path -LiteralPath $menu) "acceso directo en el menú Inicio"

  # Abrir la app tal como queda instalada (ventana propia)
  $env:CUALIBRE_PORT = "$Port"
  if ($DataDir) { $env:CUALIBRE_DATA_DIR = $DataDir } else { Remove-Item Env:CUALIBRE_DATA_DIR -ErrorAction SilentlyContinue }
  $data = if ($DataDir) { $DataDir } else { Join-Path $env:APPDATA "cualibre" }
  $app = Start-Process -FilePath (Join-Path $where $Exe) -PassThru
  $mode = ""
  try {
    $info = $null
    foreach ($second in 1..150) {
      Start-Sleep -Seconds 1
      if ($app.HasExited) { break }
      try { $info = Invoke-RestMethod "$Url/api/app-info" -TimeoutSec 2; break } catch { }
    }
    Assert ($null -ne $info) "la app instalada arranca y responde"
    if ($Version) { Assert ($info.version -eq $Version) "la app dice ser la versión $Version" }
    Start-Sleep -Seconds 15  # la ventana se crea (o falla) después de que el servidor responde
    $info = Invoke-RestMethod "$Url/api/app-info"
    $mode = $info.mode
    Write-Host "  modo: $mode · OCR: $($info.ocr)"
    Assert (-not $app.HasExited) "sigue abierta 15 segundos después"

    $page = Invoke-WebRequest "$Url/" -UseBasicParsing
    Assert ($page.Content -match "CUA-LIBRE") "la interfaz se sirve desde la carpeta instalada"
    Assert ((Invoke-WebRequest "$Url/static/js/i18n.js" -UseBasicParsing).StatusCode -eq 200) "los archivos de la interfaz están completos"
    Assert ((Invoke-RestMethod "$Url/api/manual").html.Length -gt 1000) "el manual viaja en el instalador"

    # Importar un .doc (Word 97-2003): lo que pidió la usuaria
    $answer = Join-Path $env:TEMP "cualibre-doc.json"
    $status = & curl.exe -s -o $answer -w "%{http_code}" -F "file=@$Doc;filename=Entrevista 07.doc" "$Url/api/documents"
    $document = Get-Content -LiteralPath $answer -Raw -Encoding UTF8 | ConvertFrom-Json
    Assert ($status -eq "201") "importa un documento .doc (HTTP $status)"
    Assert ($document.text.Contains("pingüino del afiche")) "el texto del .doc llega con tildes y diéresis"
    Assert ($document.text.Contains("Entrevistador | ¿Cómo recuerda")) "las tablas del .doc quedan como hablante | intervención"

    # El análisis lingüístico (spaCy) también viaja dentro del instalador
    $nouns = $null
    foreach ($second in 1..90) {
      $nouns = Invoke-RestMethod "$Url/api/nlp?lang=es&pos=noun"
      if ($nouns.words) { break }
      Start-Sleep -Seconds 1
    }
    Assert ($nouns.words.Count -gt 0) "el foco gramatical funciona (modelo de lenguaje incluido)"
    Assert (Test-Path -LiteralPath (Join-Path $data "projects")) "los proyectos se guardan en $data"
  }
  finally {
    if (-not $app.HasExited) { Stop-Process -Id $app.Id -Force }
    Start-Sleep -Seconds 3
    $log = Join-Path $data "logs\cualibre.log"
    if (Test-Path -LiteralPath $log) {
      Write-Host "  --- registro de la app ---"
      Get-Content -LiteralPath $log -Tail 30 -Encoding UTF8 | ForEach-Object { Write-Host "  $_" }
    }
  }

  # Actualizar: instalar de nuevo sobre lo ya instalado
  Install $Dir
  Assert (Test-Path -LiteralPath (Join-Path $where $Exe)) "instalar encima (actualización) funciona"

  # Desinstalar: se va el programa, quedan los datos del investigador
  Start-Process -FilePath (Join-Path $where "unins000.exe") -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART" -Wait
  foreach ($second in 1..30) { if (-not (Test-Path -LiteralPath (Join-Path $where $Exe))) { break }; Start-Sleep -Seconds 1 }
  Assert (-not (Test-Path -LiteralPath (Join-Path $where $Exe))) "la desinstalación quita el programa"
  Assert (Test-Path -LiteralPath (Join-Path $data "projects")) "la desinstalación conserva los proyectos"
  return $mode
}

# (una función de PowerShell devuelve todo lo que escribe: interesa lo último, el modo)
$plain = Test-Scenario "Instalación normal" "" "" | Select-Object -Last 1
$accents = Test-Scenario "Carpetas con espacios, tildes y ñ" `
  (Join-Path $env:LOCALAPPDATA "Programs\María Peña Ñandú\CUA-LIBRE Studio") `
  (Join-Path $env:TEMP "Perfil de María Peña\cualibre") | Select-Object -Last 1

Write-Host "`nModo en instalación normal: $plain · con tildes: $accents"
Assert ($plain -eq $accents) "la ventana se comporta igual con tildes en la ruta"
if ($plain -ne "window") {
  # Este equipo no tiene WebView2: la app usó el navegador, que es lo previsto
  Write-Host "::warning::La app abrió en modo «$plain» (sin ventana propia): este equipo no tiene WebView2."
}
Write-Host "`nTODO BIEN: el instalador funciona."
