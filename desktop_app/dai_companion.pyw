import os
import sys
import time
import socket
import subprocess
import threading
import ctypes
from PIL import Image
import pystray
import keyboard

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROJECT_DIR = r"C:\Users\hp\Desktop\DAI"
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
LOGS_DIR = os.path.join(PROJECT_DIR, "desktop_app", ".logs")
DATA_DIR = r"C:\Users\hp\AppData\Local\DAI_App_Data"
ICON_PATH = os.path.join(PROJECT_DIR, "desktop_app", "dai_shield.ico")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP_URL = "http://localhost:3000/chat"
IPC_PORT = 48925

PYTHON_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
BACKEND_LOG = os.path.join(LOGS_DIR, "backend.log")
FRONTEND_LOG = os.path.join(LOGS_DIR, "frontend.log")

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008
SW_MINIMIZE = 6

tray_icon = None
last_action_time = 0.0

def is_port_open(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.4)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def ensure_servers():
    if not is_port_open(8000):
        log_f = open(BACKEND_LOG, "a", encoding="utf-8")
        subprocess.Popen(
            [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=BACKEND_DIR,
            stdin=subprocess.DEVNULL,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
        )
    if not is_port_open(3000):
        log_f = open(FRONTEND_LOG, "a", encoding="utf-8")
        subprocess.Popen(
            ["npm.cmd", "run", "dev"],
            cwd=FRONTEND_DIR,
            stdin=subprocess.DEVNULL,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
        )

def launch_dai_window():
    ensure_servers()
    if os.path.exists(CHROME_PATH):
        subprocess.Popen([
            CHROME_PATH,
            f"--app={APP_URL}",
            f"--user-data-dir={DATA_DIR}",
            "--window-size=1280,840"
        ], creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS)
    else:
        import webbrowser
        webbrowser.open(APP_URL)

def toggle_or_launch():
    global last_action_time
    now = time.time()
    if now - last_action_time < 0.35:
        return
    last_action_time = now

    # Check if the currently focused window is DAI
    try:
        fg = user32.GetForegroundWindow()
        if fg:
            length = user32.GetWindowTextLengthW(fg)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(fg, buff, length + 1)
                title = buff.value.lower()
                # If DAI window is active in foreground, minimize it
                if ("dai" in title or "localhost:3000" in title) and not any(
                    x in title for x in ["visual studio", "antigravity", "powershell", "cmd.exe", "code", "python"]
                ):
                    user32.ShowWindow(fg, SW_MINIMIZE)
                    return
    except Exception:
        pass

    # Otherwise launch or bring to front
    launch_dai_window()

def ipc_thread():
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
            conn.close()
        except Exception:
            break

def watchdog():
    time.sleep(10)
    while True:
        try:
            ensure_servers()
        except Exception:
            pass
        time.sleep(15)

def setup_tray():
    global tray_icon
    try:
        img = Image.open(ICON_PATH)
        menu = pystray.Menu(
            pystray.MenuItem("Open DAI (Alt+D / Ctrl+D)", lambda: launch_dai_window(), default=True),
            pystray.MenuItem("Toggle Window", lambda: toggle_or_launch()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit DAI", exit_app)
        )
        tray_icon = pystray.Icon("DAI", img, "DAI (Alt+D / Ctrl+D)", menu)
        tray_icon.run_detached()
    except Exception:
        pass

def exit_app():
    global tray_icon
    if tray_icon:
        try:
            tray_icon.stop()
        except Exception:
            pass
    os._exit(0)

def main():
    ensure_servers()
    setup_tray()
    threading.Thread(target=ipc_thread, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()

    # Register Hotkeys cleanly with keyboard module (zero cmd.exe, zero console)
    try:
        keyboard.add_hotkey("alt+d", toggle_or_launch, suppress=False)
        keyboard.add_hotkey("ctrl+d", toggle_or_launch, suppress=False)
        keyboard.add_hotkey("ctrl+alt+d", toggle_or_launch, suppress=False)
        keyboard.add_hotkey("ctrl+space", toggle_or_launch, suppress=False)
    except Exception as e:
        print("Hotkey registration error:", e)

    # Keep alive forever
    keyboard.wait()

if __name__ == "__main__":
    main()
