
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import os
import queue

from p2p_node import (
    start_server,
    stop_server,
    connect_to_peer,
    send_text_to_peer,
    send_file_to_peer,
    get_connected_peers,
    set_message_callback,
    set_disconnect_callback
)


gui_events = queue.Queue()

peer_started = False


def start_peer():
    global peer_started

    name = name_entry.get().strip()
    port_text = port_entry.get().strip()

    if name == "" or port_text == "":
        messagebox.showerror(
            "Error",
            "Please enter Peer Name and Port."
        )
        return

    try:
        port = int(port_text)

        if not (1 <= port <= 65535):
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Error",
            "Enter a valid port number (1-65535)."
        )
        return

    peer_started = True

    server_thread = threading.Thread(
        target=run_server,
        args=(name, port),
        daemon=True
    )

    server_thread.start()

    status_label.config(
        text=f"Status: Starting {name} on port {port}"
    )

    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    name_entry.config(state=tk.DISABLED)
    port_entry.config(state=tk.DISABLED)


def stop_peer():
    global peer_started

    if not peer_started:
        return

    peer_started = False

    stop_server()

    status_label.config(
        text="Status: Stopped"
    )

    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

    name_entry.config(state=tk.NORMAL)
    port_entry.config(state=tk.NORMAL)

    peer_listbox.selection_clear(0, tk.END)

    chat_box.insert(
        tk.END,
        "Peer stopped.\n"
    )

    chat_box.see(tk.END)


def run_server(name, port):
    try:
        start_server(name, port)

    except OSError as error:
        gui_events.put(
            ("server_error", str(error))
        )


def connect_peer():
    if not peer_started:
        messagebox.showerror(
            "Error",
            "Please start your peer first."
        )
        return

    name = name_entry.get().strip()
    own_port_text = port_entry.get().strip()
    ip = ip_entry.get().strip()
    peer_port_text = peer_port_entry.get().strip()

    if (
        name == ""
        or own_port_text == ""
        or ip == ""
        or peer_port_text == ""
    ):
        messagebox.showerror(
            "Error",
            "Please fill in all fields."
        )
        return

    try:
        own_port = int(own_port_text)
        peer_port = int(peer_port_text)

        if not (1 <= own_port <= 65535):
            raise ValueError

        if not (1 <= peer_port <= 65535):
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Error",
            "Enter valid port numbers (1-65535)."
        )
        return

    status_label.config(
        text="Status: Connecting to peer..."
    )

    client_thread = threading.Thread(
        target=connect_and_receive,
        args=(name, own_port, ip, peer_port),
        daemon=True
    )

    client_thread.start()


def connect_and_receive(name, own_port, ip, peer_port):
    peer_name = connect_to_peer(
        name,
        own_port,
        ip,
        peer_port
    )

    if peer_name is None:
        gui_events.put(
            ("connection_failed",)
        )
    else:
        gui_events.put(
            ("connected", peer_name)
        )


def refresh_peer_list():
    peers = get_connected_peers()
    selected_peer = get_selected_peer()

    current_peers = list(
        peer_listbox.get(0, tk.END)
    )

    if current_peers != peers:
        peer_listbox.delete(0, tk.END)

        for peer in peers:
            peer_listbox.insert(tk.END, peer)

        if selected_peer in peers:
            index = peers.index(selected_peer)
            peer_listbox.selection_set(index)


def get_selected_peer():
    selected = peer_listbox.curselection()

    if not selected:
        return None

    return peer_listbox.get(selected[0])


def send_chat_message():
    if not peer_started:
        messagebox.showerror(
            "Error",
            "Please start your peer first."
        )
        return

    text = message_entry.get().strip()

    if text == "":
        return

    peer_name = get_selected_peer()

    if peer_name is None:
        messagebox.showerror(
            "Error",
            "Please select a connected peer first."
        )
        return

    sent = send_text_to_peer(text, peer_name)

    if sent:
        chat_box.insert(
            tk.END,
            f"Me to {peer_name}: {text}\n"
        )

        chat_box.see(tk.END)
        message_entry.delete(0, tk.END)

    else:
        messagebox.showerror(
            "Error",
            "Message could not be sent."
        )


def on_network_message(peer_name, message):
    gui_events.put(
        ("message", peer_name, message)
    )


def on_peer_disconnect(peer_name):
    gui_events.put(
        ("disconnected", peer_name)
    )


def show_received_message(peer_name, text):
    chat_box.insert(
        tk.END,
        f"{peer_name}: {text}\n"
    )

    chat_box.see(tk.END)


def choose_and_send_file():
    if not peer_started:
        messagebox.showerror(
            "Error",
            "Please start your peer first."
        )
        return

    peer_name = get_selected_peer()

    if peer_name is None:
        messagebox.showerror(
            "Error",
            "Please select a connected peer first."
        )
        return

    file_path = filedialog.askopenfilename()

    if file_path == "":
        return

    if not os.path.isfile(file_path):
        messagebox.showerror(
            "File Error",
            "Selected file does not exist."
        )
        return

    file_thread = threading.Thread(
        target=send_file_in_background,
        args=(file_path, peer_name),
        daemon=True
    )

    file_thread.start()

    chat_box.insert(
        tk.END,
        f"Sending file to {peer_name}...\n"
    )

    chat_box.see(tk.END)


def send_file_in_background(file_path, peer_name):
    sent = send_file_to_peer(
        file_path,
        peer_name
    )

    if sent:
        gui_events.put(
            ("file_sent", peer_name, os.path.basename(file_path))
        )
    else:
        gui_events.put(
            ("file_send_failed", peer_name)
        )


def process_gui_events():
    global peer_started

    while not gui_events.empty():
        event = gui_events.get()
        event_type = event[0]

        if event_type == "message":
            peer_name = event[1]
            message = event[2]

            if message.get("type") == "TEXT":
                show_received_message(
                    peer_name,
                    message.get("text", "")
                )

            elif message.get("type") == "FILE_RECEIVED":
                filename = message.get("filename", "")

                chat_box.insert(
                    tk.END,
                    f"{peer_name} sent file: {filename}\n"
                )

                chat_box.see(tk.END)

        elif event_type == "connected":
            peer_name = event[1]

            status_label.config(
                text=f"Status: Connected to {peer_name}"
            )

        elif event_type == "connection_failed":
            status_label.config(
                text="Status: Connection failed"
            )

            messagebox.showerror(
                "Connection Error",
                "Could not connect to the peer."
            )

        elif event_type == "disconnected":
            peer_name = event[1]

            chat_box.insert(
                tk.END,
                f"{peer_name} disconnected.\n"
            )

            chat_box.see(tk.END)

        elif event_type == "server_error":
            error = event[1]

            peer_started = False

            status_label.config(
                text="Status: Server failed"
            )

            start_button.config(state=tk.NORMAL)
            stop_button.config(state=tk.DISABLED)

            name_entry.config(state=tk.NORMAL)
            port_entry.config(state=tk.NORMAL)

            messagebox.showerror(
                "Server Error",
                error
            )

        elif event_type == "file_sent":
            peer_name = event[1]
            filename = event[2]

            chat_box.insert(
                tk.END,
                f"Me to {peer_name}: File sent - {filename}\n"
            )

            chat_box.see(tk.END)

        elif event_type == "file_send_failed":
            peer_name = event[1]

            messagebox.showerror(
                "File Error",
                f"Could not send file to {peer_name}."
            )

    refresh_peer_list()

    root.after(100, process_gui_events)


root = tk.Tk()

root.title("P2P Network Application")
root.geometry("500x850")
root.resizable(False, False)


title_label = tk.Label(
    root,
    text="P2P Network Application",
    font=("Arial", 18, "bold")
)

title_label.pack(pady=15)


peer_frame = tk.LabelFrame(
    root,
    text="My Peer",
    padx=15,
    pady=10
)

peer_frame.pack(
    fill="x",
    padx=30,
    pady=5
)

tk.Label(
    peer_frame,
    text="Peer Name:"
).grid(row=0, column=0, sticky="w", pady=5)

name_entry = tk.Entry(peer_frame, width=30)
name_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(
    peer_frame,
    text="My Port:"
).grid(row=1, column=0, sticky="w", pady=5)

port_entry = tk.Entry(peer_frame, width=30)
port_entry.grid(row=1, column=1, padx=10, pady=5)


start_button = tk.Button(
    peer_frame,
    text="Start Peer",
    width=15,
    command=start_peer
)

start_button.grid(
    row=2,
    column=0,
    padx=5,
    pady=10
)


stop_button = tk.Button(
    peer_frame,
    text="Stop Peer",
    width=15,
    command=stop_peer,
    state=tk.DISABLED
)

stop_button.grid(
    row=2,
    column=1,
    padx=5,
    pady=10
)


connect_frame = tk.LabelFrame(
    root,
    text="Connect to Another Peer",
    padx=15,
    pady=10
)

connect_frame.pack(
    fill="x",
    padx=30,
    pady=5
)

tk.Label(
    connect_frame,
    text="Peer IP:"
).grid(row=0, column=0, sticky="w", pady=5)

ip_entry = tk.Entry(connect_frame, width=30)
ip_entry.grid(row=0, column=1, padx=10, pady=5)
ip_entry.insert(0, "127.0.0.1")

tk.Label(
    connect_frame,
    text="Peer Port:"
).grid(row=1, column=0, sticky="w", pady=5)

peer_port_entry = tk.Entry(connect_frame, width=30)
peer_port_entry.grid(row=1, column=1, padx=10, pady=5)


connect_button = tk.Button(
    connect_frame,
    text="Connect",
    width=15,
    command=connect_peer
)

connect_button.grid(
    row=2,
    column=0,
    columnspan=2,
    pady=10
)


peer_list_frame = tk.LabelFrame(
    root,
    text="Connected Peers",
    padx=15,
    pady=10
)

peer_list_frame.pack(
    fill="x",
    padx=30,
    pady=5
)

peer_listbox = tk.Listbox(
    peer_list_frame,
    width=48,
    height=4,
    exportselection=False
)

peer_listbox.pack(pady=5)

tk.Label(
    peer_list_frame,
    text="Select a peer before sending a message or file."
).pack()


chat_frame = tk.LabelFrame(
    root,
    text="Chat",
    padx=15,
    pady=10
)

chat_frame.pack(
    fill="x",
    padx=30,
    pady=5
)


chat_box = tk.Text(
    chat_frame,
    width=48,
    height=6
)

chat_box.pack(pady=5)


message_frame = tk.Frame(chat_frame)
message_frame.pack(pady=5)


message_entry = tk.Entry(
    message_frame,
    width=35
)

message_entry.pack(
    side="left",
    padx=5
)


send_button = tk.Button(
    message_frame,
    text="Send",
    width=10,
    command=send_chat_message
)

send_button.pack(
    side="left",
    padx=5
)


file_button = tk.Button(
    chat_frame,
    text="Send File",
    width=15,
    command=choose_and_send_file
)

file_button.pack(pady=5)


status_label = tk.Label(
    root,
    text="Status: Not started",
    font=("Arial", 10)
)

status_label.pack(pady=10)


set_message_callback(on_network_message)
set_disconnect_callback(on_peer_disconnect)

root.after(100, process_gui_events)

root.mainloop()
