import os
import socket
from pathlib import Path
from tqdm import tqdm
import Models

user_file = {}
share_queue = []
class sharedFile:
    def __init__(self, file_name, file_path, sender , reciver, file_size):
        self.file_name = file_name
        self.file_path = file_path
        self.sender = sender
        self.reciver = reciver
        self.file_size = file_size

class fileTP:
    def __init__(self, file_name, file_path):
        self.file_name = file_name
        self.file_path = file_path


def reciveFile(client_socket, message, user):
    file_name = message[2]
    file_size = int(message[3])

    path = Path("files").joinpath(user.name)
    path.mkdir(parents=True, exist_ok=True)

    client_socket.sendall(b"ACK|UPLOAD")

    getfile(
        client_socket,
        file_name,
        file_size,
        path,
        user
    )

    return user


def getfile(client_socket, file_name, file_size, path, user):
    received_size = 0
    file_path = path.joinpath(file_name)
    buffer = b""

    print(f"[SERVER] Starting download for {file_name} ({file_size} bytes)...")

    with open(file_path, "wb") as file:
        while received_size < file_size:
            # Ensure we have a complete DATA header: DATA|name|chunk|size|
            while True:
                header_pipe_count = buffer.count(b"|")
                if header_pipe_count >= 4:
                    break

                chunk = client_socket.recv(4096)
                print(f"[SERVER] recv {len(chunk)} bytes, buffer now {len(buffer)+len(chunk)}")
                if not chunk:
                    raise ConnectionError("Client disconnected unexpectedly.")
                buffer += chunk

            # Locate the 4th pipe to separate the header.
            header_end = -1
            pipe_seen = 0
            for index, byte in enumerate(buffer):
                if byte == 124:  
                    pipe_seen += 1
                    if pipe_seen == 4:
                        header_end = index + 1
                        break

            if header_end == -1:
                raise ValueError("Malformed upload packet header.")

            header = buffer[:header_end].decode(errors="replace")
            tokens = header[:-1].split("|")
            if len(tokens) != 4 or tokens[0] != "DATA":
                raise ValueError("Malformed data packet received during upload.")

            packet_file_name = tokens[1]
            chunk_number = int(tokens[2])
            chunk_size = int(tokens[3])

            print(f"[SERVER] parsed header: name={packet_file_name} chunk={chunk_number} size={chunk_size} buffer={len(buffer)}")
            while len(buffer) < header_end + chunk_size:
                chunk = client_socket.recv(4096)
                print(f"[SERVER] recv payload {len(chunk)} bytes, buffer now {len(buffer)+len(chunk)}")
                if not chunk:
                    raise ConnectionError("Client disconnected during chunk stream.")
                buffer += chunk

            payload = buffer[header_end:header_end + chunk_size]
            file.write(payload)
            received_size += len(payload)
            client_socket.sendall(f"ACK|{chunk_number}".encode())

            buffer = buffer[header_end + chunk_size:]

        # After writing all payload bytes, consume the END packet.
        while True:
            if buffer.startswith(b"END|"):
                client_socket.sendall(b"ACK|END")
                break

            chunk = client_socket.recv(4096)
            if not chunk:
                raise ConnectionError("Client disconnected before END packet.")
            buffer += chunk

    if user not in user_file:
        user_file[user.name] = []

    user_file[user.name].append(
        fileTP(
            file_name,
            str(file_path)
        )
    )

    print(f"[SERVER] Successfully received '{file_name}' ({received_size}/{file_size} bytes saved).")


def giveUserFiles(client_socket, user):
    if user.name not in user_file or not user_file[user.name]:
        client_socket.send("No files uploaded yet.".encode())
        return

    file_list = "\n".join([f"{idx+1}. {file.file_name}" for idx, file in enumerate(user_file[user.name])])
    client_socket.send(f"Your files:\n{file_list}".encode())
    return

def fileShareRequest(file_name, sender , reciver):
    fileshare = user_file.get(sender, [])
    for file in fileshare :
        if file.file_name == file_name :
            file_path = Path(file.file_path)
            file_size = file_path.stat().st_size if file_path.exists() else 0
            share_queue.append(sharedFile(file.file_name, file.file_path, sender , reciver, file_size))

def remove_share_file(file_name, sender , reciver):
    for shared in share_queue :
        if shared.file_name == file_name and shared.sender == sender and shared.reciver == reciver :
            share_queue.remove(shared)
        else :
            raise Exception("Shared file not found in queue.")

def send_to_reciver(file_name, sender , reciver):
    for shared in share_queue :
        if shared.file_name == file_name and shared.sender == sender and shared.reciver == reciver :
            reciver_socket = Models.online_users[reciver]
            transfer_file(reciver_socket, shared.file_path, shared.file_name, shared.file_size)
            share_queue.remove(shared)
            if reciver not in user_file:
                user_file[reciver] = []
            user_file[reciver].append(fileTP(shared.file_name, shared.file_path))
        else :
            raise Exception("Shared file not found in queue.")

def transfer_file(client_socket, file_path, file_name, file_size):
    CHUNK_SIZE = 512
    chunk_number = 0

    with open(file_path, "rb") as file, tqdm(
        total=file_size,
        unit="B",
        unit_scale=True,
        desc=f"Uploading {file_name}"
    ) as pbar:

        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            packet = (
                f"DATA|{file_name}|{chunk_number}|{len(chunk)}|"
            ).encode() + chunk

            client_socket.sendall(packet)
            print(f"[CLIENT] sent DATA chunk {chunk_number}, waiting ACK")

            old_timeout = client_socket.gettimeout()
            client_socket.settimeout(None)
            try:
                ack = client_socket.recv(1024).decode()
            finally:
                client_socket.settimeout(old_timeout)

            expected_ack = f"ACK|{chunk_number}"

            if ack != expected_ack:
                raise Exception(
                    f"Expected '{expected_ack}' but got '{ack}'"
                )

            pbar.update(len(chunk))
            chunk_number += 1

    client_socket.sendall(
        f"END|{file_name}".encode()
    )
    print(f"[CLIENT] sent END for {file_name}, waiting ACK|END")

    old_timeout = client_socket.gettimeout()
    client_socket.settimeout(None)
    try:
        ack = client_socket.recv(1024).decode()
    finally:
        client_socket.settimeout(old_timeout)

    if ack != "ACK|END":
        raise Exception(
            f"Expected 'ACK|END' but got '{ack}'"
        )

    print("Upload completed successfully.")