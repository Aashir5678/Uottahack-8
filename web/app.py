import os
import sys
import threading
import time
from flask import Flask, jsonify, request, Response, render_template

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from network.server import Server, CMD_MSG, HEADER, FORMAT  # uses the restored Server.start


class WebControlServer(Server):
    def __init__(self, server_pass=""):
        super().__init__(server_pass=server_pass)
        self.client_conn = None
        self.conn_lock = threading.Lock()

    def handle_client(self, conn):
        # mark this conn as the active one (latest connection wins)
        with self.conn_lock:
            self.client_conn = conn

        print("[NEW CONNECTION] Web control client connected")
        if not self.start_time:
            self.start_time = time.time()

        try:
            while self.running:
                msg = self.receive(conn)
                if msg is None:
                    break
        finally:
            with self.conn_lock:
                if self.client_conn == conn:
                    self.client_conn = None
            try:
                conn.close()
            except Exception:
                pass
            print("[DISCONNECTED] Client left (web control server)")

    def get_latest_frame(self):
        return self.get_latest_frame_bytes()

    def send_control_command(self, command: str):
        with self.conn_lock:
            conn = self.client_conn

        if conn is None:
            return False, "No camera client connected"

        payload = command.encode(FORMAT)
        header = CMD_MSG.encode(FORMAT).ljust(HEADER, b" ")
        length_header = str(len(payload)).encode(FORMAT).ljust(HEADER, b" ")

        try:
            conn.sendall(header)
            conn.sendall(length_header)
            conn.sendall(payload)
            return True, None
        except OSError as exc:
            with self.conn_lock:
                if self.client_conn == conn:
                    self.client_conn = None
            return False, str(exc)

    def connection_status(self):
        with self.conn_lock:
            connected = self.client_conn is not None

        elapsed = time.time() - self.start_time if self.start_time else 0
        fps = round(self.frames / elapsed, 2) if elapsed > 0 else 0

        return {"connected": connected, "frames": self.frames, "fps": fps}


def create_app():
    control_server = WebControlServer()

    # FIX: now Server.start exists again
    server_thread = threading.Thread(target=control_server.start, daemon=True)
    server_thread.start()

    app = Flask(__name__, static_folder="static", template_folder="templates")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/frame.jpg")
    def latest_frame():
        frame_bytes = control_server.get_latest_frame()
        if not frame_bytes:
            return ("", 204)

        headers = {
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        }
        return Response(frame_bytes, mimetype="image/jpeg", headers=headers)

    @app.route("/api/stream.mjpg")
    def stream():
        boundary = "frame"

        def generate():
            while True:
                frame = control_server.get_latest_frame()
                if frame:
                    yield (
                        b"--" + boundary.encode() + b"\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
                        + frame + b"\r\n"
                    )
                time.sleep(0.05)

        return Response(generate(), mimetype=f"multipart/x-mixed-replace; boundary={boundary}")

    @app.route("/api/command", methods=["POST"])
    def command():
        payload = request.get_json(force=True, silent=True) or {}
        command_text = (payload.get("command") or "").strip()
        if not command_text:
            return jsonify({"error": "command is required"}), 400

        ok, error = control_server.send_control_command(command_text)
        if not ok:
            return jsonify({"error": error}), 503

        return jsonify({"status": "sent", "command": command_text})

    @app.route("/api/status")
    def status():
        return jsonify(control_server.connection_status())

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("WEB_PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)

