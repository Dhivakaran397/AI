$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$StartupPath = [System.Environment]::GetFolderPath('Startup')

$PythonwExe = "C:\Users\hp\Desktop\DAI\backend\.venv\Scripts\pythonw.exe"
$AppScript = "C:\Users\hp\Desktop\DAI\desktop_app\dai_app.pyw"
$IconPath = "C:\Users\hp\Desktop\DAI\desktop_app\dai_shield.ico"
$WorkingDir = "C:\Users\hp\Desktop\DAI"

# 1. Update Desktop Shortcut
$DesktopLnk = Join-Path $DesktopPath "DAI.lnk"
if (Test-Path $DesktopLnk) {
    Remove-Item $DesktopLnk -Force -ErrorAction SilentlyContinue
}
$Shortcut1 = $WshShell.CreateShortcut($DesktopLnk)
$Shortcut1.TargetPath = $PythonwExe
$Shortcut1.Arguments = "`"$AppScript`""
$Shortcut1.WorkingDirectory = $WorkingDir
$Shortcut1.IconLocation = "$IconPath,0"
$Shortcut1.Description = "DAI AI Assistant (Ctrl+D to toggle)"
$Shortcut1.Hotkey = "Ctrl+Alt+D"
$Shortcut1.Save()
Write-Host "Updated Desktop Shortcut: $DesktopLnk with icon $IconPath"

# 2. Update Startup Shortcut
$StartupLnk = Join-Path $StartupPath "DAI.lnk"
if (Test-Path $StartupLnk) {
    Remove-Item $StartupLnk -Force -ErrorAction SilentlyContinue
}
$Shortcut2 = $WshShell.CreateShortcut($StartupLnk)
$Shortcut2.TargetPath = $PythonwExe
$Shortcut2.Arguments = "`"$AppScript`""
$Shortcut2.WorkingDirectory = $WorkingDir
$Shortcut2.IconLocation = "$IconPath,0"
$Shortcut2.Description = "DAI AI Assistant"
$Shortcut2.Save()
Write-Host "Updated Startup Shortcut: $StartupLnk"

# 3. Notify Windows Shell to refresh icon cache immediately
$code = @'
[System.Runtime.InteropServices.DllImport("shell32.dll")]
public static extern void SHChangeNotify(int wEventId, int uFlags, System.IntPtr dwItem1, System.IntPtr dwItem2);
'@
$type = Add-Type -MemberDefinition $code -Name "Win32SHChangeNotify2" -Namespace "Win32" -PassThru
$type::SHChangeNotify(0x08000000, 0, [System.IntPtr]::Zero, [System.IntPtr]::Zero)
Write-Host "Windows Shell icon cache refreshed!"
