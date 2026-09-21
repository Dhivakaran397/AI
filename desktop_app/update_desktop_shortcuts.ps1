$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$StartMenuPath = [System.Environment]::GetFolderPath('Programs')
$StartupPath = [System.Environment]::GetFolderPath('Startup')

$Pythonw = "C:\Users\hp\Desktop\DAI\backend\.venv\Scripts\pythonw.exe"
$AppScript = "C:\Users\hp\Desktop\DAI\desktop_app\DAI_App.pyw"
$IconPath = "C:\Users\hp\Desktop\DAI\desktop_app\dai.ico"
$WorkingDir = "C:\Users\hp\Desktop\DAI\desktop_app"

# 1. Desktop Shortcut
$DesktopLnk = Join-Path $DesktopPath "DAI - AI Assistant.lnk"
$s1 = $WshShell.CreateShortcut($DesktopLnk)
$s1.TargetPath = $Pythonw
$s1.Arguments = "`"$AppScript`""
$s1.WorkingDirectory = $WorkingDir
$s1.IconLocation = "$IconPath,0"
$s1.Hotkey = "Ctrl+Alt+D"
$s1.Description = "DAI - Personal AI Assistant"
$s1.WindowStyle = 1
$s1.Save()
Write-Output "Desktop shortcut updated: $DesktopLnk"

# 2. Start Menu Shortcut
$StartMenuLnk = Join-Path $StartMenuPath "DAI - AI Assistant.lnk"
$s2 = $WshShell.CreateShortcut($StartMenuLnk)
$s2.TargetPath = $Pythonw
$s2.Arguments = "`"$AppScript`""
$s2.WorkingDirectory = $WorkingDir
$s2.IconLocation = "$IconPath,0"
$s2.Hotkey = "Ctrl+Alt+D"
$s2.Description = "DAI - Personal AI Assistant"
$s2.WindowStyle = 1
$s2.Save()
Write-Output "Start Menu shortcut updated: $StartMenuLnk"

# 3. Windows Startup Shortcut (auto-starts on boot)
$StartupLnk = Join-Path $StartupPath "DAI_App.lnk"
$s3 = $WshShell.CreateShortcut($StartupLnk)
$s3.TargetPath = $Pythonw
$s3.Arguments = "`"$AppScript`""
$s3.WorkingDirectory = $WorkingDir
$s3.IconLocation = "$IconPath,0"
$s3.Description = "DAI AI Companion Background Daemon"
$s3.WindowStyle = 7
$s3.Save()
Write-Output "Startup shortcut updated: $StartupLnk"

# Remove legacy/old startup link if any
$OldStartup = Join-Path $StartupPath "DAI_Hotkey_Listener.lnk"
if (Test-Path $OldStartup) {
    Remove-Item $OldStartup -Force
}
$OldStartup2 = Join-Path $StartupPath "DAI_Global_Hotkey.lnk"
if (Test-Path $OldStartup2) {
    Remove-Item $OldStartup2 -Force
}
