
import socket
import os
import json
import threading

from protocol import (
    create_hello_message,
    create_hello_ack_message,
    create_text_message,
    create_file_message,
    send_message,
    receive_message,
    send_file_chunks,
    receive_file_chunks
)


connected_peers = {}
peers_lock = threading.Lock()

send_locks = {}

message_callback = None
disconnect_callback = None

my_peer_name = ""

server_socket = None
server_running = False
server_lock = threading.Lock()


def set_message_callback(callback):
    global message_callback
    message_callback = callback


def set_disconnect_callback(callback):
    global disconnect_callback
    disconnect_callback = callback


def add_peer(name, connection):
    with peers_lock:
        connected_peers[name] = connection
        send_locks[name] = threading.Lock()


def get_connected_peers():
    with peers_lock:
        return list(connected_peers.keys())


def get_peer_connection(name):
    with peers_lock:
        return connected_peers.get(name)


def remove_peer(name, connection):
    with peers_lock:
        if connected_peers.get(name) is connection:
            del connected_peers[name]
            send_locks.pop(name, None)
            return True

    return False


def notify_message(peer_name, message):
    if message_callback is not None:
        message_callback(peer_name, message)


def save_incoming_file(peer_name, connection, message):
    filename = message.get("filename", "")
    filesize = message.get("filesize", -1)

    if (
        not isinstance(filesize, int)
        or isinstance(filesize, bool)
        or filesize < 0
    ):
        raise ValueError("Invalid file size.")

    if not isinstance(filename, str):
        raise ValueError("Invalid filename.")

    filename = os.path.basename(
        filename.replace("\\", "/")
    )

    if filename in ("", ".", ".."):
        raise ValueError("Invalid filename.")

    os.makedirs("downloads", exist_ok=True)

    name, extension = os.path.splitext(filename)

    file_path = os.path.join("downloads", filename)

    number = 1

    while os.path.exists(file_path):
        new_filename = f"{name}_{number}{extension}"
        file_path = os.path.join(
            "downloads",
            new_filename
        )
        number += 1

    receive_file_chunks(
        connection,
        file_path,
        filesize
    )

    notify_message(
        peer_name,
        {
            "type": "FILE_RECEIVED",
            "filename": os.path.basename(file_path)
        }
    )


def receive_from_peer(peer_name, connection):
    try:
        while True:
            data = receive_message(connection)

            if data is None:
                break

            message = json.loads(data)

            if message.get("type") == "FILE":
                save_incoming_file(
                    peer_name,
                    connection,
                    message
                )

            else:
                notify_message(peer_name, message)

    except (OSError, ValueError, UnicodeError) as error:
        print("Receive error:", error)

    finally:
        was_removed = remove_peer(
            peer_name,
            connection
        )

        connection.close()

        if was_removed and disconnect_callback is not None:
            disconnect_callback(peer_name)


def handle_incoming_peer(connection, address, my_name, my_port):
    try:
        received_data = receive_message(connection)

        if received_data is None:
            connection.close()
            return

        message = json.loads(received_data)

        if message.get("type") != "HELLO":
            connection.close()
            return

        peer_name = message.get("name", "")

        if not isinstance(peer_name, str) or peer_name == "":
            connection.close()
            return

        with server_lock:
            if not server_running:
                connection.close()
                return

        ack_message = create_hello_ack_message(
            my_name,
            my_port
        )

        send_message(connection, ack_message)

        add_peer(peer_name, connection)

        print("Connected with:", peer_name, address)

        receive_from_peer(peer_name, connection)

    except (OSError, ValueError, KeyError) as error:
        print("Connection error:", error)
        connection.close()


def start_server(name, port):
    global my_peer_name
    global server_socket
    global server_running

    new_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:
        new_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        new_socket.bind(("0.0.0.0", port))
        new_socket.listen()
        new_socket.settimeout(0.5)

        with server_lock:
            if server_running:
                raise OSError("Server is already running.")

            server_socket = new_socket
            server_running = True
            my_peer_name = name

        print(name, "is listening on port", port)

        while True:
            with server_lock:
                if not server_running or server_socket is not new_socket:
                    break

            try:
                connection, address = new_socket.accept()

            except socket.timeout:
                continue

            except OSError:
                break

            with server_lock:
                still_running = (
                    server_running
                    and server_socket is new_socket
                )

            if not still_running:
                connection.close()
                break

            peer_thread = threading.Thread(
                target=handle_incoming_peer,
                args=(connection, address, name, port),
                daemon=True
            )

            peer_thread.start()

    finally:
        with server_lock:
            if server_socket is new_socket:
                server_socket = None
                server_running = False

        new_socket.close()

        print("Server stopped.")


def stop_server():
    global server_socket
    global server_running

    with server_lock:
        server_running = False
        old_socket = server_socket
        server_socket = None

    if old_socket is not None:
        old_socket.close()

    with peers_lock:
        connections = list(connected_peers.items())

    for peer_name, connection in connections:
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        connection.close()

        was_removed = remove_peer(
            peer_name,
            connection
        )

        if was_removed and disconnect_callback is not None:
            disconnect_callback(peer_name)

    print("Peer stopped.")


def connect_to_peer(name, own_port, ip, port):
    global my_peer_name
    my_peer_name = name

    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:
        client_socket.connect((ip, port))

        hello_message = create_hello_message(
            name,
            own_port
        )

        send_message(client_socket, hello_message)

        ack_data = receive_message(client_socket)

        if ack_data is None:
            client_socket.close()
            return None

        ack = json.loads(ack_data)

        if ack.get("type") != "HELLO_ACK":
            client_socket.close()
            return None

        peer_name = ack.get("name", "")

        if peer_name == "":
            client_socket.close()
            return None

        add_peer(peer_name, client_socket)

        print("Connected to peer:", peer_name)

        receive_thread = threading.Thread(
            target=receive_from_peer,
            args=(peer_name, client_socket),
            daemon=True
        )

        receive_thread.start()

        return peer_name

    except (OSError, ValueError, KeyError) as error:
        print("Connection failed:", error)
        client_socket.close()
        return None


def send_text_to_peer(text, peer_name):
    connection = get_peer_connection(peer_name)

    if connection is None:
        return False

    with peers_lock:
        send_lock = send_locks.get(peer_name)

    if send_lock is None:
        return False

    try:
        with send_lock:
            text_message = create_text_message(text)
            send_message(connection, text_message)

        return True

    except OSError:
        remove_peer(peer_name, connection)
        connection.close()
        return False


def send_file_to_peer(file_path, peer_name):
    connection = get_peer_connection(peer_name)

    if connection is None:
        return False

    with peers_lock:
        send_lock = send_locks.get(peer_name)

    if send_lock is None:
        return False

    try:
        filesize = os.path.getsize(file_path)

        if filesize < 0:
            return False

        filename = os.path.basename(file_path)

        file_message = create_file_message(
            filename,
            filesize,
            my_peer_name
        )

        with send_lock:
            send_message(connection, file_message)

            send_file_chunks(
                connection,
                file_path
            )

        return True

    except OSError as error:
        print("File sending error:", error)
        remove_peer(peer_name, connection)
        connection.close()
        return False
