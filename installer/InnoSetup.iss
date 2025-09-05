#define MyAppName        "AppGestaoTI Agent"
#define MyAppVersion     "0.1.0"
#define MyAppPublisher   "RabeloTech"

[Setup]
AppId={{F33C7B36-9E25-4C1B-A7B1-7E7E2C9C1A10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\RabeloTech\AppGestaoTI\Agent
PrivilegesRequired=admin
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputBaseFilename=AppGestaoTI-Agent-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x86 x64

[Dirs]
Name: "{commonappdata}\RabeloTech\AppGestaoTI"; Permissions: users-modify

[Files]
; --- se for Windows 32 bits instala versão x86 ---
Source: "x86\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs; Check: not IsWin64
; --- se for Windows 64 bits instala versão x64 ---
Source: "x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs; Check: IsWin64

[Run]
; instala e inicia o serviço via WinSW
Filename: "{app}\winsw.exe"; Parameters: "install"; WorkingDir: "{app}"; Flags: runhidden; StatusMsg: "Registrando serviço..."
Filename: "{app}\winsw.exe"; Parameters: "start";   WorkingDir: "{app}"; Flags: runhidden; StatusMsg: "Iniciando serviço..."

[UninstallRun]
; para e remove o serviço ao desinstalar
Filename: "{app}\winsw.exe"; Parameters: "stop";      WorkingDir: "{app}"; Flags: runhidden
Filename: "{app}\winsw.exe"; Parameters: "uninstall"; WorkingDir: "{app}"; Flags: runhidden

[UninstallDelete]
; remove diretórios de dados e logs em %PROGRAMDATA%
Type: filesandordirs; Name: "{commonappdata}\RabeloTech\AppGestaoTI"
; remove também a pasta de instalação
Type: filesandordirs; Name: "{app}"