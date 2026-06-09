import Models
from chatController import handle_chat
from fileController import reciveFile , giveUserFiles , fileShareRequest , remove_share_file , send_to_reciver
def handle_user(client_socket, client_address):
    user = None
    print(f"[USER] Connected: {client_address}")
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if data :
                print(f"[RECEIVED] From {client_address}: {data}")
                massage = data.split("|")
                if massage[0] == "CTRL":
                   user = CTRL(client_socket, massage ,user)
                elif massage[0] == "DATA":
                    DATA(client_socket, massage , user)
                else : 
                    pass
                if massage[1] == 'EXIT' : 
                    break
        except ConnectionResetError:
            print(f"[USER] Disconnected: {client_address}")
            if user :
                user.exit()
            client_socket.close()
            break

def CTRL(client_socket, massage , user):
    
    command = massage[1]
    if command == "REGISTER":
        name = massage[2]
        password = massage[3]
        if Models.User.register(name, password) and not user:
            print(f"[REGISTER] User '{name}' registered successfully.")
            client_socket.send("register success".encode())
            return None
        else:
            print(f"[REGISTER] User '{name}' already exists.")
            client_socket.send("register failed".encode())
            return user

    elif command == "LOGIN":
        name = massage[2]
        password = massage[3]
        state , login_massage ,user = Models.User.login(name, password , client_socket)
        if state :
            print(f"[LOGIN] User '{name}' logged in successfully.")
            client_socket.send("login success".encode())
            return user
        else:
            print(f"[LOGIN] Failed to log in user  '{name}' , {login_massage}")
            client_socket.send("login failed".encode())
            return None


    elif command == "LOGOUT":
        if user.logout():
            print(f"[LOGOUT] User '{user.name}' logged out successfully.")
            client_socket.send("logout success".encode())
            return None
        else:
            print(f"[LOGOUT] Failed to log out user '{user.name}'.")
            client_socket.send(f"[LOGOUT] Failed to log out user '{user.name}'".encode())
            return user


    elif command == "LIST_USERS":
        state , online_users = Models.list_online_users(user)
        if state :
            if isinstance(online_users , str):
                client_socket.send("you are the only user online".encode())
            else :
                client_socket.send(f"online users|{','.join(online_users)}".encode())
        else :
            client_socket.send("failed to retrieve online users".encode())
        return user
    elif command == "LIST_FILES":
        if not user :
            client_socket.send("you must login first".encode())
            return user
        else :
            giveUserFiles(client_socket, user)
            return user



    elif command == "UPLOAD" :
        if not user :
            client_socket.send("you must login first".encode())
            return user
        else :
            return reciveFile(client_socket, massage, user)
        
    elif command == "SHARE_FILE" :
        file_name = massage[2]
        reciver = massage[3]
        if not user :
            client_socket.send("you must login first".encode())
            return user
        state, online_user_list = Models.list_online_users(user)
        if not state or not isinstance(online_user_list, list) or reciver not in online_user_list:
            client_socket.send(f"user '{reciver}' is not online".encode())
            return user
        else :
            client_socket.send(f"File share request sent to {reciver}".encode())
            print("stuck before socket")
            reciver_socket = Models.online_users[reciver]
            print("stuck before req")
            fileShareRequest(file_name, user.name, reciver)
            print("stuck before send")
            reciver_socket.send(f"User '{user.name}' want share a file with you: {file_name}".encode())
            return user

    elif command == "REJECT_FILE" :
        file_name = massage[2]
        sender = massage[3]
        remove_share_file(file_name, sender , user.name)
        reciver_socket = Models.online_users[reciver]
        sender_socket.send(f"User '{user.name}' rejected your file share request: {file_name}".encode())
        return user

    elif command == "ACCEPT_FILE" :
        file_name = massage[2]
        sender = massage[3]
        try:
            send_to_reciver(file_name, sender, user.name)
            client_socket.send(f"File '{file_name}' transfer completed.".encode())
        except Exception as e:
            client_socket.send(f"Error transferring file: {str(e)}".encode())
            return user
        sender_socket = Models.online_users.get(sender)
        if sender_socket:
            sender_socket.send(f"User '{user.name}' accepted your file share request: {file_name}".encode())
        return user

    elif command == "EXIT":
        if user.exit() :
            client_socket.send("GOODBYE".encode())
            client_socket.close()
        else :
            client_socket.send("unexpected error".encode())
            return user
def DATA(client_socket, massage , user):
    command = massage[1]
    if command =="CHAT":
        receiver = massage[2]
        content = " ".join(massage[3:]) 
        handle_chat(client_socket, receiver , content , user)
