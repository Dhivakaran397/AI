$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')

$ChromeExe = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$IconPath = "C:\Users\hp\Desktop\DAI\desktop_app\dai_shield.ico"
$WorkingDir = "C:\Users\hp\Desktop\DAI"
$LnkPath = Join-Path $DesktopPath "DAI.lnk"

if (Test-Path $LnkPath) {
    Remove-Item $LnkPath -Force -ErrorAction SilentlyContinue
}

$Shortcut = $WshShell.CreateShortcut($LnkPath)
$Shortcut.TargetPath = $ChromeExe
$Shortcut.Arguments = "--app=http://localhost:3000/chat"
$Shortcut.WorkingDirectory = $WorkingDir
$Shortcut.IconLocation = "$IconPath,0"
$Shortcut.Description = "DAI AI Assistant - Personal Intelligence & Project Builder"
$Shortcut.Hotkey = "Ctrl+Alt+D"
$Shortcut.Save()

Write-Host "Configured DAI.lnk successfully pointing directly to Chrome app mode with dai_shield.ico!"

# Refresh Windows Icon cache
$code = @'
[System.Runtime.InteropServices.DllImport("shell32.dll")]
public static extern void SHChangeNotify(int wEventId, int uFlags, System.IntPtr dwItem1, System.IntPtr dwItem2);
'@
$type = Add-Type -MemberDefinition $code -Name "Win32SHChangeNotify3" -Namespace "Win32" -PassThru
$type::SHChangeNotify(0x08000000, 0, [System.IntPtr]::Zero, [System.IntPtr]::Zero)
Write-Host "Windows Shell notified of icon update!"
