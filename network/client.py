

import socket
import threading
import pickle
from PIL import Image
import io
import cv2

from time import sleep

PORT = 5050
HEADER = 128
IMG_HEADER = 256
FORMAT = "utf-8"
IMG_MSG = "!IMG"
CMD_MSG = "!CMD"


class Client:
	def __init__(self, server_ip):
		self.server_ip = server_ip
		self.connected = True

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def send(self, msg):
		self.sock.sendall(CMD_MSG.encode(FORMAT))

		message = msg.encode(FORMAT)
		msg_len = len(message)
		header = str(msg_len).encode(FORMAT)
		header += b" " * (HEADER - len(header))
		self.sock.sendall(header)
		self.sock.sendall(message)


	def send_image(self, img):
		size = len(img)

		print ("starting send img")

		self.sock.sendall(IMG_MSG.encode(FORMAT))

		byte_padding = b" " * (HEADER - len(str(size).encode(FORMAT)))
		self.sock.sendall(str(size).encode(FORMAT) + byte_padding)

		self.sock.sendall(img)
		
		# if size < IMG_HEADER:
		# 	self.sock.sendall(img + b" " * (IMG_HEADER - size))

		# else:

		# 	start_index = 0

		# 	for img_index in range(IMG_HEADER, size, IMG_HEADER):
		# 		self.sock.sendall(img[start_index:img_index])

		# 		# print(str(start_index), ", " + str(img_index))
		# 		start_index = img_index


		# 	# send remaining image data if size isn't evenly divisible by header
		# 	if size % IMG_HEADER != 0:
		# 		padding_bytes = b" " * ((size % IMG_HEADER) - (size - IMG_HEADER))
		# 		self.sock.sendall(img[(size - IMG_HEADER)::] + padding_bytes)
		# 		# print(str(size - IMG_HEADER) + ", " + str(size - 1))
		

		print ("done")


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

			except Exception as e:
				print (e)
				break

	def start(self):
		self.sock.connect((self.server_ip, PORT))
		print("[CONNECTED]")

		thread = threading.Thread(target=self.listen, daemon=True)
		thread.start()

		# with open("flower.jpg", "rb") as f:
		# 	img = f.read()


		cap = cv2.VideoCapture(0)

		while True:
			ret, frame = cap.read()

			if ret:

				self.send_image(cv2.imencode('.jpg', frame)[1].tobytes())

			# msg = input(f"{self.username}: ")

			# self.send_image(("b" * 550).encode("utf-8"))

			# self.send_image(img)
			# self.send(msg)


			# if msg.lower() == "q":
			# 	break
			# self.send(msg)

			sleep(0.5)

		cap.release()
		self.connected = False
		self.sock.close()


if __name__ == "__main__":

	# username = input("Username: ")
	server_ip = input("Server IP address: ")
	# server_pass = input("Server password (if any): ")

	client = Client(server_ip)
	client.start()
