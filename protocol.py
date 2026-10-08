
import json
import os


CHUNK_SIZE = 64 * 1024


def create_hello_message(name, port):
    message = {
        "type": "HELLO",
        "name": name,
        "port": port
    }

    return json.dumps(message)


def create_hello_ack_message(name, port):
    message = {
        "type": "HELLO_ACK",
        "name": name,
        "port": port
    }

    return json.dumps(message)


def send_message(sock, message):
    message_bytes = message.encode("utf-8")

    message_length = len(message_bytes)

    header = message_length.to_bytes(
        4,
        byteorder="big"
    )

    sock.sendall(header + message_bytes)


def receive_exactly(sock, number_of_bytes):
    data = b""

    while len(data) < number_of_bytes:
        chunk = sock.recv(
            number_of_bytes - len(data)
        )

        if not chunk:
            return None

        data += chunk

    return data


def receive_message(sock):
    header = receive_exactly(sock, 4)

    if header is None:
        return None

    message_length = int.from_bytes(
        header,
        byteorder="big"
    )

    message_bytes = receive_exactly(
        sock,
        message_length
    )

    if message_bytes is None:
        return None

    return message_bytes.decode("utf-8")


def create_text_message(text):
    message = {
        "type": "TEXT",
        "text": text
    }

    return json.dumps(message)


def create_file_message(filename, filesize, sender_name):
    message = {
        "type": "FILE",
        "filename": filename,
        "filesize": filesize,
        "sender_name": sender_name
    }

    return json.dumps(message)


def send_file_chunks(sock, file_path):
    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            sock.sendall(chunk)


def receive_file_chunks(sock, file_path, filesize):
    remaining_bytes = filesize

    with open(file_path, "xb") as file:
        while remaining_bytes > 0:
            chunk = sock.recv(
                min(CHUNK_SIZE, remaining_bytes)
            )

            if not chunk:
                raise ConnectionError(
                    "Connection lost during file transfer."
                )

            file.write(chunk)

            remaining_bytes -= len(chunk)
