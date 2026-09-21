$WshShell = New-Object -ComObject WScript.Shell
$StartupPath = [System.Environment]::GetFolderPath('Startup')
$Pythonw = "C:\Users\hp\Desktop\DAI\backend\.venv\Scripts\pythonw.exe"
$Script = "C:\Users\hp\Desktop\DAI\desktop_app\hotkey_listener.pyw"

# 1. Create start_hotkey.vbs
$VbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "`"$Pythonw`" `"$Script`"", 0, False
"@
$VbsPath = "C:\Users\hp\Desktop\DAI\desktop_app\start_hotkey.vbs"
[System.IO.File]::WriteAllText($VbsPath, $VbsContent)

# 2. Put in Windows Startup
$StartupLnk = Join-Path $StartupPath "DAI_Global_Hotkey.lnk"
$Shortcut = $WshShell.CreateShortcut($StartupLnk)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$VbsPath`""
$Shortcut.WindowStyle = 7
$Shortcut.Save()
Write-Output "Startup shortcut created: $StartupLnk"

# 3. Launch hotkey daemon right now
wscript.exe $VbsPath
Write-Output "Hotkey daemon launched and active!"
