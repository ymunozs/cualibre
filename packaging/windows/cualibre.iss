; Instalador de Windows para CUA-LIBRE STUDIO (Inno Setup 6)
; Compilar tras PyInstaller: ISCC.exe packaging\windows\cualibre.iss

#define AppName "CUA-LIBRE Studio"
#define AppVersion GetEnv("CUALIBRE_VERSION") == "" ? "1.11.0" : GetEnv("CUALIBRE_VERSION")
#define AppExe "CUA-LIBRE Studio.exe"

[Setup]
AppId={{7C4A9B12-3E5D-4F81-9A2B-CUALIBRE0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Yerko Muñoz-Salinas
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=CUA-LIBRE-Studio-{#AppVersion}-windows-setup
SetupIconFile=..\cualibre.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

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

[Files]
Source: "..\..\dist\CUA-LIBRE Studio\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:Shortcuts}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:OpenNow,{#AppName}}"; Flags: nowait postinstall skipifsilent
