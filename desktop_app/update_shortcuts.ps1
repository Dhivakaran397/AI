$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$IconPath = "C:\Users\hp\Desktop\DAI\desktop_app\dai.ico"
$PythonwExe = "C:\Users\hp\Desktop\DAI\backend\.venv\Scripts\pythonw.exe"
$AppPyw = "C:\Users\hp\Desktop\DAI\desktop_app\DAI_App.pyw"

# 1. Update/Create Desktop Shortcut with custom AI Icon
$DesktopLnkPath = Join-Path $DesktopPath "DAI - AI Assistant.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopLnkPath)
$Shortcut.TargetPath = $PythonwExe
$Shortcut.Arguments = "`"$AppPyw`""
$Shortcut.WorkingDirectory = "C:\Users\hp\Desktop\DAI\desktop_app"
$Shortcut.Hotkey = "Ctrl+Alt+D"
$Shortcut.Description = "DAI Native AI Desktop App"
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = "$IconPath,0"
}
$Shortcut.Save()
Write-Output "Native App Desktop Shortcut created with custom AI Icon!"

# 2. Also create a direct DAI.bat on Desktop
$BatContent = @"
@echo off
start "" "$PythonwExe" "$AppPyw"
"@
$BatPath = Join-Path $DesktopPath "DAI.bat"
[System.IO.File]::WriteAllText($BatPath, $BatContent)
Write-Output "Created Desktop BAT: $BatPath"
