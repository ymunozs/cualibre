; Instalador de Windows para CUA-LIBRE STUDIO (Inno Setup 6.3 o superior)
; Compilar tras PyInstaller: ISCC.exe packaging\windows\cualibre.iss
;
; Pensado para quien no programa: se instala para la persona que lo ejecuta, sin
; pedir permisos de administrador y sin preguntar por carpetas. Queda en
; %LOCALAPPDATA%\Programs\CUA-LIBRE Studio (otra carpeta: setup.exe /DIR="...").
;
; Este archivo se guarda en UTF-8 CON marca BOM: sin ella, las versiones de Inno
; Setup anteriores a la 6.3 leen mal la ñ y las tildes.

#define AppName "CUA-LIBRE Studio"
#define AppVersion GetEnv("CUALIBRE_VERSION")
#if AppVersion == ""
  #error Falta la variable CUALIBRE_VERSION (la definen build_windows.bat y el workflow)
#endif
#define AppExe "CUA-LIBRE Studio.exe"
#define AppUrl "https://github.com/ymunozs/cualibre"

[Setup]
AppId={{7C4A9B12-3E5D-4F81-9A2B-CUALIBRE0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Yerko Muñoz-Salinas
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}
AppUpdatesURL={#AppUrl}/releases/latest
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
; Sin páginas de carpeta ni de confirmación: elegir «Archivos de programa» sin
; ser administrador terminaba en «acceso denegado»
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
; El idioma se toma de Windows; solo se pregunta si no es ninguno de los tres
ShowLanguageDialog=auto
OutputDir=..\..\dist
; Nombre fijo, sin versión: así el enlace de descarga del README
; (releases/latest/download/...) sirve para todas las versiones
OutputBaseFilename=CUA-LIBRE-Studio-windows-setup
SetupIconFile=..\cualibre.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
; Solo Windows 10/11 de 64 bits (incluye equipos ARM, que emulan x64)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
; El instalador se muestra en el idioma de Windows (español, inglés o portugués de Brasil)
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[CustomMessages]
spanish.DesktopIcon=Crear acceso directo en el Escritorio
spanish.Shortcuts=Accesos directos:
spanish.OpenNow=Abrir %1 ahora
english.DesktopIcon=Create a desktop shortcut
english.Shortcuts=Shortcuts:
english.OpenNow=Open %1 now
brazilianportuguese.DesktopIcon=Criar atalho na Área de Trabalho
brazilianportuguese.Shortcuts=Atalhos:
brazilianportuguese.OpenNow=Abrir o %1 agora

[InstallDelete]
; Al actualizar, fuera los archivos de la versión anterior: una biblioteca
; vieja mezclada con la nueva puede impedir que la app abra
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\..\dist\CUA-LIBRE Studio\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:Shortcuts}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:OpenNow,{#AppName}}"; Flags: nowait postinstall skipifsilent
