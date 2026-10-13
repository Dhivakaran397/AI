import os
import sys
import time
import socket
import threading
import subprocess
import ctypes
from ctypes import wintypes

# 1. Bulletproof Single-Instance Check via Local Loopback Port
_singleton_sock = None
def ensure_single_instance(port=59421):
    global _singleton_sock
    try:
        _singleton_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _singleton_sock.bind(("127.0.0.1", port))
        _singleton_sock.listen(1)
        return True
    except Exception:
        return False

if not ensure_single_instance():
    sys.exit(0)

PROJECT_DIR = r"C:\Users\hp\Desktop\DAI"
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
PYTHON_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP_URL = "http://localhost:3000/chat"
DATA_DIR = r"C:\Users\hp\AppData\Local\DAI_App_Data"

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008

SW_SHOWNORMAL = 1
SW_SHOW = 5
SW_MINIMIZE = 6
SW_RESTORE = 9

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
VK_D = 0x44

ID_ALT_D = 1
ID_CTRL_ALT_D = 2

last_action = 0.0

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

def is_port_open(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def ensure_servers(wait_timeout=6):
    need_wait = False
    if not is_port_open(8000):
        need_wait = True
        subprocess.Popen(
            [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=BACKEND_DIR,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
        )
    if not is_port_open(3000):
        need_wait = True
        subprocess.Popen(
            ["npm.cmd", "run", "dev"],
            cwd=FRONTEND_DIR,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
        )
    
    if need_wait:
        # Give servers a few seconds to accept connections
        start = time.time()
        while time.time() - start < wait_timeout:
            if is_port_open(3000):
                break
            time.sleep(0.4)

def is_dai_window(hwnd):
    if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
        return False
    
    cbuff = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cbuff, 256)
    if cbuff.value != "Chrome_WidgetWin_1":
        return False

    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return False
        
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    title = buff.value.strip().lower()

    # Reject other popular tools/websites (prevents false matches with ChatGPT, etc.)
    if any(k in title for k in [
        "chatgpt", "gemini", "claude", "copilot", "antigravity",
        "visual studio", "code", "whatsapp", "linkedin", "google search"
    ]):
        return False

    import re
    if re.search(r'\bdai\b', title) or "personal ai assistant" in title or "localhost:3000" in title:
        return True

    return False

def find_dai_window():
    found_windows = []
    
    try:
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF) or user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

    def enum_cb(hwnd, _):
        if is_dai_window(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            t = buff.value.strip().lower()
            if t == "dai" or t.startswith("dai -"):
                found_windows.insert(0, hwnd)
            else:
                found_windows.append(hwnd)
        return 1

    PROC = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HWND, wintypes.LPARAM)
    user32.EnumDesktopWindows(None, PROC(enum_cb), 0)
    return found_windows[0] if found_windows else None

def force_foreground(hwnd):
    try:
        user32.ShowWindow(hwnd, SW_RESTORE)
        fg_hwnd = user32.GetForegroundWindow()
        if fg_hwnd and fg_hwnd != hwnd:
            fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
            cur_tid = kernel32.GetCurrentThreadId()
            if fg_tid != cur_tid:
                user32.AttachThreadInput(cur_tid, fg_tid, True)
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                user32.AttachThreadInput(cur_tid, fg_tid, False)
            else:
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
        else:
            user32.SetForegroundWindow(hwnd)
    except Exception:
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)

def launch_chrome_app():
    # Make sure servers are up before opening Chrome window
    ensure_servers(wait_timeout=6)
    if os.path.exists(CHROME_EXE):
        subprocess.Popen([
            CHROME_EXE,
            f"--app={APP_URL}",
            f"--user-data-dir={DATA_DIR}",
            "--window-size=1280,840"
        ])
    else:
        import webbrowser
        webbrowser.open(APP_URL)

def toggle_app():
    global last_action
    now = time.time()
    if now - last_action < 0.3:
        return
    last_action = now

    log_path = os.path.join(PROJECT_DIR, "desktop_app", "hotkey.log")
    try:
        hwnd = find_dai_window()
        fg_hwnd = user32.GetForegroundWindow()

        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] toggle_app: found_hwnd={hwnd}, fg_hwnd={fg_hwnd}\n")

        if hwnd:
            # 1. If DAI is currently active foreground window -> MINIMIZE IT!
            if fg_hwnd == hwnd:
                user32.ShowWindow(hwnd, SW_MINIMIZE)
                return

            # 2. If DAI is in background or minimized -> BRING TO FRONT!
            force_foreground(hwnd)
            return
        
        # 3. If DAI window does not exist -> LAUNCH IT!
        launch_chrome_app()
    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] toggle_app error: {e}\n")
        launch_chrome_app()

def main():
    log_path = os.path.join(PROJECT_DIR, "desktop_app", "hotkey.log")
    with open(log_path, "a", encoding="utf-8") as lf:
        lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Hotkey listener started with PID {os.getpid()}\n")
        lf.flush()

        # Register Native Windows Global Hotkeys
        reg_alt_d = user32.RegisterHotKey(None, ID_ALT_D, MOD_ALT | MOD_NOREPEAT, VK_D)
        reg_ctrl_alt_d = user32.RegisterHotKey(None, ID_CTRL_ALT_D, MOD_ALT | MOD_CONTROL | MOD_NOREPEAT, VK_D)

        lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] RegisterHotKey Alt+D={reg_alt_d}, Ctrl+Alt+D={reg_ctrl_alt_d}\n")
        lf.flush()

        if not reg_alt_d:
            lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fallback to keyboard hook\n")
            lf.flush()
            try:
                import keyboard
                keyboard.add_hotkey("alt+d", toggle_app, suppress=False)
                while True:
                    time.sleep(1)
            except Exception as e:
                lf.write(f"Keyboard fallback error: {e}\n")
            return

        lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Entering GetMessageW loop...\n")
        lf.flush()

        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        user32.GetMessageW.restype = wintypes.BOOL

        msg = wintypes.MSG()
        WM_HOTKEY = 0x0312

        try:
            while True:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0:  # WM_QUIT
                    break
                elif ret == -1:  # Error
                    break
                
                if msg.message == WM_HOTKEY:
                    lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] WM_HOTKEY received! Toggling app...\n")
                    lf.flush()
                    # Run in thread so message loop never stalls
                    threading.Thread(target=toggle_app, daemon=True).start()

                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            lf.write(f"Exception in loop: {e}\n")
            lf.flush()

if __name__ == "__main__":
    main()
