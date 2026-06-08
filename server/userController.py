from Models import User, Message, list_online_users
def handle_user(client_socket, client_address):
    user = None
    print(f"[USER] Connected: {client_address}")
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if data:
                print(f"[RECEIVED] From {client_address}: {data}")
                massage = data.split("|")
                if massage[0] == "CTRL":
                   user = CTRL(client_socket, massage ,user)
                elif massage[0] == "DATA":
                    DATA(client_socket, massage[1], massage[2], massage[3])
                else : 
                    pass
                if massage[1] == 'EXIT' : 
                    break
        except ConnectionResetError:
            print(f"[USER] Disconnected: {client_address}")
              
            client_socket.close()
            break

def CTRL(client_socket, massage , user):
    
    command = massage[1]
    if command == "REGISTER":
        name = massage[2]
        password = massage[3]
        if User.register(name, password) and not user:
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
        state , login_massage ,user = User.login(name, password)
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
            client_socket.send("logout failed".encode())
            return user


    elif command == "LIST_USERS":
        state , online_users = list_online_users(user)
        if state :
            if isinstance(online_users , str):
                client_socket.send("you are the only user online")
            else :
                client_socket.send(f"online users|{','.join(online_users)}".encode())
        else :
            client_socket.send("failed to retrieve online users".encode())
        return user
    elif command == "EXIT":
        if user.exit() :
            client_socket.send("GOODBYE".encode())
            client_socket.close()
        else :
            client_socket.send("unexpected error".encode())
            return user
        