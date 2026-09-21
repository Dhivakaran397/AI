import os
import sys
import time
import socket
import subprocess
import ctypes
from ctypes import wintypes
import keyboard

user32 = ctypes.windll.user32

def is_port_open(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def find_dai_window():
    found = []
    def enum_cb(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.lower()
                if "dai" in title or "localhost:3000" in title:
                    found.append(hwnd)
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return found[0] if found else None

def bring_to_front(hwnd):
    user32.ShowWindow(hwnd, 9)
    user32.ShowWindow(hwnd, 5)
    user32.keybd_event(0x12, 0, 0, 0)
    user32.SetForegroundWindow(hwnd)
    user32.keybd_event(0x12, 0, 2, 0)

def toggle_or_launch():
    hwnd = find_dai_window()
    if hwnd:
        fg = user32.GetForegroundWindow()
        if fg == hwnd:
            user32.ShowWindow(hwnd, 6)
        else:
            bring_to_front(hwnd)
    else:
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        exe = edge_path if os.path.exists(edge_path) else chrome_path
        app_args = [
            exe,
            "--app=http://localhost:3000/chat",
            r"--user-data-dir=C:\Users\hp\AppData\Local\DAI_App",
            "--window-size=1240,840"
        ]
        subprocess.Popen(app_args)

def main():
    keyboard.add_hotkey("alt+space", toggle_or_launch, suppress=True)
    keyboard.add_hotkey("ctrl+space", toggle_or_launch, suppress=True)
    keyboard.add_hotkey("alt+d", toggle_or_launch, suppress=True)
    keyboard.add_hotkey("ctrl+alt+d", toggle_or_launch, suppress=True)
    keyboard.wait()

if __name__ == "__main__":
    main()
