Set WshShell = CreateObject("WScript.Shell")
PythonwPath = "C:\Users\hp\Desktop\DAI\backend\.venv\Scripts\pythonw.exe"
ScriptPath = "C:\Users\hp\Desktop\DAI\desktop_app\DAI_Native.pyw"
WorkingDir = "C:\Users\hp\Desktop\DAI\desktop_app"

WshShell.CurrentDirectory = WorkingDir
Command = """" & PythonwPath & """ """ & ScriptPath & """"
WshShell.Run Command, 0, False
