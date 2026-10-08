
# TCP-Based Peer-to-Peer (P2P) Network Application

## 1. Project Overview

This project is a Python-based Peer-to-Peer (P2P) Network Application developed using TCP sockets and Tkinter.

The application allows multiple peers to communicate directly over a network. Each peer can send and receive text messages and transfer different types of files.

A peer can act as both a server and a client, allowing two-way communication without a central messaging server.

## 2. Project Features

- TCP-based peer-to-peer communication
- Graphical User Interface (GUI) using Tkinter
- Start and Stop Peer functionality
- Connect to another peer using IP address and port
- Multiple peer connections
- Two-way text messaging
- File transfer between connected peers
- Support for JPG, PNG, PDF, ZIP, audio, and video files
- Chunk-based binary file transfer
- HELLO and HELLO_ACK handshake
- JSON-based message protocol
- Four-byte length-prefixed messages
- Background threads for network communication
- Connected peers list
- Peer disconnection notifications
- Error handling for invalid ports and failed connections
- Automatic saving of received files in the downloads folder
- Duplicate filename handling

## 3. Technologies Used

- Programming Language: Python
- GUI Framework: Tkinter
- Networking: TCP Sockets
- Message Format: JSON
- Concurrency: Python Threading
- File Handling: Python Standard Library

## 4. Project Structure

P2P_Network/
    main.py
    p2p_node.py
    protocol.py
    requirements.txt
    README.md
    downloads/

## 5. File Descriptions

### main.py

Creates the graphical user interface and manages user interactions, including starting and stopping peers, connecting to other peers, sending messages, and selecting files.

### p2p_node.py

Manages TCP server and client connections, connected peers, message exchange, file transfer, and peer disconnections.

### protocol.py

Implements the communication protocol, including HELLO, HELLO_ACK, TEXT, and FILE messages. It also handles JSON message framing and binary file transfer in chunks.

### requirements.txt

Documents the project's Python dependency requirements.

### downloads/

Stores files received from other peers. The folder is created automatically when needed.

## 6. Requirements

- Python 3
- Tkinter support
- A computer running Windows, Linux, or macOS
- Network connectivity between peers

No additional third-party Python packages are required.

## 7. How to Run the Application

1. Open the project folder in Visual Studio Code or a terminal.

2. Run the following command:

   python main.py

3. Enter a peer name and listening port.

4. Click "Start Peer".

5. Open another instance of the application.

6. Enter a different peer name and port, then click "Start Peer".

7. Enter the remote peer's IP address and listening port.

8. Click "Connect".

9. Select a connected peer from the list.

10. Send a text message using the message box and "Send" button.

11. To transfer a file, click "Send File" and select the file.

12. To stop a peer, click "Stop Peer".

## 8. Example: Connecting Three Peers

For testing on the same computer, use the following configuration:

| Peer | IP Address | Listening Port |
|------|------------|----------------|
| Alice | 127.0.0.1 | 5000 |
| Bob | 127.0.0.1 | 5001 |
| Charlie | 127.0.0.1 | 5002 |

Start all three peers.

Connect Bob to Alice using port 5000.

Connect Charlie to Alice using port 5000.

Connect Charlie to Bob using port 5001.

After successful connections, each peer can communicate with the other connected peers.

Note: 127.0.0.1 is the loopback address and is used when testing multiple peers on the same computer. For communication between different computers, use the reachable IP address of the destination computer.

## 9. Communication Protocol

The application uses TCP sockets.

A peer begins communication by sending a HELLO message. The receiving peer responds with HELLO_ACK.

Text messages are exchanged using the TEXT message type.

File transfers begin with a FILE metadata message containing the filename and file size. The file content is then transmitted as raw binary data in chunks.

JSON messages use a four-byte length prefix to identify the message size.

## 10. File Transfer

The application supports transferring different file types, including:

- Text files
- JPG and PNG images
- PDF documents
- ZIP archives
- Audio files
- Video files

File data is transferred in 64 KB chunks.

Received files are saved inside the downloads folder.

If a file with the same name already exists, the application creates a new filename to avoid overwriting the existing file.

## 11. Testing and Results

The application was manually tested using three peers: Alice, Bob, and Charlie.

The following tests were completed successfully:

- Starting and stopping peers
- Restarting a stopped peer
- Connecting two peers
- Connecting three peers
- Two-way text messaging
- Sending JPG and PDF files
- Transferring PNG, ZIP, audio, and video files
- Transferring files larger than 5 MB
- Handling invalid port input
- Handling failed connection attempts
- Handling attempts to send without selecting a peer
- Detecting peer disconnections
- Maintaining communication between other peers after one peer stops
- Reconnecting a peer after restarting
- Sending messages after reconnection

These tests were performed locally using the loopback address (127.0.0.1).

## 12. Limitations

- Peers must be manually connected using their IP addresses and ports.
- Stopped peers do not automatically reconnect after restarting.
- Transfers interrupted by a disconnection may leave incomplete files.
- Communication is not encrypted.
- The application was tested locally; operation across different computers or networks has not yet been verified.

## 13. Conclusion

This project demonstrates the implementation of a TCP-based peer-to-peer communication system using Python.

It provides practical experience with socket programming, multithreading, GUI development, message protocols, and binary file transfer.

The application successfully supports direct communication between multiple peers through a simple graphical interface.
