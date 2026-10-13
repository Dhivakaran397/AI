import os
import sys
import subprocess

PROJECT_DIR = r"C:\Users\hp\Desktop\DAI"
COMPANION_SCRIPT = os.path.join(PROJECT_DIR, "desktop_app", "dai_companion.pyw")
PYTHONW = os.path.join(PROJECT_DIR, "backend", ".venv", "Scripts", "pythonw.exe")

def main():
    subprocess.Popen([PYTHONW, COMPANION_SCRIPT], creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    import dai_companion
    dai_companion.show_window()

if __name__ == "__main__":
    main()
