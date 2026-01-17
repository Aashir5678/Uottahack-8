import socket
import threading
import cv2
import numpy as np

PORT = 5050
HEADER = 128
FORMAT = "utf-8"

IMG_MSG = "!IMG"
CMD_MSG = "!CMD"

class Server:
    def __init__(self, server_pass=""):
        self.SERVER = "0.0.0.0"
        self.ADDR = (self.SERVER, PORT)
        self.server_password = server_pass

        self.img_buff = None
        self.img_lock = threading.Lock()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server.bind(self.ADDR)
        self.server.listen()
        print(f"[SERVER] Listening on port {PORT}")

        while True:
            conn, addr = self.server.accept()
            print(f"[NEW CONNECTION] {addr}")
            thread = threading.Thread(target=self.handle_client, args=(conn,))
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
        print("[SERVER] Receiving image")

        size = int(conn.recv(HEADER).decode(FORMAT).strip())
        img_bytes = self.recv_exact(conn, size)

        if img_bytes is None:
            return None

        with self.img_lock:
            self.img_buff = img_bytes

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

        cv2.imshow("webcam", frame)
        cv2.waitKey(1)

    # ----------------- CLIENT HANDLER -----------------

    def handle_client(self, conn):
        recv_thread = threading.Thread(
            target=self.get_frames, args=(conn,), daemon=True
        )
        recv_thread.start()

        while True:
            self.display_img()

    def get_frames(self, conn):
        while True:
            msg = self.receive(conn)
            if msg is None:
                break

        conn.close()
        print("[DISCONNECTED] Client left")


if __name__ == "__main__":
    password = input("Set server password (leave blank for none): ")
    server = Server(server_pass=password)
    server.start()
