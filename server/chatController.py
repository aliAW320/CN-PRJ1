import Models
def handle_chat(client_socket, reciver , content , user):
    if reciver in Models.online_users :
        sender = user.name
        reciver_socket = Models.online_users[reciver]
        reciver_socket.send(f"Message from {sender}: {content}".encode())
        print(reciver_socket)
        client_socket.send(f"Message sent to {reciver}".encode())
    else :
        client_socket.send(f"User '{reciver}' is not online.".encode())
