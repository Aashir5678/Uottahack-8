
"""
Author: Aashir Alam

MUST DISABLE FIREWALL ON THIS COMPUTER FOR OTHER COMPUTERS TO JOIN

"""

import socket
import threading
import pickle

class Server:
	"""Represents a server which clients can connect to and send messages to"""
	def __init__(self, port=5050, header=1048, server_pass="", format_="utf-8"):
		"""
		:param port: int
 		:param header: int
		:param format: str
		"""
		self.PORT = port
		self.HEADER = header
		self.HOST = socket.gethostname()
		self.SERVER = socket.gethostbyname_ex(self.HOST)[-1][-1]
		self.ADDR = (self.SERVER, self.PORT)
		print (self.ADDR)
		self.server_password = server_pass
		self.FORMAT = format_
		self.DISCONNECT_MSG = "!DISCONNECT"
		self.WRONG_PASS_MSG = "!WRONGPASSWORD"
		self.NEW_CLIENT_MSG = "!NEWCLIENT"
		self.started = False
		self.lock = threading.Lock()

		# "aashir": [conn, [messages]]
		self.clients = {}
		# ordered messages
		self.messages = []
		self.banned_ips = []

		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def bind_server(self):
		"""
		Attempts to bind the server to self.ADDR, returns true if binding wsa successful
		:returns: bool
		"""
		try:
			self.server.bind(self.ADDR)
			return True

		except:
			return False

	def start(self):
		"""
		Starts the server
		:returns: None
		"""
		self.started = True

		try:
			self.server.listen(5)

		except:
			return None

		print ("server has started")

		# Wait for any incoming connections, and handle that connection
		while True:
			try:
				conn, addr = self.server.accept()

			except OSError as e:
				print (f"OSError: {str(e)}")
				break

			client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
			client_thread.setDaemon(True)
			client_thread.start()

		self.close()

	def handle_client(self, conn, addr):
		"""
		Handles a client when they join
		:param conn: socket.socket
		:param addr: str
		:returns: None
		"""
		username = self.receive_message(conn)
		server_password = self.receive_message(conn)

		if addr[0] in self.banned_ips:
			self.send_string_message(conn, self.DISCONNECT_MSG)
			conn.close()
			return None

		elif not username:
			self.send_string_message(conn, self.DISCONNECT_MSG)
			conn.close()
			return None

		elif username in self.clients:
			client = self.clients[username]
			client_connected = client[0].fileno()

			if client_connected != -1:
				self.send_string_message(conn, self.DISCONNECT_MSG)
				conn.close()
				return None

		elif self.server_password != server_password:
			self.send_string_message(conn, self.WRONG_PASS_MSG)
			conn.close()
			return None


		# Store client and send all messges to client
		connected = True
		join_message = f"{username} has joined the chat."
		print (join_message)

		self.lock.acquire()
		self.messages.append(join_message)
		self.lock.release()
		self.clients[username] = [conn, addr, []]
		self.send_client_message(username=username)
		self.broadcast_new_client(username)

		while connected:
			try:
				message = self.receive_message(conn)

			except TimeoutError:
				continue

			if isinstance(message, Exception):
				connected = False
				break

			# Add message to clients dictionary, and send that message to every other client

			self.lock.acquire()
			self.clients[username][-1].append(message)
			message = f"{username}: {message}"
			print (message)

			self.messages.append(message)
			self.send_client_message(new_message=message)
			self.lock.release()

		self.disconnect_client(username)

	def receive_message(self, conn):
		"""
		Receives message from the connection provided and returns it decoded
		:param conn: socket.socket
		:returns: str / Exception
		"""
		try:
			message_len = conn.recv(self.HEADER).decode(self.FORMAT)

		except (ConnectionAbortedError, OSError, ConnectionResetError) as e:
			return e

		if not message_len:
			return ""

		message_len = int(message_len)

		try:
			message = conn.recv(message_len).decode(self.FORMAT)

		except (ConnectionAbortedError, OSError, ConnectionResetError) as e:
			return e


		return message

	def send_client_message(self, username="", new_message=None):
		"""
		Sends a message to the client with the username provided,
		if no username is provided then the new message is sent
		to every client, if a username is provided but new_message
		is None, then all the messages sent are sent to the client
		with that username.

		:param username: str
		:param new_message: str
		:returns: bool
		"""

		# Send one new message to client with the username
		if username and new_message is not None:
			client_info = self.clients.get(username, None)

			if client_info is not None:
				conn = client_info[0]
				self.send_string_message(conn, new_message)
				return True

			return False

		# Send all messages to client with the username
		elif username and new_message is None:
			client_info = self.clients.get(username)
			conn = client_info[0]

			for message in self.messages:
				self.send_string_message(conn, message)

			return True

		# Sends one new message to all clients in server
		elif not username:
			for client_username, client_info in self.clients.items():
				conn = client_info[0]
				self.send_string_message(conn, new_message)

			return True


		return False


	def broadcast_new_client(self, client_username):
		"""
		Sends the new client to every other
		client in the server
		:param client_username: str
		:returns: bool
		"""
		for username, client_info in self.clients.items():
			conn = client_info[0]
			send = f"{client_username} has joined the chat."
			self.send_string_message(conn, send)

		return True

	def send_string_message(self, conn, msg):
		"""
		Sends a message to the connection provided
		:param conn: socket.socket
		:param msg: str
		:returns: None
		"""

		# Find out message length to send to server sending actual message

		message = msg.encode(self.FORMAT)
		message_len = len(message)
		send_len = str(message_len).encode(self.FORMAT)
		send_len += b" " * (self.HEADER - len(send_len))

		try:
			conn.send(send_len)
			conn.send(message)

		except OSError:
			pass

	def ban_ip(self, ip):
		"""
		Bans the specified ip address from the server, if ip address isn't valid
		then False is returned, if it is valid True is returned
		:param ip: str
		:returns: bool
		"""
		# Validate ip address

		try:
			socket.inet_aton(ip)

		except:
			return False

		self.banned_ips.append(ip)
		
		for client_username, client_info in self.clients.items():
			client_ip = client_info[1][0]
			if client_ip in self.banned_ips:
				self.disconnect_client(client_username)

		return True

	def unban_ip(self, ip):
		"""
		Unbans the specified ip address from the server, if ip is successfully 
		unbanned, then True if returned, otherwise False is returned
		:param ip: str
		:returns: bool
		"""
		if ip in self.banned_ips:
			self.banned_ips.remove(ip)
			return True

		return False
		
	def kick_client(self, username):
		"""
		Kicks the client with the username provided, returns true if client was successfully kicked
		:param username: str
		:returns: bool
		"""
		if username not in self.clients:
			print ("non existing client")
			return False

		self.lock.acquire()
		conn = self.clients[username][0]
		self.send_string_message(conn, self.DISCONNECT_MSG)

		conn.close()
		disconnect_msg = f"{username} has been kicked."
		print (disconnect_msg)
		self.messages.append(disconnect_msg)
		self.send_client_message(new_message=disconnect_msg)
		self.lock.release()

		return True

	def disconnect_client(self, username):
		"""
		Disconnects the client with the username provided, returns true if client was successfully disconnected
		:param username: str
		:returns: bool
		"""
		if (username not in self.clients) or (False in self.clients[username][-1]):
			return False

		self.lock.acquire()
		conn = self.clients[username][0]
		self.send_string_message(conn, self.DISCONNECT_MSG)

		conn.close()
		disconnect_msg = f"{username} has disconnected."
		print (disconnect_msg)
		self.messages.append(disconnect_msg)
		self.send_client_message(new_message=disconnect_msg)
		self.lock.release()

		return True

	def close(self):
		print ("server closed")
		self.server.close()



if __name__ == "__main__":
	server = Server()
	bound = server.bind_server()
	print (bound)
	server.start()