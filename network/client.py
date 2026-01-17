
# Author: Aashir Alam (fixed & simplified)

import socket
import threading

PORT = 5050
HEADER = 128
FORMAT = "utf-8"

class Client:
    def __init__(self, username, server_ip, server_pass=""):
        self.username = username
        self.server_ip = server_ip
        self.server_pass = server_pass
        self.connected = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send(self, msg):
        message = msg.encode(FORMAT)
        msg_len = len(message)
        header = str(msg_len).encode(FORMAT)
        header += b" " * (HEADER - len(header))
        self.sock.sendall(header)
        self.sock.sendall(message)

    def receive(self):
        header = self.sock.recv(HEADER).decode(FORMAT)
        if not header:
            return None
        length = int(header.strip())
        return self.sock.recv(length).decode(FORMAT)

    def listen(self):
        while self.connected:
            try:
                msg = self.receive()
                if msg:
                    print(msg)
            except:
                break

    def start(self):
        self.sock.connect((self.server_ip, PORT))
        print("[CONNECTED]")

        self.send(self.username)
        self.send(self.server_pass)

        thread = threading.Thread(target=self.listen, daemon=True)
        thread.start()

        while True:
            msg = input()
            if msg.lower() == "q":
                break
            self.send(msg)

        self.connected = False
        self.sock.close()


if __name__ == "__main__":
    username = input("Username: ")
    server_ip = input("Server IP address: ")
    server_pass = input("Server password (if any): ")

    client = Client(username, server_ip, server_pass)
    client.start()
