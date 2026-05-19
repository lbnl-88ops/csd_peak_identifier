; CSD Peak Identifier Installer NSIS Script

!include "MUI2.nsh"

; General
Name "CSD Peak Identifier"
OutFile "CSD_Peak_Identifier_Installer.exe"
InstallDir "$PROGRAMFILES64\CSD Peak Identifier"
InstallDirRegKey HKLM "Software\CSDPeakIdentifier" "Install_Dir"
RequestExecutionLevel admin

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Section
Section "CSD Peak Identifier (required)"
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; Files to be installed
    File /r "dist\peak_identifier\*.*"
    
    ; Write the installation path into the registry
    WriteRegStr HKLM "Software\CSDPeakIdentifier" "Install_Dir" "$INSTDIR"
    
    ; Write the uninstall keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CSDPeakIdentifier" "DisplayName" "CSD Peak Identifier"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CSDPeakIdentifier" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CSDPeakIdentifier" "DisplayIcon" '"$INSTDIR\peak_identifier.exe"'
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CSDPeakIdentifier" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CSDPeakIdentifier" "NoRepair" 1
    WriteUninstaller "uninstall.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\CSD Peak Identifier"
    CreateShortcut "$SMPROGRAMS\CSD Peak Identifier\CSD Peak Identifier.lnk" "$INSTDIR\peak_identifier.exe" "" "$INSTDIR\peak_identifier.exe" 0
    CreateShortcut "$SMPROGRAMS\CSD Peak Identifier\Uninstall CSD Peak Identifier.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
    
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CSDPeakIdentifier"
    DeleteRegKey HKLM "Software\CSDPeakIdentifier"

    ; Remove files and uninstaller
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    Delete "$SMPROGRAMS\CSD Peak Identifier\CSD Peak Identifier.lnk"
    Delete "$SMPROGRAMS\CSD Peak Identifier\Uninstall CSD Peak Identifier.lnk"
    RMDir "$SMPROGRAMS\CSD Peak Identifier"

SectionEnd
