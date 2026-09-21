import os
import sys
import subprocess
import time

edge = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
chrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
browser = edge if os.path.exists(edge) else chrome

def launch_app():
    try:
        cmd = [browser, "--app=http://localhost:3000/chat", "--window-size=1240,840"]
        subprocess.Popen(cmd)
    except Exception as e:
        pass

try:
    import keyboard
    # Global Hotkeys: Alt+Space, Alt+D, Ctrl+Alt+D
    keyboard.add_hotkey("alt+space", launch_app)
    keyboard.add_hotkey("alt+d", launch_app)
    keyboard.add_hotkey("ctrl+alt+d", launch_app)
    keyboard.wait()
except Exception as e:
    pass
