import socket
import time
import threading
from files import sendFile, select_file, recive_file
file_transfer_active = False

def listen_to_server(client_socket):
    global file_transfer_active
    print("Listening for messages from the server...")
    while True:
        try:
            if file_transfer_active:
                time.sleep(0.1)
                continue
            
            data = client_socket.recv(1024).decode()
            if data:
                print(f"\n{data}\n")
                if data.startswith("login success"):
                    user = data.split("")[-1]  
        except socket.timeout:
            pass
        except ConnectionResetError:
            print("Connection to the server was lost.")
            break
        except Exception:
            break

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(0.2)

client_socket.connect(('127.0.0.1', 8000))
print("Connected to the server.")

# راه‌اندازی ترد پس‌زمینه برای دریافت پیام‌ها
listener_thread = threading.Thread(target=listen_to_server, args=(client_socket,), daemon=True)
listener_thread.start()

while True:
    message = input("Enter a message to send (or 'exit' to quit): ").strip()
    if not message:
        continue
        
    massage = [part for part in message.split(" ") if part]
    command = massage[0].upper() 

    if command == "REGISTER":
        client_socket.send(f"CTRL|REGISTER|{massage[1]}|{massage[2]}".encode())
    elif command == "LOGIN":
        client_socket.send(f"CTRL|LOGIN|{massage[1]}|{massage[2]}".encode())
    elif command == "LOGOUT":
        client_socket.send(f"CTRL|LOGOUT".encode())
    elif command == "LIST_USERS":
        client_socket.send(f"CTRL|LIST_USERS".encode())
    elif command == "EXIT": 
        client_socket.send("CTRL|EXIT".encode())
        time.sleep(0.5)
        break
    elif command == "LIST_FILES":
        client_socket.send(f"CTRL|LIST_FILES".encode())
    elif command == "CHAT":
        client_socket.send(f"DATA|CHAT|{massage[1]}|{' '.join(massage[2:])}".encode())
    elif command == "UPLOAD":
        file_path = select_file()
        if file_path: 
            try:
                file_transfer_active = True
                time.sleep(0.2) 
                sendFile(file_path, client_socket)
            except Exception as e:
                print(f"Error during upload: {e}")
            finally:
                file_transfer_active = False
                client_socket.settimeout(0.2)
        else:
            print("Upload cancelled: No file selected.")
    elif command == "SHARE_FILE":
        file_name = massage[1]
        reciver = massage[2]
        client_socket.send(f"CTRL|SHARE_FILE|{file_name}|{reciver}".encode())

    elif command == "REJECT_FILE":
        file_name = massage[1]
        sender = massage[2]
        client_socket.send(f"DATA|REJECT_FILE|{file_name}|{sender}".encode())

    elif command == "ACCEPT_FILE":
        file_name = massage[1]
        sender = massage[2]
        
        file_transfer_active = True
        time.sleep(0.3) 
        
        client_socket.send(f"DATA|ACCEPT_FILE|{file_name}|{sender}".encode())
        
        try:
            recive_file(client_socket, file_name, sender )
        except Exception as e:
            print(f"Error during file receive: {e}")
        finally:
            file_transfer_active = False
            client_socket.settimeout(0.2)
                
    time.sleep(0.1)