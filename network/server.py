
# Author: Aashir Alam (fixed & simplified)

"""
SERVER HOST MUST DISABLE HOTSPOT FOR CLIENTS TO JOIN


"""

import socket
import threading

PORT = 5050
HEADER = 128
FORMAT = "utf-8"

DISCONNECT_MSG = "!DISCONNECT"
WRONG_PASS_MSG = "!WRONGPASSWORD"

class Server:
    def __init__(self, server_pass=""):
        self.SERVER = "0.0.0.0"
        self.ADDR = (self.SERVER, PORT)
        self.server_password = server_pass

        self.clients = {}
        self.messages = []
        self.lock = threading.Lock()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server.bind(self.ADDR)
        self.server.listen()
        print(f"[SERVER] Listening on port {PORT}")

        while True:
            conn, addr = self.server.accept()
            print(f"[NEW CONNECTION] {addr}")
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()

    def send(self, conn, msg):
        message = msg.encode(FORMAT)
        msg_len = len(message)
        header = str(msg_len).encode(FORMAT)
        header += b" " * (HEADER - len(header))
        conn.sendall(header)
        conn.sendall(message)

    def receive(self, conn):
        header = conn.recv(HEADER).decode(FORMAT)
        if not header:
            return None
        length = int(header.strip())
        return conn.recv(length).decode(FORMAT)


    
    def handle_client(self, conn, addr):
        try:
            username = self.receive(conn)
            password = self.receive(conn)

            if self.server_password and password != self.server_password:
                self.send(conn, WRONG_PASS_MSG)
                conn.close()
                return

            with self.lock:
                self.clients[username] = conn
                join_msg = f"{username} has joined."
                print(join_msg)
                self.broadcast(join_msg)

            while True:
                msg = self.receive(conn)
                if msg is None:
                    break

                full_msg = f"{username}: {msg}"
                print(full_msg)
                self.broadcast(full_msg)

        except:
            pass

        finally:
            with self.lock:
                if username in self.clients:
                    del self.clients[username]
            conn.close()
            leave_msg = f"{username} has disconnected."
            print(leave_msg)
            self.broadcast(leave_msg)

    def broadcast(self, msg):
        for conn in self.clients.values():
            try:
                self.send(conn, msg)
            except:
                pass


if __name__ == "__main__":
    password = input("Set server password (leave blank for none): ")
    server = Server(server_pass=password)
    server.start()
