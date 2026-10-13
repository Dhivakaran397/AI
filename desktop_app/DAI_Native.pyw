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
import webview

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROJECT_DIR = r"C:\Users\hp\Desktop\DAI"
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
LOGS_DIR = os.path.join(PROJECT_DIR, "desktop_app", ".logs")
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", PROJECT_DIR), "DAI_App_Data")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

PYTHON_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
PYTHONW_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "pythonw.exe")
NODE_EXE = r"C:\Program Files\nodejs\node.exe"
NEXT_BIN = os.path.join(FRONTEND_DIR, "node_modules", "next", "dist", "bin", "next")
ICON_PATH = os.path.join(PROJECT_DIR, "desktop_app", "dai.ico")
if not os.path.exists(ICON_PATH):
    ICON_PATH = os.path.join(PROJECT_DIR, "desktop_app", "dai_shield.ico")

APP_URL = "http://localhost:3000/chat"

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
VK_D = 0x44

ID_ALT_D = 1
ID_CTRL_ALT_D = 2
IPC_PORT = 48922

window = None
tray_icon = None
is_window_visible = True
last_toggle_time = 0.0

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
    for _ in range(20):
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
    time.sleep(10)
    while True:
        try:
            if not is_port_open(8000):
                ensure_backend()
            if not is_port_open(3000):
                ensure_frontend()
        except Exception:
            pass
        time.sleep(15)

def get_window_hwnd():
    global window
    if not window:
        return None
    try:
        if hasattr(window, "native") and window.native:
            return int(window.native.Handle.ToInt64())
    except Exception:
        pass
    return None

def show_and_focus():
    global window, is_window_visible
    if not window:
        return
    try:
        ensure_servers()
        window.show()
        window.restore()
        
        hwnd = get_window_hwnd()
        if hwnd and user32.IsWindow(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            cur_tid = kernel32.GetCurrentThreadId()
            fg_hwnd = user32.GetForegroundWindow()
            fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0
            if fg_tid and fg_tid != cur_tid:
                user32.AttachThreadInput(cur_tid, fg_tid, True)
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                user32.AttachThreadInput(cur_tid, fg_tid, False)
            else:
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
        is_window_visible = True
    except Exception:
        pass

def hide_window():
    global window, is_window_visible
    if not window:
        return
    try:
        window.hide()
        is_window_visible = False
    except Exception:
        pass

def toggle_window():
    global window, is_window_visible, last_toggle_time
    now = time.time()
    if now - last_toggle_time < 0.35:
        return
    last_toggle_time = now

    hwnd = get_window_hwnd()
    fg_hwnd = user32.GetForegroundWindow() if hwnd else None

    if is_window_visible and hwnd and (fg_hwnd == hwnd):
        hide_window()
    else:
        show_and_focus()

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
                threading.Thread(target=toggle_window, daemon=True).start()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception:
        pass

def setup_tray():
    global tray_icon
    try:
        img = Image.open(ICON_PATH)
        menu = pystray.Menu(
            pystray.MenuItem("Open DAI (Alt+D)", lambda: show_and_focus(), default=True),
            pystray.MenuItem("Toggle Window", lambda: toggle_window()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit DAI", exit_app)
        )
        tray_icon = pystray.Icon("DAI", img, "DAI - Personal AI Assistant (Alt+D)", menu)
        tray_icon.run_detached()
    except Exception:
        pass

def exit_app():
    global tray_icon, window
    if tray_icon:
        try:
            tray_icon.stop()
        except Exception:
            pass
    if window:
        try:
            window.destroy()
        except Exception:
            pass
    os._exit(0)

def on_closing():
    hide_window()
    return False

def on_loaded():
    global window
    try:
        import clr
        clr.AddReference("System.Drawing")
        import System.Drawing
        form = window.native
        form.Icon = System.Drawing.Icon(ICON_PATH)
        form.Text = "DAI"
    except Exception:
        pass

def try_focus_existing():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", IPC_PORT))
        s.sendall(b"TOGGLE\n")
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
            if data in ["SHOW", "TOGGLE"]:
                toggle_window()
        except Exception:
            break

def main():
    global window, is_window_visible

    # If instance already running, focus existing window and exit this duplicate process
    if try_focus_existing():
        sys.exit(0)

    start_minimized = "--minimized" in sys.argv

    # 1. Start backend & frontend production servers
    ensure_servers()

    # 2. Start IPC server for single-instance communication
    threading.Thread(target=ipc_server, daemon=True).start()

    # 3. Setup Windows System Tray Icon
    setup_tray()

    # 4. Setup Global Native Hotkey (Alt+D) message loop
    threading.Thread(target=hotkey_loop, daemon=True).start()

    # 5. Start background watchdog loop
    threading.Thread(target=watchdog_loop, daemon=True).start()

    # 6. Configure Native Desktop App Window
    webview.settings['ALLOW_DOWNLOADS'] = True
    webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = False

    window = webview.create_window(
        title="DAI",
        url=APP_URL,
        width=1280,
        height=840,
        min_size=(800, 600),
        text_select=True,
        zoomable=True,
        background_color="#090d16"
    )
    window.events.closing += on_closing
    window.events.loaded += on_loaded

    if start_minimized:
        is_window_visible = False
        def _hide_init():
            time.sleep(0.5)
            hide_window()
        threading.Thread(target=_hide_init, daemon=True).start()

    # Start native Windows event loop with dedicated persistent storage
    webview.start(storage_path=DATA_DIR)

if __name__ == "__main__":
    main()
