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
PYTHON_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
PYTHONW_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "pythonw.exe")
ICON_PATH = os.path.join(PROJECT_DIR, "desktop_app", "dai_shield.ico")
STORAGE_DIR = os.path.join(PROJECT_DIR, "desktop_app", ".webview_storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

IPC_PORT = 48921

window = None
tray_icon = None
is_window_visible = True
last_toggle_time = 0.0

def is_port_open(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def ensure_servers_running():
    # Check backend
    if not is_port_open(8000):
        py = PYTHONW_EXE if os.path.exists(PYTHONW_EXE) else "python"
        subprocess.Popen(
            [py, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=BACKEND_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
    # Check frontend
    if not is_port_open(3000):
        subprocess.Popen(
            ["npm.cmd", "run", "dev"],
            cwd=FRONTEND_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )

def get_window_hwnd():
    global window
    if not window or not window.native:
        return None
    try:
        return int(window.native.Handle.ToInt64())
    except Exception:
        return None

def is_window_foreground():
    hwnd = get_window_hwnd()
    if not hwnd:
        return False
    return user32.GetForegroundWindow() == hwnd

def show_and_focus():
    global window, is_window_visible
    if not window:
        return
    try:
        window.show()
        window.restore()
        hwnd = get_window_hwnd()
        if hwnd:
            user32.ShowWindow(hwnd, 9) # SW_RESTORE
            user32.keybd_event(0x12, 0, 0, 0)
            user32.SetForegroundWindow(hwnd)
            user32.keybd_event(0x12, 0, 2, 0)
        is_window_visible = True
    except Exception as e:
        print("Show error:", e)

def hide_or_minimize():
    global window, is_window_visible
    if not window:
        return
    try:
        window.hide()
        is_window_visible = False
    except Exception as e:
        print("Hide error:", e)

def toggle_window():
    global last_toggle_time, is_window_visible
    now = time.time()
    if now - last_toggle_time < 0.35:
        return
    last_toggle_time = now

    ensure_servers_running()
    if not is_window_visible or not is_window_foreground():
        show_and_focus()
    else:
        hide_or_minimize()

def on_closing():
    # When user clicks 'X', hide to system tray instead of closing app
    hide_or_minimize()
    return False

def setup_hotkeys():
    time.sleep(1.0)
    try:
        import keyboard
        # Register user requested shortcuts
        keyboard.add_hotkey("ctrl+d", toggle_window, suppress=False)
        keyboard.add_hotkey("alt+d", toggle_window, suppress=False)
        keyboard.add_hotkey("ctrl+space", toggle_window, suppress=False)
        keyboard.add_hotkey("ctrl+alt+d", toggle_window, suppress=False)
        print("[DAI] Global hotkeys hooked: ctrl+d, alt+d, ctrl+space, ctrl+alt+d")
    except Exception as e:
        print("[DAI] Failed to hook keyboard:", e)

def setup_tray():
    global tray_icon
    try:
        img = Image.open(ICON_PATH)
        menu = pystray.Menu(
            pystray.MenuItem("Open DAI (Ctrl+D)", lambda: show_and_focus(), default=True),
            pystray.MenuItem("Toggle Window", lambda: toggle_window()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit DAI", exit_app)
        )
        tray_icon = pystray.Icon("DAI", img, "DAI - Personal Intelligence (Ctrl+D / Alt+D)", menu)
        tray_icon.run_detached()
    except Exception as e:
        print("[DAI] Tray setup error:", e)

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
            if data == "TOGGLE":
                toggle_window()
            elif data == "SHOW":
                show_and_focus()
        except Exception:
            break

def try_connect_existing_instance():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", IPC_PORT))
        s.sendall(b"SHOW\n")
        s.close()
        return True
    except Exception:
        return False

def on_loaded():
    # Set window icon once native form is ready
    global window
    try:
        import clr
        clr.AddReference("System.Drawing")
        import System.Drawing
        form = window.native
        form.Icon = System.Drawing.Icon(ICON_PATH)
    except Exception as e:
        print("Icon set error:", e)

def main():
    global window

    # Check if instance is already running
    if try_connect_existing_instance():
        sys.exit(0)

    # Ensure background backend & frontend are running
    ensure_servers_running()

    # Start IPC server
    threading.Thread(target=ipc_server, daemon=True).start()

    # Start system tray
    setup_tray()

    # Start hotkey listener
    threading.Thread(target=setup_hotkeys, daemon=True).start()

    # Create native desktop window
    window = webview.create_window(
        title="DAI — Personal Intelligence & Project Builder",
        url="http://localhost:3000/chat",
        width=1280,
        height=840,
        min_size=(800, 600),
        text_select=True
    )
    window.events.closing += on_closing
    window.events.loaded += on_loaded

    # Run native event loop
    webview.start(storage_path=STORAGE_DIR)

if __name__ == "__main__":
    main()
