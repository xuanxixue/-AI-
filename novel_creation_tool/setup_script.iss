
; 小说创作辅助工具安装脚本
[Setup]
AppName=小说创作辅助工具
AppVersion=1.0.0
DefaultDirName={autopf}\小说创作辅助工具
DefaultGroupName=小说创作辅助工具
OutputBaseFilename=小说创作辅助工具安装程序
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
OutputDir=.

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\NovelCreationTool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\小说创作辅助工具"; Filename: "{app}\NovelCreationTool.exe"
Name: "{commondesktop}\小说创作辅助工具"; Filename: "{app}\NovelCreationTool.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "在桌面创建快捷方式"; GroupDescription: "附加任务："

[Run]
Filename: "{app}\NovelCreationTool.exe"; Description: "启动小说创作辅助工具"; Flags: nowait postinstall skipifsilent
