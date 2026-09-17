"""
Multi-Domain / Multi-Port Launcher for Fayda Postal Dispatch System.
Runs:
 - Public Citizen Kiosk: http://127.0.0.1:3000
 - Postal Staff Portal:  http://127.0.0.1:5000
 - Central FastAPI API:   http://127.0.0.1:8000
"""
import os
import sys
import threading
import http.server
import socketserver
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KIOSK_DIR = os.path.join(BASE_DIR, "fayda-dispatch-system", "kiosk")
STAFF_DIR = os.path.join(BASE_DIR, "fayda-dispatch-system", "staff")
BACKEND_DIR = os.path.join(BASE_DIR, "fayda-dispatch-system", "backend")

# Ensure backend path is on sys.path
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def start_static_server(directory, port, name):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, format, *args):
            # Keep console clean
            pass

    try:
        with ReusableTCPServer(("127.0.0.1", port), Handler) as httpd:
            print(f"[ONLINE] {name} -> http://127.0.0.1:{port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"[ERROR] {name} Server on port {port}: {e}")


def main():
    print("=" * 68)
    print("  FAYDA POSTAL DISPATCH SYSTEM - MULTI-DOMAIN SERVICE LAUNCHER")
    print("=" * 68)

    # 1. Start Citizen Kiosk on port 3000
    kiosk_thread = threading.Thread(
        target=start_static_server,
        args=(KIOSK_DIR, 3000, "Citizen Public Kiosk"),
        daemon=True
    )
    kiosk_thread.start()

    # 2. Start Staff Portal on port 5000
    staff_thread = threading.Thread(
        target=start_static_server,
        args=(STAFF_DIR, 5000, "Postal Staff Portal"),
        daemon=True
    )
    staff_thread.start()

    print(f"[ONLINE] Backend API & Docs  -> http://127.0.0.1:8000/docs")
    print("-" * 68)
    print("Public Citizen Kiosk: http://127.0.0.1:3000")
    print("Postal Staff Portal:  http://127.0.0.1:5000")
    print("Backend API & Docs:   http://127.0.0.1:8000")
    print("=" * 68)

    # 3. Start FastAPI Backend on port 8000 (Main Thread)
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
