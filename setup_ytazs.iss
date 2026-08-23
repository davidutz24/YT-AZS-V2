[Setup]
AppName=YT AZS
AppVersion=12.0
AppId={{65A83D2B-0A45-4B52-9F58-2E548F6D9D1A}
AppPublisher=David Marica - AZS Gherla
AppPublisherURL=https://www.azsgherla.ro
DefaultDirName={autopf}\YT AZS
DefaultGroupName=YT AZS
OutputDir=installer
OutputBaseFilename=YT-AZS-Setup-V12.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UsePreviousAppDir=yes
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\YT-AZS.exe
PrivilegesRequired=lowest

[Languages]
Name: "ro"; MessagesFile: "compiler:Languages\Romanian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Creaza o pictograma pe Desktop"; GroupDescription: "Pictograme aditionale:"

[Files]
Source: "dist\YT-AZS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\YT AZS"; Filename: "{app}\YT-AZS.exe"
Name: "{group}\Dezinstaleaza YT AZS"; Filename: "{uninstallexe}"
Name: "{commondesktop}\YT AZS"; Filename: "{app}\YT-AZS.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\YT-AZS.exe"; Description: "Porneste YT AZS V12"; Flags: nowait postinstall skipifsilent
