import os
import sys
import time
import signal
import subprocess
import webbrowser

BACKEND_CMD = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
FRONTEND_URL = "http://localhost:3000"

procs: list[subprocess.Popen] = []


def shutdown(sig=None, frame=None):
    print("\nShutting down...")
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

if __name__ == "__main__":
    print("Starting FastAPI backend on port 8000...")
    backend = subprocess.Popen(BACKEND_CMD)
    procs.append(backend)

    print("Starting Next.js frontend on port 3000...")
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend = subprocess.Popen(
        [npm, "run", "start"],
        cwd=FRONTEND_DIR,
    )
    procs.append(frontend)

    print("Waiting for servers to start...")
    time.sleep(5)

    print(f"Opening {FRONTEND_URL}")
    webbrowser.open(FRONTEND_URL)

    print("Next Gen AI running. Press Ctrl+C to stop.")
    try:
        backend.wait()
    except KeyboardInterrupt:
        shutdown()
