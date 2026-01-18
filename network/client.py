import socket
import threading
import cv2
from time import sleep


PORT = 5050
HEADER = 128
FORMAT = "utf-8"

IMG_MSG = "!IMG"
CMD_MSG = "!CMD"

class Client:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.connected = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # ----------------- SEND HELPERS -----------------

    def send_image(self, img_bytes):
        size = len(img_bytes)

        # Send IMG header
        header = IMG_MSG.encode(FORMAT)
        header += b" " * (HEADER - len(header))
        self.sock.sendall(header)

        # Send image size
        size_header = str(size).encode(FORMAT)
        size_header += b" " * (HEADER - len(size_header))
        self.sock.sendall(size_header)

        # Send image data
        self.sock.sendall(img_bytes)

    # ----------------- RECEIVE (OPTIONAL) -----------------

    def receive(self):
        header = self.sock.recv(HEADER).decode(FORMAT).strip()
        if not header:
            return None

        length = int(self.sock.recv(HEADER).decode(FORMAT).strip())
        return self.sock.recv(length).decode(FORMAT)

    def listen(self):
        while self.connected:
            try:
                msg = self.receive()
                if msg is None:
                    break
            except:
                break

    # ----------------- MAIN -----------------

    def start(self):
        self.sock.connect((self.server_ip, PORT))
        print("[CONNECTED]")

        threading.Thread(target=self.listen, daemon=True).start()

        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            encoded = cv2.imencode(".jpg", frame)[1].tobytes()
            self.send_image(encoded)

            sleep(0.1)  # ~10 FPS

        cap.release()
        self.sock.close()


if __name__ == "__main__":
    server_ip = input("Server IP address: ")
    client = Client(server_ip)
    client.start()