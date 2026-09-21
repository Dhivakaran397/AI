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
PYTHON_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
PYTHONW_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "pythonw.exe")
ICON_PATH = os.path.join(PROJECT_DIR, "desktop_app", "dai.ico")
IPC_PORT = 48921

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BROWSER_EXE = EDGE_PATH if os.path.exists(EDGE_PATH) else CHROME_PATH

# Win32 Constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
SW_HIDE = 0
SW_NORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3
SW_RESTORE = 9
SW_SHOW = 5

HOTKEYS = [
    (101, MOD_CONTROL | MOD_NOREPEAT, 0x20, "Ctrl+Space"),
    (102, MOD_ALT | MOD_NOREPEAT, 0x44, "Alt+D"),
    (103, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, 0x44, "Ctrl+Alt+D"),
    (104, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, 0x44, "Ctrl+Shift+D"),
    (105, MOD_ALT | MOD_NOREPEAT, 0x20, "Alt+Space"),
]

tray_icon = None

def is_port_open(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.6)
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

def find_dai_window():
    found = []
    def enum_cb(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.lower()
                # Check for DAI titles
                if ("dai" in title or "localhost:3000" in title or "personal intelligence" in title or "localhost_/chat" in title):
                    # Filter out IDE or shell windows
                    if not any(x in title for x in ["visual studio", "antigravity", "powershell", "cmd.exe"]):
                        found.append(hwnd)
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return found[0] if found else None

def bring_window_to_front(hwnd):
    # Simulate Alt key pulse to grant SetForegroundWindow permission
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.ShowWindow(hwnd, SW_SHOW)
    user32.keybd_event(0x12, 0, 0, 0)
    user32.SetForegroundWindow(hwnd)
    user32.keybd_event(0x12, 0, 2, 0)

last_toggle_time = 0.0

def toggle_dai_window():
    global last_toggle_time
    now = time.time()
    if now - last_toggle_time < 0.4:
        return
    last_toggle_time = now

    ensure_servers_running()
    hwnd = find_dai_window()
    if hwnd:
        fg = user32.GetForegroundWindow()
        if fg == hwnd:
            # If already focused, minimize it (toggle behavior)
            user32.ShowWindow(hwnd, 6) # SW_MINIMIZE
        else:
            bring_window_to_front(hwnd)
    else:
        # Launch dedicated standalone app window
        app_args = [
            BROWSER_EXE,
            "--app=http://localhost:3000/chat",
            r"--user-data-dir=C:\Users\hp\AppData\Local\DAI_App",
            "--window-size=1260,860"
        ]
        subprocess.Popen(app_args)

def hotkey_listener_thread():
    # Register Win32 hotkeys
    registered = []
    for hid, mod, vk, name in HOTKEYS:
        res = user32.RegisterHotKey(None, hid, mod, vk)
        if res:
            registered.append(hid)
            print(f"[DAI Hotkey] Registered {name}")
        else:
            print(f"[DAI Hotkey] Skipped {name} (already in use)")
    
    # Also attach keyboard library hooks in parallel as secondary layer
    try:
        import keyboard
        for k in ["ctrl+space", "alt+d", "ctrl+alt+d", "ctrl+shift+d"]:
            try:
                keyboard.add_hotkey(k, toggle_dai_window, suppress=False)
            except Exception:
                pass
    except Exception:
        pass

    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == WM_HOTKEY:
            toggle_dai_window()
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    # Cleanup on exit
    for hid in registered:
        user32.UnregisterHotKey(None, hid)

def ipc_server_thread():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", IPC_PORT))
        s.listen(5)
    except Exception as e:
        return

    while True:
        try:
            conn, _ = s.accept()
            data = conn.recv(1024).decode().strip()
            conn.close()
            if data == "TOGGLE":
                toggle_dai_window()
        except Exception:
            break

def open_in_browser(icon, item):
    import webbrowser
    webbrowser.open("http://localhost:3000/chat")

def restart_servers(icon, item):
    ensure_servers_running()
    if tray_icon:
        tray_icon.notify("DAI Services checked & restarted.", title="DAI Assistant")

def exit_dai(icon, item):
    if tray_icon:
        tray_icon.stop()
    os._exit(0)

def setup_tray():
    global tray_icon
    img = Image.open(ICON_PATH)
    menu = pystray.Menu(
        pystray.MenuItem("Open DAI (Ctrl+Space / Alt+D)", lambda: toggle_dai_window(), default=True),
        pystray.MenuItem("Open in Web Browser", open_in_browser),
        pystray.MenuItem("Restart Services", restart_servers),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit DAI", exit_dai)
    )
    tray_icon = pystray.Icon(
        "DAI",
        img,
        "DAI - Personal Intelligence (Ctrl+Space / Alt+D)",
        menu
    )
    tray_icon.run()

def try_connect_existing_instance():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", IPC_PORT))
        s.sendall(b"TOGGLE\n")
        s.close()
        return True
    except Exception:
        return False

def main():
    # Single instance check
    if try_connect_existing_instance():
        # Another instance was already running and has toggled the window
        sys.exit(0)

    # Start hotkey listener thread
    t_hotkey = threading.Thread(target=hotkey_listener_thread, daemon=True)
    t_hotkey.start()

    # Start IPC server thread
    t_ipc = threading.Thread(target=ipc_server_thread, daemon=True)
    t_ipc.start()

    # Immediately open/show DAI window on launch
    threading.Thread(target=toggle_dai_window, daemon=True).start()

    # Start system tray (blocks on main thread)
    setup_tray()

if __name__ == "__main__":
    main()
