import sys, time
with open(r"C:\Users\hp\Desktop\DAI\desktop_app\trace.log", "w") as f:
    f.write("Started\n")
    f.flush()
    try:
        import keyboard
        f.write("Imported keyboard\n")
        f.flush()
        def foo(): pass
        keyboard.add_hotkey("alt+d", foo)
        f.write("Added hotkey\n")
        f.flush()
        for i in range(10):
            time.sleep(1)
            f.write(f"Tick {i}\n")
            f.flush()
    except Exception as e:
        f.write(f"Exception: {e}\n")
        f.flush()
    f.write("Finished normally\n")
