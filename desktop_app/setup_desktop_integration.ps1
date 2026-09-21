$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$StartupPath = [System.Environment]::GetFolderPath('Startup')
$ScriptDir = "C:\Users\hp\Desktop\DAI\desktop_app"
$VbsLauncher = Join-Path $ScriptDir "open_dai_app.vbs"
$HotkeyScript = Join-Path $ScriptDir "dai_hotkey.pyw"
$PythonwExe = "C:\Users\hp\Desktop\DAI\backend\.venv\Scripts\pythonw.exe"
if (-not (Test-Path $PythonwExe)) {
    $PythonwExe = "pythonw.exe"
}

# 1. Create Desktop Shortcut with native Windows Hotkey (Ctrl+Alt+D)
$DesktopLnkPath = Join-Path $DesktopPath "DAI - AI Assistant.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopLnkPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$VbsLauncher`""
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.Hotkey = "Ctrl+Alt+D"
$Shortcut.Description = "DAI Autonomous AI Assistant (Hotkey: Alt+D / Ctrl+Alt+D)"

# Use Chrome or Edge icon if available
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$EdgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if (Test-Path $ChromePath) {
    $Shortcut.IconLocation = "$ChromePath,0"
} elseif (Test-Path $EdgePath) {
    $Shortcut.IconLocation = "$EdgePath,0"
}
$Shortcut.Save()
Write-Output "Created Desktop Shortcut: $DesktopLnkPath (Hotkey: Ctrl+Alt+D)"

# 2. Create Startup Shortcut to automatically run hotkey listener on laptop boot
$StartupLnkPath = Join-Path $StartupPath "DAI_Hotkey_Listener.lnk"
$StartupShortcut = $WshShell.CreateShortcut($StartupLnkPath)
$StartupShortcut.TargetPath = $PythonwExe
$StartupShortcut.Arguments = "`"$HotkeyScript`""
$StartupShortcut.WorkingDirectory = $ScriptDir
$StartupShortcut.WindowStyle = 7 # Minimized
$StartupShortcut.Save()
Write-Output "Added to Windows Startup: $StartupLnkPath"

# 3. Launch the hotkey listener right now silently
Start-Process -FilePath $PythonwExe -ArgumentList "`"$HotkeyScript`"" -WindowStyle Hidden
Write-Output "DAI Hotkey Listener is now ACTIVE in background!"
