import sys
import os
import subprocess
import time
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

MUTEX_NAME = "Global_DAI_Hotkey_Daemon_Mutex_v2"
mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    sys.exit(0)

SW_RESTORE = 9
SW_SHOW = 5
SW_MINIMIZE = 6

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPEN_VBS = os.path.join(SCRIPT_DIR, "open_dai_app.vbs")

def find_dai_window():
    target_hwnds = []

    def enum_cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.lower()
                
                # Exclude editor and console windows
                class_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_buff, 256)
                cls_name = class_buff.value
                if cls_name in ["ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS"]:
                    return True

                if (("dai" in title and ("intelligence" in title or "project" in title or "chat" in title or "builder" in title))
                        or "localhost:3000" in title
                        or title.startswith("dai —")
                        or title.startswith("dai -")):
                    target_hwnds.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return target_hwnds[0] if target_hwnds else None

def force_foreground_window(hwnd):
    try:
        fg_hwnd = user32.GetForegroundWindow()
        fore_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
        app_thread = kernel32.GetCurrentThreadId()

        if fore_thread != app_thread:
            user32.AttachThreadInput(fore_thread, app_thread, True)
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            user32.AttachThreadInput(fore_thread, app_thread, False)
        else:
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

_last_toggle = 0

def toggle_dai():
    global _last_toggle
    now = time.time()
    if now - _last_toggle < 0.4:
        return
    _last_toggle = now

    try:
        hwnd = find_dai_window()
        if hwnd:
            fg_hwnd = user32.GetForegroundWindow()
            if fg_hwnd == hwnd:
                user32.ShowWindow(hwnd, SW_MINIMIZE)
            else:
                force_foreground_window(hwnd)
        else:
            subprocess.Popen(["wscript.exe", OPEN_VBS], shell=False)
    except Exception:
        pass

def run_win32_hotkeys():
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_NOREPEAT = 0x4000
    VK_D = 0x44
    VK_SPACE = 0x20

    user32.RegisterHotKey(None, 1, MOD_ALT | MOD_NOREPEAT, VK_D)
    user32.RegisterHotKey(None, 2, MOD_CONTROL | MOD_NOREPEAT, VK_SPACE)
    user32.RegisterHotKey(None, 3, MOD_ALT | MOD_CONTROL | MOD_NOREPEAT, VK_D)
    user32.RegisterHotKey(None, 4, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_D)
    user32.RegisterHotKey(None, 5, MOD_ALT | MOD_NOREPEAT, VK_SPACE)

    msg = wintypes.MSG()
    WM_HOTKEY = 0x0312
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == WM_HOTKEY:
            toggle_dai()
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

def main():
    try:
        import keyboard
        # Register both Alt+Space and Ctrl+Space, plus Alt+D and Ctrl+Alt+D
        keyboard.add_hotkey("alt+space", toggle_dai, suppress=False)
        keyboard.add_hotkey("ctrl+space", toggle_dai, suppress=False)
        keyboard.add_hotkey("alt+d", toggle_dai, suppress=False)
        keyboard.add_hotkey("ctrl+alt+d", toggle_dai, suppress=False)
        keyboard.add_hotkey("ctrl+shift+d", toggle_dai, suppress=False)
        keyboard.wait()
    except Exception:
        run_win32_hotkeys()

if __name__ == "__main__":
    main()
