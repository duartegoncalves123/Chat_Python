import pygame
from datetime import datetime

# Password para o upgrade a super-moderador
PASSWORD_SUPERMOD = '123456'

# Classe que representa o #general
class Hall:
    def __init__(self, name):
        self.rooms = {}  # {room_name: Room}
        self.clients = [] # Clientes que estão no chat
        self.clients_inHall = [] # Clientes que estão no #general no momento
        self.clients_superMod = [] # Clientes com estatuto de super-moderador
        self.room_player_map = {}  # {playerName: roomName}
        self.name = name # Nome do Hall

    def welcome_new(self, new_client):  # Recebe um novo cliente no Hall
        msg = 'Welcome to ' + self.name + ', ' + new_client.client_name
        if new_client not in self.clients:
            self.clients.append(new_client)
        self.clients_inHall.append(new_client)
        return msg

    def check_Username(self, client):  # Verifica se já existe um utilizador com o nome que o cliente que está por parâmetro possui
        for x in self.clients:
            if x.client_name == client.client_name:
                return True
        return False

    def broadcastHall(self, msg, client):  # Broadcast da mensagem no #general
        new_msg = '(' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ') ' + client.client_name + ': ' + msg + '\n'
        for x in self.clients_inHall:
            x.sock.sendall(new_msg.encode())

    def broadcastNews(self, msg, client):  #Broadcast de um aviso no #general
        for x in self.clients_inHall:
            if x.sock != client.sock:
                x.sock.sendall(msg.encode())

    def list_rooms(self, client):  # Lista todas as salas existentes com o número de clientes que estão lá dentro
        if len(self.rooms) == 0:
            msg = 'There are no existing rooms! Use [instructions] to learn how to create your own!'
            client.sock.sendall(msg.encode())
        else:
            count = 0
            msg = 'Listing current rooms: '
            for room in self.rooms:
                if count == len(self.rooms):
                    msg += room + ": " + str(len(self.rooms[room].clients)) + " client(s)"
                else:
                    msg += room + ": " + str(len(self.rooms[room].clients)) + " client(s) / "

            client.sock.sendall(msg.encode())

    def handle_msg(self, client, msg):  # Irá ver o que é preciso de fazer com a mensagem
        instructions = 'Instructions: [list] to list all rooms / [join -room_name-] to join/create/switch to a room / [upgradeSuper -pass-] to upgrade yourself to a Super-Moderator / [warnAll -msg-] to send a msg to all rooms and hall / [addMod -username-] to add a moderator to your room / [pm -username- -your msg-] to send a private message / [exit] to quit. Otherwise start typing and enjoy!'
        if msg == 'instructions':  # Pretende ler as instruções
                client.sock.sendall(instructions.encode())

        elif msg == 'list':  # Chama a função list_rooms
            self.list_rooms(client)

        elif msg == 'join #general':  # O cliente pretende voltar ao #general
            if client not in self.clients_inHall:  # Verifica se o cliente não está atualmente no #general
                old_room = self.room_player_map[client.client_name]  # Vê a sala em que o cliente está atualmente presente
                self.rooms[old_room].remove_client_fromRoom(client)  # Remove o cliente da sala
                if client.client_name in self.room_player_map: del self.room_player_map[client.client_name]  # Se o cliente estiver presente do dicionário room_player_map remove-o
                self.clients_inHall.append(client)  # Junta o cliente ao array dos clientes presentes no #general
                entryMsg = client.client_name + ' has joined #general'
                self.broadcastNews(entryMsg, client)
                client.sock.sendall('You have joined #general'.encode())
            else:
                client.sock.sendall('You are already in #general!'.encode())

        elif 'join' in msg:
            in_room = False
            if len(msg.split()) == 2:
                room_name = msg.split()[1]

                if client.client_name in self.room_player_map:  # Pode estar a querer trocar de sala
                    if self.room_player_map[client.client_name] == room_name: # Já se encontra na sala em que está a pretender entrar
                        aux = 'You are already in room: ' + room_name
                        client.sock.sendall(aux.encode())
                        in_room = True

                    else:  # Troca
                        if room_name in self.rooms:
                            if client not in self.rooms[room_name].bannedList: # Verifica se o cliente está banido da sala ou não
                                if client in self.clients_inHall:  # Se o cliente estiver no #general é removido
                                    self.clients_inHall.remove(client)
                                old_room = self.room_player_map[client.client_name] # Vê a sala em que o cliente está atualmente presente
                                self.rooms[old_room].remove_client_fromRoom(client) # Remove o cliente da sala
                            else:
                                client.sock.sendall('You are banned from this room'.encode())

                if not in_room:
                    if not room_name in self.rooms:  # Pretende criar uma sala nova
                        room_name = '#' + room_name
                        new_room = Room(room_name)
                        self.rooms[room_name] = new_room
                        new_room.moderators.append(client) # Adiciona o criador como um moderador da sala

                    if client not in self.rooms[room_name].bannedList: # Junta o cliente à sala se não estiver banido
                        if client in self.clients_inHall:
                            self.clients_inHall.remove(client)
                        self.rooms[room_name].clients.append(client)
                        self.rooms[room_name].welcome_client(client)
                        self.room_player_map[client.client_name] = room_name
                    else:
                        client.sock.sendall('You are banned from this room'.encode())
            else: # Se o comando for mal implementado serão enviadas as instruçõoes ao cliente
                client.sock.sendall(instructions.encode())

        elif 'pm' in msg: # Envia uma mensagem privada a um utilizador
            msg_receiver = msg.split()[1] # Receptor da mensagem
            found_user = False
            for x in self.clients:
                if x.client_name == msg_receiver:
                    found_user = True
                    username = msg.split()[1]
                    aux = msg.split()[2]
                    new_msg = '(' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ') ' + username + ': ' + aux + '\n'
                    x.sock.sendall(new_msg.encode())
                    # Play sound
                    pygame.mixer.init()
                    pygame.mixer.music.load("stairs.mp3")
                    pygame.mixer.music.play()
            if found_user == False: # Cliente não existe
                client.sock.sendall('User does not exist!'.encode())

        elif 'addMod' in msg: # Adiciona um moderador a uma sala
            client_toAddName = msg.split()[1]
            found_user = False
            for x in self.clients:
                if x.client_name == client_toAddName:
                    found_user = True
                    client_toAdd = x
                    self.rooms[self.room_player_map[client.client_name]].add_moderator(client, client_toAdd) # Chama a função add_moderator na sala em questão
            if found_user == False:
                client.sock.sendall('User does not exist!'.encode())

        elif 'ban' in msg: # Ban um utilizador
            client_toBanName = msg.split()[1] # Nome do cliente a banir
            client_toBan = None
            for x in self.clients:
                if x.client_name == client_toBanName:
                    client_toBan = x
            check = self.rooms[self.room_player_map[client.client_name]].ban_client(client, client_toBan) # Chama a função ban_clientt na sala em questão
            if check == True: # Se o ban ocorrer a variável check irá ficar True e irá correr as linhas para remover o utilizador da sala e adicionálo ao #general
                self.rooms[self.room_player_map[client_toBan.client_name]].remove_client_fromRoom(client_toBan)
                del self.room_player_map[client_toBan.client_name]
                self.clients_inHall.append(client_toBan)

        elif 'warnAll' in msg: # Mensagem global para todos os utilizadores
            new_msg = msg.split(' ', 1)[1]
            final_Msg = 'GLOBAL MESSAGE: ' + new_msg
            if client in self.clients_superMod: # Verifica se o utilizador a enviar a mensagem possui o estatudo de super-moderador
                for x, y in self.rooms.items():
                    y.broadcastNews_inRoom(final_Msg)
                for x in self.clients_inHall:
                    x.sock.sendall(final_Msg.encode())
            else:
                client.sock.sendall('You are not a super moderator'.encode())

        elif 'upgradeSuper' in msg: # Irá dar estatuto de super-moderador se acertar na palavra-passe
            password = msg.split()[1]
            if password == PASSWORD_SUPERMOD:
                self.clients_superMod.append(client)
                client.sock.sendall('Upgraded to Super Moderator!'.encode())
            else:
                client.sock.sendall('Wrong password!'.encode())

        else:
            # Verifica se está numa sala primeiro
            if client.client_name in self.room_player_map:
                self.rooms[self.room_player_map[client.client_name]].broadcast(client, msg)
                # Play sound
                pygame.mixer.init()
                pygame.mixer.music.load("stairs.mp3")
                pygame.mixer.music.play()
            else: # Envia mensagem para o Hall
                self.broadcastHall(msg, client)
                # Play sound
                pygame.mixer.init()
                pygame.mixer.music.load("stairs.mp3")
                pygame.mixer.music.play()

    def remove_client(self, client): # Função para remover o cliente do chat
        if client in self.clients:
            self.clients_inHall.remove(client)
        if client.client_name in self.room_player_map:
            self.rooms[self.room_player_map[client.client_name]].remove_client_fromRoom(client)
            del self.room_player_map[client.client_name]
        self.clients.remove(client)


class Room:
    def __init__(self, name):
        self.clients = []  # Lista dos clientes presentes na sala
        self.moderators = []  # Lista dos moderadores da sala
        self.bannedList = []  # Lista dos clientes banidos da sala
        self.name = name  # Nome da sala

    def welcome_client(self, client): # Recebe o cliente novo na sala
        msg = self.name + " welcomes: " + client.client_name + '\n'
        for x in self.clients:
            x.sock.sendall(msg.encode())

    def add_moderator(self, client, client_toAdd): # Adiciona um cliente para moderador da sala
        if client in self.moderators and client_toAdd in self.clients: # Verifica se o cliente que está a promover é um moderador e se o cliente que está a ser promovido está na sala
            self.moderators.append(client_toAdd)
            msg = client_toAdd.client_name + ' was promoted to moderator'
            self.broadcastNews_inRoom(msg)
        else:
            msg = 'You do not have permission to add new moderators'
            self.broadcastNews_inRoom(msg)

    def ban_client(self, client, client_toBan): # Ban um cliente da sala
        if client in self.moderators and client_toBan in self.clients: # Verifica se o cliente que está a banir é um moderador e se o cliente que está a ser banido está na sala
            self.bannedList.append(client_toBan)
            msg = client_toBan.client_name + ' was banned'
            self.broadcastNews_inRoom(msg)
            return True
        check = 0
        if client not in self.moderators:
            check = 1
            client.sock.sendall('You do not have the permission to ban other users'.encode())
        if client_toBan not in self.clients and check == 0:
            client.sock.sendall('User is not in the room'.encode())
        return False

    def broadcast(self, client, msg): # Broadcast de uma mensagem para a sala
        new_msg = '(' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ') ' + client.client_name + ': ' + msg + '\n'
        for x in self.clients:
            x.sock.sendall(new_msg.encode())

    def broadcastNews_inRoom(self, msg): # Broadcast de um aviso na sala
        for client in self.clients:
            client.sock.sendall(msg.encode())

    def remove_client_fromRoom(self, client): # Remove um cliente da sala
        self.clients.remove(client)
        leave_msg = client.client_name + ' has left the room\n'
        self.broadcastNews_inRoom(leave_msg)
