import socket
import threading
import time
def listen_to_server(client_socket):
    print("Listening for messages from the server...")
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if data:
                print(f"\n{data}\n")
        except ConnectionResetError:
            print("Connection to the server was lost.")
            break        
            


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 8000))
print("Connected to the server.")
listener_thread = threading.Thread(target=listen_to_server, args=(client_socket,), daemon=True)
listener_thread.start()

while True:
    message = input("Enter a message to send (or 'exit' to quit): ")
    massage = message.split(" ")
    if massage[0]== "REGISTER" :
        client_socket.send(f"CTRL|REGISTER|{massage[1]}|{massage[2]}".encode())
    elif massage[0]== "LOGIN" :
        client_socket.send(f"CTRL|LOGIN|{massage[1]}|{massage[2]}".encode())
    elif massage[0]== "LOGOUT" :
        client_socket.send(f"CTRL|LOGOUT".encode())
    elif massage[0]== "LIST_USERS" :
        client_socket.send(f"CTRL|LIST_USERS".encode())
    elif massage[0] == "EXIT" : 
        client_socket.send("CTRL|EXIT".encode())
        time.sleep(0.5)
        break
    elif massage[0] == "CHAT" :
        client_socket.send(f"DATA|CHAT|{massage[1]}|{" ".join(massage[2:])}".encode())



    #avoid thered race condition for printing    
    time.sleep(0.1)


