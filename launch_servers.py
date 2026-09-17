"""
Localhost Launcher for Fayda Postal Dispatch System.
Runs all portals on localhost:
 - Public Citizen Kiosk: http://localhost:3000
 - Postal Staff Portal:  http://localhost:4000
 - Central FastAPI API:   http://localhost:8000
"""
import os
import sys
import time
import socket
import urllib.request
import threading
import http.server
import socketserver
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KIOSK_DIR = os.path.join(BASE_DIR, "kiosk")
STAFF_DIR = os.path.join(BASE_DIR, "staff")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

# Ensure backend path is on sys.path
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def is_backend_alive():
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/docs", timeout=1)
        return req.status == 200
    except Exception:
        return False


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def start_static_server(directory, port, name):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, format, *args):
            pass

    if is_port_in_use(port):
        print(f"[ONLINE] {name:22} -> http://localhost:{port} (Active)")
        return

    try:
        with ReusableTCPServer(("127.0.0.1", port), Handler) as httpd:
            print(f"[ONLINE] {name:22} -> http://localhost:{port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"[ERROR] {name} on port {port}: {e}")


def main():
    print("=" * 68)
    print("  FAYDA POSTAL DISPATCH SYSTEM - LOCALHOST SERVICE LAUNCHER")
    print("=" * 68)

    # 1. Start Citizen Kiosk on port 3000
    kiosk_thread = threading.Thread(
        target=start_static_server,
        args=(KIOSK_DIR, 3000, "Citizen Public Kiosk"),
        daemon=True
    )
    kiosk_thread.start()

    # 2. Start Staff Portal on port 4000
    staff_thread = threading.Thread(
        target=start_static_server,
        args=(STAFF_DIR, 4000, "Postal Staff Portal"),
        daemon=True
    )
    staff_thread.start()

    time.sleep(0.5)

    print(f"[ONLINE] {'Backend API & Docs':22} -> http://localhost:8000/docs")
    print("-" * 68)
    print("Public Citizen Kiosk: http://localhost:3000")
    print("Postal Staff Portal:  http://localhost:4000")
    print("Backend API & Docs:   http://localhost:8000")
    print("=" * 68)

    # 3. Check if FastAPI Backend is already running on port 8000
    if is_backend_alive():
        print("[INFO] FastAPI Backend is already active on http://localhost:8000.")
        print("[INFO] All portals are live on localhost. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down launcher...")
            sys.exit(0)
    else:
        from main import app
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
