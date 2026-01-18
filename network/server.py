import socket
import threading
import time
import numpy as np
import cv2
import os

# ----------------- CONSTANTS -----------------

PORT = 5050
HEADER = 128
FORMAT = "utf-8"

IMG_MSG = "!IMG"
CMD_MSG = "!CMD"

SAVE_EVERY_N_FRAMES = 10


class Server:
    def __init__(self, server_pass=""):
        self.SERVER = "0.0.0.0"
        self.ADDR = (self.SERVER, PORT)
        self.server_password = server_pass

        # Timing / FPS
        self.start_time = 0.0
        self.frames = 0

        # Latest image buffer (bytes)
        self.img_buff = None
        self.img_lock = threading.Lock()

        # Socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.running = True

        # Optional: save directory
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_dir = os.path.join(BASE_DIR, "Ai", "images")
        os.makedirs(self.save_dir, exist_ok=True)

    # ----------------- SOCKET HELPERS -----------------

    def recv_exact(self, conn, size: int):
        data = b""
        while len(data) < size:
            packet = conn.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def recv_header_str(self, conn):
        raw = self.recv_exact(conn, HEADER)
        if raw is None:
            return None
        return raw.decode(FORMAT, errors="ignore").strip()

    def receive(self, conn):
        msg_type = self.recv_header_str(conn)
        if not msg_type:
            return None

        if msg_type == IMG_MSG:
            return self.receive_img(conn)

        if msg_type == CMD_MSG:
            length_str = self.recv_header_str(conn)
            if not length_str:
                return None
            try:
                length = int(length_str)
            except ValueError:
                return None

            payload = self.recv_exact(conn, length)
            if payload is None:
                return None
            return payload.decode(FORMAT, errors="ignore")

        return None

    # ----------------- IMAGE HANDLING -----------------

    def receive_img(self, conn):
        size_str = self.recv_header_str(conn)
        if not size_str:
            return None
        try:
            size = int(size_str)
        except ValueError:
            return None

        img_bytes = self.recv_exact(conn, size)
        if img_bytes is None:
            return None

        with self.img_lock:
            self.img_buff = img_bytes

        self.frames += 1

        # Optional: save every N frames (decode then write)
        if SAVE_EVERY_N_FRAMES and (self.frames % SAVE_EVERY_N_FRAMES == 0):
            frame = cv2.imdecode(np.frombuffer(img_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                filename = f"frame_{self.frames:06d}.jpg"
                filepath = os.path.join(self.save_dir, filename)
                cv2.imwrite(filepath, frame)

        return IMG_MSG

    def get_latest_frame_bytes(self):
        with self.img_lock:
            if not self.img_buff:
                return None
            return bytes(self.img_buff)

    # ----------------- SERVER LOOP -----------------

    def start(self):
        """Accept clients and handle each client in its own thread."""
        self.server.bind(self.ADDR)
        self.server.listen()
        print(f"[SERVER] Listening on port {PORT}")

        self.start_time = time.time()

        while self.running:
            try:
                conn, addr = self.server.accept()
            except OSError:
                break

            print(f"[NEW CONNECTION] {addr}")
            t = threading.Thread(target=self.handle_client, args=(conn,), daemon=True)
            t.start()

    def handle_client(self, conn):
        """Default client handler: keep receiving until disconnect."""
        try:
            while self.running:
                msg = self.receive(conn)
                if msg is None:
                    break
        finally:
            try:
                conn.close()
            except Exception:
                pass
            print("[DISCONNECTED] Client left")
