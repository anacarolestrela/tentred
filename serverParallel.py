import socket
import threading

def handle_server(server_addr, server_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_addr, server_port))
            print(f"Conectado a {server_addr}:{server_port}")

            # Lógica para interagir com o servidor (enviar comandos RTSP, receber dados RTP, etc.).
            # Substitua isso pela lógica específica do seu cliente.

    except Exception as e:
        print(f"Erro ao conectar a {server_addr}:{server_port}: {e}")
        # Lide com erros ou adote uma estratégia de reconexão.

def main():
    server_addr_primary = 'localhost'  # Endereço do servidor principal
    server_port_primary = 5050  # Porta do servidor principal
    server_addr_backup = '127.0.0.1'  # ou o endereço real do servidor de backup
    server_port_backup = 5051  # Porta do servidor de backup

    # Crie duas threads para lidar com as conexões aos servidores principal e de backup.
    thread_primary = threading.Thread(target=handle_server, args=(server_addr_primary, server_port_primary))
    thread_backup = threading.Thread(target=handle_server, args=(server_addr_backup, server_port_backup))

    # Inicie as threads.
    thread_primary.start()
    thread_backup.start()

    # Espere até que ambas as threads terminem.
    thread_primary.join()
    thread_backup.join()

if __name__ == "__main__":
    main()

