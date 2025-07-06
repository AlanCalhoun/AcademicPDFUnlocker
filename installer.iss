; File: installer.iss
[Setup]
AppName=Academic PDF Unlocker
AppVersion=1.0
DefaultDirName={autopf}\AcademicPDFUnlocker
DefaultGroupName=Academic PDF Unlocker
OutputBaseFilename=AcademicPDFUnlockerSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=assets\pdf_unlocker_icon.ico
LicenseFile=license.txt

[Files]
Source: "dist\AcademicPDFUnlocker.exe"; DestDir: "{app}"; Flags: ignoreversion
; Optional: include chromedriver if needed
; Source: "path\to\chromedriver.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Academic PDF Unlocker"; Filename: "{app}\AcademicPDFUnlocker.exe"
Name: "{commondesktop}\Academic PDF Unlocker"; Filename: "{app}\AcademicPDFUnlocker.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
