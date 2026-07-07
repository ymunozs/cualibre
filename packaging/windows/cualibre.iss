; Instalador de Windows para CUA-LIBRE STUDIO (Inno Setup 6)
; Compilar tras PyInstaller: ISCC.exe packaging\windows\cualibre.iss

#define AppName "CUA-LIBRE Studio"
#define AppVersion GetEnv("CUALIBRE_VERSION") == "" ? "1.0" : GetEnv("CUALIBRE_VERSION")
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
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\..\dist\CUA-LIBRE Studio\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName} ahora"; Flags: nowait postinstall skipifsilent
