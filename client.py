# Author: Aashir

import socket
import threading
import pickle
from time import time
from _pickle import UnpicklingError

class Client:
	"""Represents a client which can join and send messages to a Server"""
	def __init__(self, username, server_ip, port=5050, header=1048, format_="utf-8", server_pass=""):
		"""
		:param port: int
		:param header: int
		:param format_: str
		"""
		self.PORT = port
		self.HEADER = header
		self.FORMAT = format_
		self.SERVER = server_ip
		self.DISCONNECT_MSG = "!DISCONNECT"
		self.WRONG_PASS_MSG = "!WRONGPASSWORD"
		self.NEW_CLIENT_MSG = "!NEWCLIENT"

		self.server_password = server_pass
		self.ADDR = (self.SERVER, self.PORT)
		self.username = username
		self.connected = False

		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.clients = []
		self.messages = []

	def __str__(self):
		return f"{self.username} ({self.SERVER}, {self.PORT})"

	def join_server(self):
		"""
		Connects the client to the server
		:returns: bool
		"""

		self.client.settimeout(20)

		try:
			self.client.connect(self.ADDR)

		except ConnectionRefusedError as e:
			return False

		except socket.timeout:
			print ("timed out")
			return False

		except WindowsError as e:
			if e.winerror == 10060:
				print ("couldn't connect to server because it took too long to respond or it has failed to respond")

			return False

		else:
			self.client.settimeout(None)

		self.connected = True

		# Making seperate thread for receiving any new clients or new client messages
		receive_clients_thread = threading.Thread(target=self.receive_clients)

		self.send_message(self.username)
		self.send_message(self.server_password)
		self.clients.append(self.username)

		receive_clients_thread.start()

		return True

	def send_message(self, msg):
		"""
		Sends a message to the server
		:param msg: str
		:returns: None
		"""
		if msg == "get":
			print (self.messages)
			print (self.clients)
			return None
        
        # Find out message length to send to server sending actual message

		message = msg.encode(self.FORMAT)
		message_len = len(message)
		send_len = str(message_len).encode(self.FORMAT)
		send_len += b" " * (self.HEADER - len(send_len))

		try:
			self.client.send(send_len)
			self.client.send(message)

		except OSError:
			self.close("OSError when trying to send message: " + message.decode('utf-8'))

	def receive_message(self):
		"""
		Receives message from the server and returns it decoded
		:returns: str / Exception
		"""
		try:
			message_len = self.client.recv(self.HEADER).decode(self.FORMAT)

		except (ConnectionAbortedError, OSError, ConnectionResetError) as e:
			return e

		if not message_len:
			return ""

		message_len = int(message_len)
		try:
			message = self.client.recv(message_len).decode(self.FORMAT)

		except (ConnectionAbortedError, OSError, ConnectionResetError) as e:
			return e

		return message


	def receive_clients(self):
		"""
		Receives updated clients dictionary
		or any new messages from server
		:returns: None
		"""
		
		while self.connected:
			try:
				message = self.receive_message()

			except TimeoutError:
				continue

			if isinstance(message, Exception):
				break

			if message == self.DISCONNECT_MSG:
				print ("Disconnected from server")
				break

			elif message == self.WRONG_PASS_MSG:
				print ("Wrong server password")
				break

			else:
				username = message.split(": ")[0]

				if username == message:
					username = message.split(" ")[0]

				if message == f"{username} has disconnected." or message == f"{username} has been kicked." and username in self.clients:
					self.clients.remove(username)
					self.messages.append(message)

				elif message == f"{username} has joined the chat." and username not in self.clients:
					self.clients.append(username)
					self.messages.append(message)

				elif ":" in message or message not in self.messages:
					self.messages.append(message)
					

		self.close()
		quit()


	def close(self):
		"""
		Closes the clients connection to the server
		:returns: None
		"""
		self.connected = False
		self.client.close()


if __name__ == "__main__":
	username = input("Username: ")
	host_name = input("Host Name (leave blank for localhost): ")
	server_pass = input("Server password: ")
	
	if host_name:
		server_ips = socket.gethostbyname_ex(socket.gethostname())[-1]

	else:
		server_ips = socket.gethostbyname_ex(host_name)[-1]

	for server_ip in server_ips:
		client = Client(username, server_ip, server_pass=server_pass)
		connected = client.join_server()

		if connected:
			break


	while client.connected:
		message = input(f"{client.username}: ")
		client.send_message(message)

		if message == "q":
			break

	print ("not connected")
	if client.connected:
		client.close()