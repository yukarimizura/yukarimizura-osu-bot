import subprocess
import sys
import time
from watchfiles import watch

WATCH = (
    "commands",
    "api",
    "utils",
    "bot.py",
    "config.py",
)

IGNORE = (
    "__pycache__",
    "venv",
    ".git",
    "data",
)

def start():
    print("▶ Starting bot...")
    return subprocess.Popen([sys.executable, "bot.py"])

bot = start()

try:
    for changes in watch(*WATCH, debounce=20000):

        changes = [
            c for c in changes
            if not any(ignore in c[1] for ignore in IGNORE)
            and not c[1].endswith(".pyc")
        ]

        if not changes:
            continue

        print("\nDetected changes:")
        for _, path in changes:
            print(" •", path)

        print("Restarting bot...")

        bot.terminate()
        bot.wait()

        # give Discord time to fully close
        time.sleep(2)

        bot = start()

except KeyboardInterrupt:
    print("\nStopping...")
    bot.terminate()