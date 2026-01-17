import socket
import threading
import cv2
import time
import numpy as np
import os

# ----------------- CONSTANTS -----------------

PORT = 5050
HEADER = 128
FORMAT = "utf-8"

IMG_MSG = "!IMG"
CMD_MSG = "!CMD"

SAVE_EVERY_N_FRAMES = 10


# ----------------- SERVER -----------------

class Server:
    def __init__(self, server_pass=""):
        self.SERVER = "0.0.0.0"
        self.ADDR = (self.SERVER, PORT)
        self.server_password = server_pass

        # Timing / FPS
        self.start_time = 0
        self.frames = 0

        # Image buffer
        self.img_buff = None
        self.img_lock = threading.Lock()

        # Socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # ---- Save directory (Ai/images) ----
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_dir = os.path.join(BASE_DIR, "Ai", "images")
        os.makedirs(self.save_dir, exist_ok=True)

    # ----------------- START SERVER -----------------

    def start(self):
        self.server.bind(self.ADDR)
        self.server.listen()
        print(f"[SERVER] Listening on port {PORT}")

        while True:
            conn, addr = self.server.accept()
            print(f"[NEW CONNECTION] {addr}")
            thread = threading.Thread(
                target=self.handle_client,
                args=(conn,),
                daemon=True
            )
            thread.start()

    # ----------------- SOCKET HELPERS -----------------

    def recv_exact(self, conn, size):
        data = b""
        while len(data) < size:
            packet = conn.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def receive(self, conn):
        header = conn.recv(HEADER).decode(FORMAT).strip()
        if not header:
            return None

        if header == IMG_MSG:
            return self.receive_img(conn)

        elif header == CMD_MSG:
            length = int(conn.recv(HEADER).decode(FORMAT).strip())
            return conn.recv(length).decode(FORMAT)

        return None

    # ----------------- IMAGE HANDLING -----------------

    def receive_img(self, conn):
        size = int(conn.recv(HEADER).decode(FORMAT).strip())
        img_bytes = self.recv_exact(conn, size)

        if img_bytes is None:
            return None

        with self.img_lock:
            self.img_buff = img_bytes

        self.frames += 1
        return IMG_MSG

    def display_img(self):
        with self.img_lock:
            if not self.img_buff:
                return
            img_data = self.img_buff

        frame = cv2.imdecode(
            np.frombuffer(img_data, dtype=np.uint8),
            cv2.IMREAD_COLOR
        )

        if frame is None:
            return

        # -------- FPS --------
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            fps = round(self.frames / elapsed, 2)
            if self.frames % 30 == 0:
                print(f"FPS: {fps}")

        # -------- Save every N frames --------
        if self.frames % SAVE_EVERY_N_FRAMES == 0:
            filename = f"frame_{self.frames:06d}.jpg"
            filepath = os.path.join(self.save_dir, filename)
            cv2.imwrite(filepath, frame)

        # -------- Display --------
        cv2.imshow("frame", frame)
        cv2.waitKey(1)

    # ----------------- CLIENT HANDLER -----------------

    def handle_client(self, conn):
        recv_thread = threading.Thread(
            target=self.get_frames,
            args=(conn,),
            daemon=True
        )
        recv_thread.start()

        self.start_time = time.time()

        while True:
            self.display_img()

    def get_frames(self, conn):
        while True:
            msg = self.receive(conn)
            if msg is None:
                break

        conn.close()
        print("[DISCONNECTED] Client left")

# ----------------- MAIN -----------------

if __name__ == "__main__":
    password = input("Set server password (leave blank for none): ")
    server = Server(server_pass=password)
    server.start()
