Set WshShell = CreateObject("WScript.Shell")
PythonwPath = "C:\Users\hp\Desktop\DAI\backend\.venv\Scripts\pythonw.exe"
ScriptPath = "C:\Users\hp\Desktop\DAI\desktop_app\start_services.py"
HotkeyPath = "C:\Users\hp\Desktop\DAI\desktop_app\hotkey_listener.pyw"
WorkingDir = "C:\Users\hp\Desktop\DAI\desktop_app"

WshShell.CurrentDirectory = WorkingDir
WshShell.Run """" & PythonwPath & """ """ & ScriptPath & """", 0, False
WshShell.Run """" & PythonwPath & """ """ & HotkeyPath & """", 0, False
