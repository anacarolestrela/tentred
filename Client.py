from tkinter import *
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk
import socket, threading, sys, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename, backup_server=None):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.backupServer = backup_server
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer(self.serverAddr, self.serverPort)
		self.frameNbr = 0
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
  
		
	def createWidgets(self):
		"""Build do GUI."""
		# botao Setup 
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# botao Play 		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# botao Pause 			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		#  botao Teardown 
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# nome na caixa do filme
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""	acoes do botão de setup"""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""acoes do botao teardown."""
		self.sendRtspRequest(self.TEARDOWN)		
		self.master.destroy() # Close the gui window
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # apaga cache

	def pauseMovie(self):
		"""acoes do botao de pausa."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""acoes do botao de play."""
		if self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):		
		"""aguardando pacotes"""
		while True:
			try:
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					
					currFrameNbr = rtpPacket.seqNum()
					print("Current Seq Num: " + str(currFrameNbr))
										
					if currFrameNbr > self.frameNbr: # discarta o ultimo pacote
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# parar de ouvir quando aperatr teardown
				if self.playEvent.isSet(): 
					break
				
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break
					
	def writeFrame(self, data):
		"""mostrar o frame recebitp"""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename
	
	def updateMovie(self, imageFile):
		"""atualizar o arquivo de imagem com o frame"""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo
		
	def connectToServer(self, server_addr, server_port):
		"""iniciar a secao"""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkMessageBox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""enviar o request"""	
		
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			# atualiza a sequencia
			self.rtspSeq = 1
			
			# prepara o pacote a ser enviado
			request = "SETUP " + str(self.fileName) + "\n " + str(self.rtspSeq) + " \n RTSP/1.0 RTP/UDP " + str(self.rtpPort)
			
			self.rtspSocket.send(request.encode("utf-8"))
			# atualiza a sequencia
			self.requestSent = self.SETUP
		
		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			# atualiza a sequencia
			self.rtspSeq = self.rtspSeq + 1
			
			# escreve o rtsp a ser enviado
			request = "PLAY " + "\n " + str(self.rtspSeq)

			self.rtspSocket.send(request.encode("utf-8"))
			print('-'*60 + "\nPLAY request sent to Server...\n" + '-'*60)
			# atualiza a sequencia
			self.requestSent = self.PLAY
		
		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# atualiza a sequencia
			self.rtspSeq = self.rtspSeq + 1
			
			# escreve o rtsp a ser enviado
			request = "PAUSE " + "\n " + str(self.rtspSeq)
			
			self.rtspSocket.send(request.encode("utf-8"))
			print('-'*60 + "\nPAUSE request sent to Server...\n" + '-'*60)
			# atualizacao dos requests enviados
			self.requestSent = self.PAUSE

			
		# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# atualiza a sequencia

			self.rtspSeq = self.rtspSeq + 1
			
			request = "TEARDOWN " + "\n " + str(self.rtspSeq)
			
			self.rtspSocket.send(request.encode("utf-8"))
			print('-'*60 + "\nTEARDOWN request sent to Server...\n" + '-'*60)
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.TEARDOWN
		else:
			return
		
		# envia solicitacao pelo socket
		
		print('\nData sent:\n' + request)
	
	def recvRtspReply(self):
		while True:
			reply = self.rtspSocket.recv(1024)
			
			if reply: 
				self.parseRtspReply(reply.decode("utf-8"))
			
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])
		
		# processar apenas se o porta do server estiver correta
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# id novo
			if self.sessionId == 0:
				self.sessionId = session
			
			# pocessar apenas se o id for o mesmo
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:

						# atualizacao de estado
						self.state = self.READY
						
						# abre a porta rtp
						self.openRtpPort() 
					elif self.requestSent == self.PLAY:
						# self.state = ...
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						# self.state = ...
						self.state = self.READY
						self.playEvent.set()
					elif self.requestSent == self.TEARDOWN:
						# self.state = ...
						self.state = self.INIT
						
						# Flag de teardow para fechar o socket.
						self.teardownAcked = 1 
	
	def openRtpPort(self):
		"""abre o socket ."""

		self.rtpSocket.settimeout(0.5)
		# define valor de timeout do socket para 0.5sec
		
		try:
			# faz o bind com a porta oferecida pelo cliente
			self.rtpSocket.bind((self.serverAddr, self.rtpPort)) #sempre maior que 1024
			print("Bind RtpPort Success")
		except:
			tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

	def handler(self):
		"""botao de encerrar secao"""
		self.pauseMovie()
		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else: 
			self.playMovie()