$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$StartMenuPath = [System.Environment]::GetFolderPath('Programs')
$StartupPath = [System.Environment]::GetFolderPath('Startup')

$LaunchVbs = "C:\Users\hp\Desktop\DAI\desktop_app\launch_dai.vbs"
$IconPath = "C:\Users\hp\Desktop\DAI\desktop_app\dai_shield.ico"
$WorkingDir = "C:\Users\hp\Desktop\DAI\desktop_app"

# Clean old/obsolete shortcuts
@("DAI - AI Assistant.lnk", "DAI_App.lnk", "DAI_Hotkey_Listener.lnk", "DAI_Global_Hotkey.lnk", "DAI_Companion.lnk") | ForEach-Object {
    $f1 = Join-Path $DesktopPath $_
    if (Test-Path $f1) { Remove-Item $f1 -Force }
    $f2 = Join-Path $StartMenuPath $_
    if (Test-Path $f2) { Remove-Item $f2 -Force }
    $f3 = Join-Path $StartupPath $_
    if (Test-Path $f3) { Remove-Item $f3 -Force }
}

# 1. Desktop Shortcut
$DesktopLnk = Join-Path $DesktopPath "DAI.lnk"
$s1 = $WshShell.CreateShortcut($DesktopLnk)
$s1.TargetPath = "wscript.exe"
$s1.Arguments = "`"$LaunchVbs`""
$s1.WorkingDirectory = $WorkingDir
$s1.IconLocation = "$IconPath,0"
$s1.Hotkey = ""
$s1.Description = "DAI"
$s1.WindowStyle = 1
$s1.Save()
Write-Output "Desktop shortcut updated: $DesktopLnk"

# 2. Start Menu Shortcut
$StartMenuLnk = Join-Path $StartMenuPath "DAI.lnk"
$s2 = $WshShell.CreateShortcut($StartMenuLnk)
$s2.TargetPath = "wscript.exe"
$s2.Arguments = "`"$LaunchVbs`""
$s2.WorkingDirectory = $WorkingDir
$s2.IconLocation = "$IconPath,0"
$s2.Hotkey = ""
$s2.Description = "DAI"
$s2.WindowStyle = 1
$s2.Save()
Write-Output "Start Menu shortcut updated: $StartMenuLnk"

# 3. Windows Startup Shortcut (auto-boots on Windows start)
$StartupLnk = Join-Path $StartupPath "DAI.lnk"
$s3 = $WshShell.CreateShortcut($StartupLnk)
$s3.TargetPath = "wscript.exe"
$s3.Arguments = "`"$LaunchVbs`""
$s3.WorkingDirectory = $WorkingDir
$s3.IconLocation = "$IconPath,0"
$s3.Description = "DAI"
$s3.WindowStyle = 7
$s3.Save()
Write-Output "Startup shortcut updated: $StartupLnk"

# Refresh Windows Icon Cache
$code = @'
[System.Runtime.InteropServices.DllImport("shell32.dll")]
public static extern void SHChangeNotify(int wEventId, int uFlags, System.IntPtr dwItem1, System.IntPtr dwItem2);
'@
$type = Add-Type -MemberDefinition $code -Name "Win32SHChangeNotify7" -Namespace "Win32" -PassThru
$type::SHChangeNotify(0x08000000, 0, [System.IntPtr]::Zero, [System.IntPtr]::Zero)
Write-Output "Done updating all shortcuts!"
