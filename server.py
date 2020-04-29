import pygame
import socket

# Define socket host and port
import threading

from Hall import Hall

class Client:
    def __init__(self, sock, client_name):
        self.sock = sock
        self.client_name = client_name

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000

# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print('Listening on port %s ...' % SERVER_PORT)

clients = []
hall = Hall('#general')

def handle_client(client):
    while True:
        # Recebe mensagem do cliente
        msg = client.sock.recv(1024).decode()

        if msg == 'exit':
            goodbyeMsg = 'exit'
            client.sock.sendall(goodbyeMsg.encode())

            name = client.client_name
            clients.remove(client)
            hall.remove_client(client)
            leaveMsg = name + ' has left the chat'
            for client in clients:
                client.sock.sendall(leaveMsg.encode())
            break

        if msg != 'exit':
            # Imprime a mensagem do cliente
            hall.handle_msg(client, msg)

while True:
    # Wait for client connections
    client_connection, client_address = server_socket.accept()

    # Obtém o nome do utilizador
    while True:
        name = client_connection.recv(1024).decode()
        client = Client(client_connection, name)
        if hall.check_Username(client) == False:
            clients.append(client)
            client.sock.sendall('Username Accepted'.encode())
            break
        else:
            client.sock.sendall('Username Declined'.encode())

    # Hall cumprimenta o novo cliente
    entryMsg = hall.welcome_new(client)

    msg = 'User ' + name + ' is now connected!'
    hall.broadcastNews(msg, client)
    client.sock.sendall(entryMsg.encode())

    # Cria Threads
    thread = threading.Thread(target=handle_client, args=(client, ))
    thread.start()