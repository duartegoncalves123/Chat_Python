import socket
import threading
import tkinter
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# Define socket host and port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8000
global is_running
is_running = True

def receives_thread(client_socket):
    '''while is_running:
        res = client_socket.recv(4096).decode('utf-8')
        msg_list.insert(tkinter.END, res)
    # Close socket
    client_socket.close()'''

    while True:
        try:
            res = client_socket.recv(4096).decode('utf-8')
            msg_list.insert(tkinter.END, res)
        except OSError:  # Possibly client has left the chat.
            client_socket.close()
            global is_running
            is_running = False
            break

def send(event = None):
    msg = msg_text.get()
    msg_text.set("")  # Clears input field.
    client_socket.sendall(msg.encode())
    if msg == "exit":
        global is_running
        is_running = False
        client_socket.close()
        top.quit()

def on_closing(event=None):
    msg_text.set("exit")
    send()

# Create socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server
client_socket.connect((SERVER_HOST, SERVER_PORT))


# Tkinter GUI
top = tkinter.Tk()
top.title('Chat')

frame = tkinter.Frame(top)
msg_text = tkinter.StringVar()
msg_text.set('Insert username')
scrollbar = tkinter.Scrollbar(frame)
msg_list = tkinter.Listbox(frame, height=15, width=90, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
frame.pack()

entry_field = tkinter.Entry(top, textvariable=msg_text)
entry_field.bind("<Return>", send)
entry_field.pack()
send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack()

top.protocol("WM_DELETE_WINDOW", on_closing)

# Cria thread
thread = threading.Thread(target=receives_thread, args=(client_socket,))
thread.start()
tkinter.mainloop()

while is_running == True:
    username = msg_text.get()
    client_socket.sendall(username.encode())
    res = client_socket.recv(1024).decode()
    if res == 'Username Accepted':
        break
    msg_list.insert(tkinter.END, 'Username already exists! Choose another one')
