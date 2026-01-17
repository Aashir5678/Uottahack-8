

"""
SERVER HOST MUST DISABLE HOTSPOT FOR CLIENTS TO JOIN


"""

import socket
import threading
# from PIL import Image
import cv2
import io
import numpy as np

PORT = 5050
HEADER = 128
IMG_HEADER = 256 # 128
FORMAT = "utf-8"


IMG_MSG = "!IMG"
CMD_MSG = "!CMD"

DISCONNECT_MSG = "!DISCONNECT"
WRONG_PASS_MSG = "!WRONGPASSWORD"

class Server:
    def __init__(self, server_pass=""):
        self.SERVER = "0.0.0.0"
        self.ADDR = (self.SERVER, PORT)
        self.server_password = server_pass
        self.img_buff = None

        # self.clients = {}
        self.messages = []

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
        try:
            header = conn.recv(HEADER).decode(FORMAT)

        except UnicodeDecodeError as e:
            return None

        if header == IMG_MSG:
            return self.receive_img(conn)


        elif header == CMD_MSG:
            if not header:
                return None

            length = int(conn.recv(HEADER).decode(FORMAT).strip())
            msg = conn.recv(length).decode(FORMAT)

            self.lock.acquire()
            self.messages.append(msg)
            self.lock.release()

            return msg


    
    def handle_client(self, conn, addr):
        # try:
        get_frames_thread = threading.Thread(target=self.get_frames, args=(conn,))


        get_frames_thread.start()

        while True:
            self.display_img()
            
            # msg = self.receive(conn)

            # if msg is None:
            #     break

            # elif msg == IMAGE_MSG:
            #     # print("received image")
            #     self.receive_img(conn)


            # full_msg = f"{username}: {msg}"username
            # print(full_msg)
            # self.broadcast(full_msg)

        # except Exception as e:
        # 	print(e)

        # finally:

        # 	# Delete client if error

        #     with self.lock:
        #         if username in self.clients:
        #             del self.clients[username]

        #     conn.close()
        #     leave_msg = f"{username} has disconnected."
        #     print(leave_msg)
        #     self.broadcast(leave_msg)

    def get_frames(self, conn):
        while True:
            msg = self.receive(conn)

            if msg is None:
                break

            elif msg == IMG_MSG:
                self.receive_img(conn)

            elif msg == CMD_MSG:
                full_msg = f"{username}: {msg}"
                print(full_msg)




    def receive_img(self, conn):
        print ("starting to read img")
        # buff = bytearray()

        size = int(conn.recv(HEADER).decode(FORMAT))
        self.img_buff = conn.recv(size)

        # for img_index in range(0, size, IMG_HEADER):
        #     buff.extend(conn.recv(IMG_HEADER))



        # # buffer remaining image
        # if size % IMG_HEADER != 0:
        #     buff.extend(conn.recv(IMG_HEADER))


        # # print (f"received {str(len(img))} size img")

        # with open("flower.jpg", "wb") as f:
        #     f.write(bytes(buff))

        # img = Image.open(io.BytesIO(bytes(buff)))

        # img.show()

        with open("flower.jpg", "wb") as f:
            f.write(self.img_buff)


        

        # with open("")

        return self.img_buff


    def display_img(self):
        # if self.img_buff == None:
        #     return

        with open("flower.jpg", "rb") as f:
            self.img_buff = f.read()

        if self.img_buff == None or not self.img_buff:
            return

        frame = cv2.imdecode(np.frombuffer(self.img_buff, dtype=np.uint8), cv2.IMREAD_COLOR)

        cv2.imshow("webcam", frame)
        cv2.waitKey(1)
        # print ("showing")





if __name__ == "__main__":
    password = input("Set server password (leave blank for none): ")
    server = Server(server_pass=password)
    server.start()
