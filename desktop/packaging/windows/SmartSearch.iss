#ifndef SourceDir
  #error SourceDir must point to a fresh dotnet publish directory.
#endif
#ifndef OutputDir
  #error OutputDir must point to a fresh installer directory.
#endif
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#ifndef MyAppArch
  #define MyAppArch "x64"
#endif
#ifndef AllowedArchitectures
  #define AllowedArchitectures "x64compatible"
#endif
#ifndef InstallModeArchitectures
  #define InstallModeArchitectures "x64compatible"
#endif

[Setup]
AppId={{BE6BC4C8-605B-48DD-A4FE-11975FD7D4DD}
AppName=Smart Search
AppVersion={#MyAppVersion}
AppPublisher=Smart Search
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName=Smart Search
VersionInfoProductVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\Smart Search
DefaultGroupName=Smart Search
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
AppMutex=Local\SmartSearch.Desktop
CloseApplications=no
RestartApplications=no
ArchitecturesAllowed={#AllowedArchitectures}
ArchitecturesInstallIn64BitMode={#InstallModeArchitectures}
OutputDir={#OutputDir}
#ifdef SignedBuild
OutputBaseFilename=SmartSearch-{#MyAppVersion}-win-{#MyAppArch}-Setup-signed
SignTool=smartsearch
SignedUninstaller=yes
SignedUninstallerDir={#SignedUninstallerDirectory}
#else
OutputBaseFilename=SmartSearch-{#MyAppVersion}-win-{#MyAppArch}-Setup-unsigned-test
#endif
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=Smart Search
UninstallDisplayIcon={app}\SmartSearch.Desktop.exe
SetupIconFile={#SourceDir}\Assets\smart-search.ico

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Smart Search"; Filename: "{app}\SmartSearch.Desktop.exe"

[Run]
Filename: "{app}\SmartSearch.Desktop.exe"; Description: "Launch Smart Search"; Flags: nowait postinstall skipifsilent
