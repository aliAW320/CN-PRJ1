import socket
import threading
import userController
PATH = "127.0.0.1"
PORT = 8000
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((PATH, PORT))
    server.listen()
    print(f"[SERVER] Listening on {PATH}:{PORT}")
    
    while True:
        client_socket, client_address = server.accept()
        
        client_thread = threading.Thread(target=userController.handle_user, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    start_server()
    