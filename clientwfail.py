import socket
import threading
import time

class RTSPClient:
    def __init__(self, server_addr, server_port):
        self.server_addr = server_addr
        self.server_port = server_port
        self.connected = False
        self.client_socket = None

    def handle_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_addr, self.server_port))
            print(f"Conectado a {self.server_addr}:{self.server_port}")
            self.connected = True

            while self.connected:
                # Lógica para interagir com o servidor. Esta é uma simulação básica, você vai querer expandir isto.
                self.client_socket.sendall(b"REQUEST")
                data = self.client_socket.recv(1024)
                if not data:
                    # A conexão foi fechada pelo servidor.
                    self.connected = False
                else:
                    print(f"Recebido do servidor: {data.decode()}")
                    time.sleep(1)  # Para simular alguma operação em curso.

        except Exception as e:
            self.connected = False
            print(f"Erro ao conectar a {self.server_addr}:{self.server_port}: {e}")

        finally:
            if self.client_socket:
                self.client_socket.close()

def main():
    server_addr_primary = 'localhost'
    server_port_primary = 5050
    server_addr_backup = '127.0.0.1'
    server_port_backup = 5051

    client_primary = RTSPClient(server_addr_primary, server_port_primary)
    client_backup = RTSPClient(server_addr_backup, server_port_backup)

    thread_primary = threading.Thread(target=client_primary.handle_server)
    thread_backup = threading.Thread(target=client_backup.handle_server)

    # Tente conectar ao servidor principal primeiro.
    thread_primary.start()
    thread_primary.join(5)  # Aguarde até 5 segundos para ver se podemos nos conectar ao servidor principal.

    # Se não conseguirmos nos conectar ao servidor principal, tente o servidor de backup.
    if not client_primary.connected:
        thread_backup.start()
        thread_backup.join()

if __name__ == "__main__":
    main()
