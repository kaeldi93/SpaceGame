import socket
import threading
import time
import socketserver
import spaceWS, WSLogger, game_logic

http_msg = b'GET / HTTP/1.1'

game = ""

class WSHandler(socketserver.BaseRequestHandler):
  def handle(self):
    global game
    handshakes = set()
    handler = spaceWS.Handler(game)
    while True:
      global http_msg

      self.data = self.request.recv(4096)
      if self.data == b"":
        print("Connection closed!")
        return

      WSLogger.log(str(self.data))
      incoming_ip = self.client_address[0]
      if not incoming_ip in handshakes:
        self.data = self.data.strip()
        lines = self.data.split(b"\r\n")
        if not http_msg in lines:
          print("Not websocket request!")
        else:
          lines.remove(http_msg)
          headers = {}
          for l in lines:
            sline = l.decode('utf-8')
            colon_loc = sline.index(': ')
            if colon_loc == -1 or colon_loc == 0 or colon_loc > len(sline)-1:
              continue
            headers[sline[:colon_loc]] = sline[colon_loc+2:]

          self.data = spaceWS.handshake(headers)
          self.request.sendall(self.data)
          handshakes.add(incoming_ip)
      else:
        # TODO: Handle pings and pongs.
        if handler.handle(self.data):
          if handler.status == "reply_ready":
            self.data = handler.getMessage()
            bytedata = self.data.encode('utf-8')
            frame = handler.frameForMessage(bytedata, 1)
            self.request.sendall(frame)
          elif handler.status == "close":
            frame = handler.frameForMessage(b"", 8)
            self.request.sendall(frame)
            handshakes.remove(incoming_ip)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
  # Ctrl-C will cleanly kill all spawned threads
  daemon_threads = True
  # much faster rebinding
  allow_reuse_address = True

# Exists for testing purposes. Largely outdated, but kept around just in case.
def client(ip, port, message):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((ip, port))
  print("Connected!")
  try:
    sock.sendall(bytes(message, 'ascii'))
    print("Sent!")
    response = str(sock.recv(1024), 'ascii')
    print("Received: {}".format(response))
  finally:
    sock.close()

def startServer():
  global game
  
  game = game_logic.AsteroidsGame()
  game_thread = threading.Thread(target=game.loop, name="game_thread")
  game_thread.start()
  
  HOST, PORT = "", 8080
  print(str(HOST) + " " + str(PORT))

  server = ThreadedTCPServer((HOST, PORT), WSHandler)
  ip, port = server.server_address
  print(str(ip) + " " + str(port))

  server.serve_forever()

if __name__ == "__main__":
  startServer()


