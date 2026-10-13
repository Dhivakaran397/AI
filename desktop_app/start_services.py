import os
import sys
import time
import socket
import subprocess

PROJECT_DIR = r"C:\Users\hp\Desktop\DAI"
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
LOGS_DIR = os.path.join(PROJECT_DIR, "desktop_app", ".logs")
os.makedirs(LOGS_DIR, exist_ok=True)

PYTHON_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
PYTHONW_EXE = os.path.join(BACKEND_DIR, ".venv", "Scripts", "pythonw.exe")
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
COMPANION_SCRIPT = os.path.join(PROJECT_DIR, "desktop_app", "dai_companion.pyw")
APP_URL = "http://localhost:3000/chat"
DATA_DIR = r"C:\Users\hp\AppData\Local\DAI_App_Data"

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008

def is_port_open(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
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
    for _ in range(15):
        time.sleep(0.4)
        if is_port_open(8000):
            return True
    return False

def ensure_frontend():
    if is_port_open(3000):
        return True
    log_f = open(os.path.join(LOGS_DIR, "frontend.log"), "a", encoding="utf-8")
    prod_build = os.path.join(FRONTEND_DIR, ".next")
    node_cmd = r"C:\Program Files\nodejs\node.exe" if os.path.exists(r"C:\Program Files\nodejs\node.exe") else "node"
    next_bin = os.path.join(FRONTEND_DIR, "node_modules", "next", "dist", "bin", "next")
    if os.path.exists(prod_build):
        cmd = [node_cmd, next_bin, "start", "-p", "3000"]
    else:
        cmd = [node_cmd, next_bin, "dev", "-p", "3000"]

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

HOTKEY_VBS = os.path.join(PROJECT_DIR, "desktop_app", "start_hotkey.vbs")

def ensure_companion():
    subprocess.Popen(
        ["wscript.exe", HOTKEY_VBS],
        cwd=os.path.join(PROJECT_DIR, "desktop_app"),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
    )

def launch_chrome():
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

def main():
    # 1. Ensure servers are alive
    ensure_backend()
    ensure_frontend()
    # 2. Ensure companion hotkey listener is alive
    ensure_companion()
    # 3. Always launch / focus the Chrome App window
    launch_chrome()

if __name__ == "__main__":
    main()
