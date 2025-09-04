#define MyAppName        "AppGestaoTI Agent"
#define MyAppVersion     "0.1.0"
#define MyPublisher      "RabeloTech"
#define MyExeName        "appgestaoti-agent.exe"
#define MyOutputName     "AppGestaoTI-Agent-Setup-x86"
#define MyAppDir         "{autopf}\RabeloTech\AppGestaoTI\Agent"
#define MyDataRoot       "{commonappdata}\RabeloTech\AppGestaoTI\agent"
#define MyRunCmdPath     "{commonappdata}\RabeloTech\AppGestaoTI\agent\agent-run.cmd"

[Setup]
AppId={{A5F8D8D3-67C2-4B4D-8F5E-AGTI-AGENT-0001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyPublisher}
DefaultDirName={#MyAppDir}
DisableProgramGroupPage=yes
OutputDir=installer\output
OutputBaseFilename={#MyOutputName}
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x86
ArchitecturesInstallIn64BitMode=x86
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyExeName}
WizardStyle=modern
MinVersion=6.1sp1

[Files]
Source: "dist\appgestaoti-agent.exe"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{#MyDataRoot}";
Name: "{#MyDataRoot}\keys";
Name: "{#MyDataRoot}\logs";

[Icons]
Name: "{group}\{#MyAppName} - Executar (Tudo)"; Filename: "{#MyRunCmdPath}"
Name: "{group}\{#MyAppName} - Inventory agora"; Filename: "{#MyRunCmdPath}"; Parameters: "inventory"
Name: "{group}\{#MyAppName} - Metrics (1 amostra)"; Filename: "{#MyRunCmdPath}"; Parameters: "metrics"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; opcional pós-instalação
; Filename: "{#MyRunCmdPath}"; Parameters: ""; Flags: postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C schtasks /Delete /TN ""AGTI_Inventory"" /F"; Flags: runhidden; RunOnceId: "DelAGTI_Inventory"
Filename: "{cmd}"; Parameters: "/C schtasks /Delete /TN ""AGTI_Metrics"" /F";  Flags: runhidden; RunOnceId: "DelAGTI_Metrics"

[Code]
var
  PageCfg: TWizardPage;
  LUrl, LToken, LInvTime, LMetEvery, LRunAsSystem: TNewStaticText;
  EUrl, EToken, EInvTime, EMetEvery: TNewEdit;
  CbRunAsSystem: TNewCheckBox;

procedure InitializeWizard;
begin
  PageCfg := CreateCustomPage(wpSelectTasks, 'Configurar agente', 'Backend e agendamentos');

  LUrl := TNewStaticText.Create(PageCfg);
  LUrl.Parent := PageCfg.Surface;
  LUrl.Caption := 'BACKEND_URL (ex.: http://127.0.0.1:8000):';
  LUrl.Top := ScaleY(8);
  LUrl.Left := 0;

  EUrl := TNewEdit.Create(PageCfg);
  EUrl.Parent := PageCfg.Surface;
  EUrl.Top := LUrl.Top + ScaleY(16);
  EUrl.Left := 0;
  EUrl.Width := ScaleX(380);
  EUrl.Text := 'http://127.0.0.1:8000';

  LToken := TNewStaticText.Create(PageCfg);
  LToken.Parent := PageCfg.Surface;
  LToken.Caption := 'ENROLLMENT_TOKEN:';
  LToken.Top := EUrl.Top + ScaleY(32);
  LToken.Left := 0;

  EToken := TNewEdit.Create(PageCfg);
  EToken.Parent := PageCfg.Surface;
  EToken.Top := LToken.Top + ScaleY(16);
  EToken.Left := 0;
  EToken.Width := ScaleX(380);
  EToken.Text := 'TESTE_LOCAL';

  LInvTime := TNewStaticText.Create(PageCfg);
  LInvTime.Parent := PageCfg.Surface;
  LInvTime.Caption := 'Horário do INVENTORY diário (HH:MM 24h):';
  LInvTime.Top := EToken.Top + ScaleY(32);
  LInvTime.Left := 0;

  EInvTime := TNewEdit.Create(PageCfg);
  EInvTime.Parent := PageCfg.Surface;
  EInvTime.Top := LInvTime.Top + ScaleY(16);
  EInvTime.Left := 0;
  EInvTime.Width := ScaleX(80);
  EInvTime.Text := '10:00';

  LMetEvery := TNewStaticText.Create(PageCfg);
  LMetEvery.Parent := PageCfg.Surface;
  LMetEvery.Caption := 'Intervalo do METRICS (minutos):';
  LMetEvery.Top := EInvTime.Top + ScaleY(32);
  LMetEvery.Left := 0;

  EMetEvery := TNewEdit.Create(PageCfg);
  EMetEvery.Parent := PageCfg.Surface;
  EMetEvery.Top := LMetEvery.Top + ScaleY(16);
  EMetEvery.Left := 0;
  EMetEvery.Width := ScaleX(80);
  EMetEvery.Text := '5';

  LRunAsSystem := TNewStaticText.Create(PageCfg);
  LRunAsSystem.Parent := PageCfg.Surface;
  LRunAsSystem.Caption := 'Agendar tarefas como:';
  LRunAsSystem.Top := EMetEvery.Top + ScaleY(32);
  LRunAsSystem.Left := 0;

  CbRunAsSystem := TNewCheckBox.Create(PageCfg);
  CbRunAsSystem.Parent := PageCfg.Surface;
  CbRunAsSystem.Top := LRunAsSystem.Top + ScaleY(16);
  CbRunAsSystem.Left := 0;
  CbRunAsSystem.Width := ScaleX(300);
  CbRunAsSystem.Caption := 'Executar como SYSTEM (recomendado)';
  CbRunAsSystem.Checked := True;
end;

function _Quote(const S: string): string;
begin
  Result := '"' + S + '"';
end;

function _CmdContent(const AppExe, Url, Token: string): string;
var
  Lines: string;
begin
  Lines :=
    '@echo off' #13#10 +
    'setlocal' #13#10 +
    'set DATA_DIR=%ProgramData%\RabeloTech\AppGestaoTI\agent' #13#10 +
    'set BACKEND_URL=' + Url + #13#10 +
    'set ENROLL_PATH=/api/agent/enroll' #13#10 +
    'set INVENTORY_PATH=/api/agent/inventory' #13#10 +
    'set METRICS_PATH=/api/agent/metrics' #13#10 +
    'set ENROLLMENT_TOKEN=' + Token + #13#10 +
    'set DEV_MODE=0' #13#10 +
    'set ENFORCE_HTTPS=0' #13#10 +
    'set REQUIRE_DOMAIN=0' #13#10 +
    _Quote(AppExe) + ' %*' #13#10 +
    'endlocal' #13#10;
  Result := Lines;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Url, Token, InvTime, MetEvery, Ru, AppExe, CmdPath, CmdContent, Cmd, Params: string;
  Code: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    Url := EUrl.Text;
    Token := EToken.Text;
    InvTime := EInvTime.Text;
    MetEvery := EMetEvery.Text;
    Ru := 'SYSTEM';
    if not CbRunAsSystem.Checked then
      Ru := ExpandConstant('{username}');

    AppExe := ExpandConstant('{app}\{#MyExeName}');
    CmdPath := ExpandConstant('{#MyRunCmdPath}');

    CmdContent := _CmdContent(AppExe, Url, Token);
    if not SaveStringToFile(CmdPath, CmdContent, False) then
      MsgBox('Falha ao criar wrapper CMD em ' + CmdPath, mbError, MB_OK);

    // criar/atualizar tarefas agendadas
    Cmd := ExpandConstant('{cmd}');

    // INVENTORY diário
    Params := '/C schtasks /Create /TN "AGTI_Inventory" /SC DAILY /ST "' + InvTime +
      '" /TR ' + _Quote(CmdPath + ' inventory') + ' /F /RL HIGHEST /RU "' + Ru + '"';
    Exec(Cmd, Params, '', SW_HIDE, ewWaitUntilTerminated, Code);

    // METRICS a cada N minutos
    Params := '/C schtasks /Create /TN "AGTI_Metrics" /SC MINUTE /MO ' + MetEvery +
      ' /TR ' + _Quote(CmdPath + ' metrics') + ' /F /RL HIGHEST /RU "' + Ru + '"';
    Exec(Cmd, Params, '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Code: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Exec(ExpandConstant('{cmd}'), '/C schtasks /Delete /TN "AGTI_Inventory" /F', '', SW_HIDE, ewWaitUntilTerminated, Code);
    Exec(ExpandConstant('{cmd}'), '/C schtasks /Delete /TN "AGTI_Metrics" /F',  '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
end;
