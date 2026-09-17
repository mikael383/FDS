"""
Multi-Domain / Multi-Port Launcher for Fayda Postal Dispatch System.
Binds to 0.0.0.0 so other PCs, phones, and kiosk tablets on the local network can connect!

Runs:
 - Public Citizen Kiosk: http://0.0.0.0:3000  (LAN: http://<YOUR_IP>:3000)
 - Postal Staff Portal:  http://0.0.0.0:4000  (LAN: http://<YOUR_IP>:4000)
 - Central FastAPI API:   http://0.0.0.0:8000  (LAN: http://<YOUR_IP>:8000)
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


def get_local_ip():
    """Find local network IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


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


def start_static_server(directory, port, name, local_ip):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, format, *args):
            pass

    if is_port_in_use(port):
        print(f"[ONLINE] {name:22} -> Local: http://localhost:{port} | LAN: http://{local_ip}:{port} (Active)")
        return

    try:
        with ReusableTCPServer(("0.0.0.0", port), Handler) as httpd:
            print(f"[ONLINE] {name:22} -> Local: http://localhost:{port} | LAN: http://{local_ip}:{port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"[ERROR] {name} on port {port}: {e}")


def main():
    local_ip = get_local_ip()

    print("=" * 72)
    print("  FAYDA POSTAL DISPATCH SYSTEM - MULTI-DEVICE NETWORK LAUNCHER")
    print("=" * 72)
    print(f"  Local Network IP Address: {local_ip}")
    print("=" * 72)

    # 1. Start Citizen Kiosk on port 3000
    kiosk_thread = threading.Thread(
        target=start_static_server,
        args=(KIOSK_DIR, 3000, "Citizen Public Kiosk", local_ip),
        daemon=True
    )
    kiosk_thread.start()

    # 2. Start Staff Portal on port 4000
    staff_thread = threading.Thread(
        target=start_static_server,
        args=(STAFF_DIR, 4000, "Postal Staff Portal", local_ip),
        daemon=True
    )
    staff_thread.start()

    time.sleep(0.5)

    print(f"[ONLINE] {'Backend API & Docs':22} -> Local: http://localhost:8000/docs | LAN: http://{local_ip}:8000/docs")
    print("-" * 72)
    print("Access from ANY PC / Phone on the same Wi-Fi network:")
    print(f"  • Public Citizen Kiosk: http://{local_ip}:3000")
    print(f"  • Postal Staff Portal:  http://{local_ip}:4000")
    print(f"  • Backend API & Docs:   http://{local_ip}:8000")
    print("=" * 72)

    # 3. Check if FastAPI Backend is already running on port 8000
    if is_backend_alive():
        print(f"[INFO] FastAPI Backend is already active on port 8000.")
        print("[INFO] All portals are live across the local network. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down launcher...")
            sys.exit(0)
    else:
        from main import app
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
