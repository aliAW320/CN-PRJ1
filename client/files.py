from tkinter import Tk, filedialog

from tqdm import tqdm

import os

from pathlib import Path





def select_file():

    root = Tk()

    root.withdraw()



    file_path = filedialog.askopenfilename()



    root.destroy()

    return file_path





def sendFile(file_path, client_socket):

    file_name = os.path.basename(file_path)

    file_size = os.path.getsize(file_path)



    client_socket.sendall(

        f"CTRL|UPLOAD|{file_name}|{file_size}".encode()

    )



    old_timeout = client_socket.gettimeout()

    client_socket.settimeout(None)

    try:

        ack = client_socket.recv(1024).decode()

    finally:

        client_socket.settimeout(old_timeout)



    if ack != "ACK|UPLOAD":

        print("Upload request rejected")

        return



    transfer_file(

        client_socket,

        file_path,

        file_name,

        file_size

    )





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





def recive_file(client_socket, file_name, sender):

    """Receive a file from the server (file share) and save it to files/sender/"""

    path = Path("files").joinpath(sender)

    path.mkdir(parents=True, exist_ok=True)

    file_path = path.joinpath(file_name)

   

    received_size = 0

    buffer = b""

   

    print(f"[CLIENT] Waiting to receive '{file_name}' from {sender}...")

   

    with open(file_path, "wb") as file:

        while True:

            # Wait for DATA packet header or END packet

            while True:

                header_pipe_count = buffer.count(b"|")

                if header_pipe_count >= 4 or buffer.startswith(b"END|") or buffer.startswith(b"ERR|"):

                    break

               

                chunk = client_socket.recv(4096)

                if not chunk:

                    raise ConnectionError("Server disconnected unexpectedly.")

                buffer += chunk

           

            # Check for END packet

            if buffer.startswith(b"END|"):

                client_socket.sendall(b"ACK|END")

                print(f"[CLIENT] File receive completed for '{file_name}'.")

                break

            if buffer.startswith(b"ERR|"):

                raise Exception(buffer.decode(errors="replace"))

           

            # Parse the DATA header

            header_end = -1

            pipe_seen = 0

            for index, byte in enumerate(buffer):

                if byte == 124:  # b'|'

                    pipe_seen += 1

                    if pipe_seen == 4:

                        header_end = index + 1

                        break

           

            if header_end == -1:

                raise ValueError("Malformed data packet received.")

           

            header = buffer[:header_end].decode(errors="replace")

            tokens = header[:-1].split("|")

            if len(tokens) != 4 or tokens[0] != "DATA":

                raise ValueError("Malformed data packet header.")

           

            packet_file_name = tokens[1]

            chunk_number = int(tokens[2])

            chunk_size = int(tokens[3])

           

            # Read full chunk payload

            while len(buffer) < header_end + chunk_size:

                chunk = client_socket.recv(4096)

                if not chunk:

                    raise ConnectionError("Server disconnected during chunk stream.")

                buffer += chunk

           

            payload = buffer[header_end:header_end + chunk_size]

            file.write(payload)

            received_size += len(payload)

            client_socket.sendall(f"ACK|{chunk_number}".encode())

           

            buffer = buffer[header_end + chunk_size:]

   

    print(f"[CLIENT] Successfully received '{file_name}' from {sender}.")
