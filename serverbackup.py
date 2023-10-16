import sys, socket

from ServerWorker import ServerWorker

class ServerBackup:	
	
	def main(self):
		try:
			SERVER_PORT = int(sys.argv[1])
		except:
			print("[Usage: ServerBackup.py Server_port]\n")
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		rtspSocket.bind(('127.0.0.1', SERVER_PORT))
		rtspSocket.listen(5)        

		# recebe infos do cliente
		while True:
			clientInfo = {}
			clientInfo['rtspSocket'] = rtspSocket.accept()
			ServerWorker(clientInfo).run()		

if __name__ == "__main__":
	(ServerBackup()).main()
