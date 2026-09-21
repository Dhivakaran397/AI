Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

desktopAppDir = fso.GetParentFolderName(WScript.ScriptFullName)
daiDir = fso.GetParentFolderName(desktopAppDir)
backendDir = daiDir & "\backend"
frontendDir = daiDir & "\frontend"

' 1. Check if backend is alive
On Error Resume Next
Set http8000 = CreateObject("MSXML2.ServerXMLHTTP.6.0")
http8000.setTimeouts 1000, 1000, 1000, 1000
http8000.open "GET", "http://localhost:8000/healthz", False
http8000.send
If Err.Number <> 0 Then
    WshShell.CurrentDirectory = backendDir
    WshShell.Run """" & backendDir & "\.venv\Scripts\python.exe"" -m uvicorn app.main:app --host 0.0.0.0 --port 8000", 0, False
End If
Err.Clear

' 2. Check if frontend is alive
Set http3000 = CreateObject("MSXML2.ServerXMLHTTP.6.0")
http3000.setTimeouts 1000, 1000, 1000, 1000
http3000.open "GET", "http://localhost:3000", False
http3000.send
If Err.Number <> 0 Then
    WshShell.CurrentDirectory = frontendDir
    WshShell.Run "cmd.exe /c npm run dev", 0, False
End If
Err.Clear

' 3. Open Standalone App Window (Chrome or Edge)
chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

If fso.FileExists(chromePath) Then
    WshShell.Run """" & chromePath & """ --app=http://localhost:3000/chat --window-size=1240,860", 1, False
ElseIf fso.FileExists(edgePath) Then
    WshShell.Run """" & edgePath & """ --app=http://localhost:3000/chat --window-size=1240,860", 1, False
Else
    WshShell.Run "http://localhost:3000/chat", 1, False
End If
