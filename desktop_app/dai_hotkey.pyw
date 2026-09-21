import sys
import os
import subprocess
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

VK_D = 0x44
VK_SPACE = 0x20

ID_ALT_D = 1
ID_CTRL_ALT_D = 2
ID_CTRL_SHIFT_SPACE = 3

SW_RESTORE = 9
SW_SHOW = 5
SW_MINIMIZE = 6

def find_dai_window():
    found_hwnd = []
    def enum_windows_callback(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.lower()
                if "dai" in title or "localhost:3000" in title:
                    found_hwnd.append(hwnd)
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
    return found_hwnd[0] if found_hwnd else None

def toggle_dai():
    hwnd = find_dai_window()
    if hwnd:
        fg_hwnd = user32.GetForegroundWindow()
        if fg_hwnd == hwnd:
            user32.ShowWindow(hwnd, SW_MINIMIZE)
        else:
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        vbs_path = os.path.join(script_dir, "open_dai_app.vbs")
        subprocess.Popen(["wscript.exe", vbs_path], shell=False)

def main():
    user32.RegisterHotKey(None, ID_ALT_D, MOD_ALT | MOD_NOREPEAT, VK_D)
    user32.RegisterHotKey(None, ID_CTRL_ALT_D, MOD_ALT | MOD_CONTROL | MOD_NOREPEAT, VK_D)
    user32.RegisterHotKey(None, ID_CTRL_SHIFT_SPACE, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_SPACE)
    
    msg = wintypes.MSG()
    WM_HOTKEY = 0x0312
    
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == WM_HOTKEY:
            toggle_dai()
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

if __name__ == "__main__":
    main()
