import os
import sys
import time
import socket
import threading
import subprocess
import ctypes
from ctypes import wintypes
from PIL import Image
import pystray

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROJECT_DIR = r"C:\Users\hp\Desktop\DAI"
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
LOGS_DIR = os.path.join(PROJECT_DIR, "desktop_app", ".logs")
DATA_DIR = os.path.join(r"C:\Users\hp\AppData\Local", "DAI_App_Data")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

PYTHON_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
PYTHONW_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "pythonw.exe")
NODE_EXE = r"C:\Program Files\nodejs\node.exe"
NEXT_BIN = os.path.join(FRONTEND_DIR, "node_modules", "next", "dist", "bin", "next")
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ICON_PATH = os.path.join(PROJECT_DIR, "desktop_app", "dai.ico")
if not os.path.exists(ICON_PATH):
    ICON_PATH = os.path.join(PROJECT_DIR, "desktop_app", "dai_shield.ico")

APP_URL = "http://localhost:3000/chat"

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
IPC_PORT = 48922

tray_icon = None
last_action_time = 0.0

def is_port_open(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def ensure_backend():
    if is_port_open(8000):
        return True
    log_f = open(os.path.join(LOGS_DIR, "backend.log"), "a", encoding="utf-8")
    subprocess.Popen(
        [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdin=subprocess.DEVNULL,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
    )
    for _ in range(25):
        time.sleep(0.3)
        if is_port_open(8000):
            return True
    return False

def ensure_frontend():
    if is_port_open(3000):
        return True
    log_f = open(os.path.join(LOGS_DIR, "frontend.log"), "a", encoding="utf-8")
    prod_build = os.path.join(FRONTEND_DIR, ".next")
    node_cmd = NODE_EXE if os.path.exists(NODE_EXE) else "node"
    if os.path.exists(prod_build):
        cmd = [node_cmd, NEXT_BIN, "start", "-p", "3000"]
    else:
        cmd = [node_cmd, NEXT_BIN, "dev", "-p", "3000"]

    subprocess.Popen(
        cmd,
        cwd=FRONTEND_DIR,
        stdin=subprocess.DEVNULL,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
    )
    for _ in range(30):
        time.sleep(0.3)
        if is_port_open(3000):
            return True
    return False

def ensure_servers():
    t_be = threading.Thread(target=ensure_backend, daemon=True)
    t_fe = threading.Thread(target=ensure_frontend, daemon=True)
    t_be.start()
    t_fe.start()
    t_be.join(timeout=8)
    t_fe.join(timeout=10)

def watchdog_loop():
    time.sleep(15)
    while True:
        try:
            if not is_port_open(8000):
                ensure_backend()
            if not is_port_open(3000):
                ensure_frontend()
        except Exception:
            pass
        time.sleep(15)

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

    if any(k in title for k in [
        "chatgpt", "gemini", "claude", "copilot", "antigravity",
        "visual studio", "code", "whatsapp", "linkedin", "google search"
    ]):
        return False

    if (
        title == "dai"
        or title.startswith("dai -")
        or title.startswith("dai ")
        or title.endswith("| dai")
        or "personal ai assistant" in title
        or "localhost:3000" in title
    ):
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

def launch_app_window():
    ensure_servers()
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

def toggle_or_focus(force_open=False):
    global last_action_time
    now = time.time()
    if now - last_action_time < 0.35:
        return
    last_action_time = now

    hwnd = find_dai_window()
    fg_hwnd = user32.GetForegroundWindow() if hwnd else None

    if hwnd:
        if force_open:
            force_foreground(hwnd)
        elif fg_hwnd == hwnd:
            user32.ShowWindow(hwnd, SW_MINIMIZE)
        else:
            force_foreground(hwnd)
    else:
        launch_app_window()

def hotkey_loop():
    user32.RegisterHotKey(None, ID_ALT_D, MOD_ALT | MOD_NOREPEAT, VK_D)
    user32.RegisterHotKey(None, ID_CTRL_ALT_D, MOD_ALT | MOD_CONTROL | MOD_NOREPEAT, VK_D)

    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = wintypes.BOOL

    msg = wintypes.MSG()
    WM_HOTKEY = 0x0312

    try:
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            if msg.message == WM_HOTKEY:
                threading.Thread(target=toggle_or_focus, args=(False,), daemon=True).start()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception:
        pass

def try_focus_existing():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", IPC_PORT))
        s.sendall(b"OPEN\n")
        s.close()
        return True
    except Exception:
        return False

def ipc_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", IPC_PORT))
        s.listen(5)
    except Exception:
        return

    while True:
        try:
            conn, _ = s.accept()
            data = conn.recv(1024).decode().strip()
            conn.close()
            if data == "OPEN":
                threading.Thread(target=toggle_or_focus, args=(True,), daemon=True).start()
            elif data == "TOGGLE":
                threading.Thread(target=toggle_or_focus, args=(False,), daemon=True).start()
        except Exception:
            break

def setup_tray():
    global tray_icon
    try:
        img = Image.open(ICON_PATH)
        menu = pystray.Menu(
            pystray.MenuItem("Open DAI (Alt+D)", lambda: toggle_or_focus(force_open=True), default=True),
            pystray.MenuItem("Toggle Window", lambda: toggle_or_focus(force_open=False)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit DAI", exit_app)
        )
        tray_icon = pystray.Icon("DAI", img, "DAI - Personal AI Assistant (Alt+D)", menu)
        tray_icon.run()
    except Exception:
        pass

def exit_app():
    global tray_icon
    if tray_icon:
        try:
            tray_icon.stop()
        except Exception:
            pass
    hwnd = find_dai_window()
    if hwnd:
        user32.PostMessageW(hwnd, 0x0010, 0, 0) # WM_CLOSE
    os._exit(0)

def main():
    # If instance already running, tell it to open and exit
    if try_focus_existing():
        sys.exit(0)

    start_minimized = "--minimized" in sys.argv

    # 1. Start servers in background
    ensure_servers()

    # 2. Start IPC listener
    threading.Thread(target=ipc_server, daemon=True).start()

    # 3. Start Hotkey loop
    threading.Thread(target=hotkey_loop, daemon=True).start()

    # 4. Start Watchdog loop
    threading.Thread(target=watchdog_loop, daemon=True).start()

    # 5. If not starting minimized (e.g. user clicked icon), open window
    if not start_minimized:
        threading.Thread(target=launch_app_window, daemon=True).start()

    # 6. Run tray icon on main thread
    setup_tray()

if __name__ == "__main__":
    main()
