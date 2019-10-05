# CS656 - Computer Network - Fall 2019
# Assignment 1
# Introduction to Socket Programming
#
# server.py
# This message server handles client connections, sending stored messages to the client
# and stores new input messages from the client.

import sys
import socket
import threading


class Server:
    server_tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    msg = []  # Message buffer
    n_port = 0  # Declare the server TCP port
    req_code = 0  # Used to validate client's connection attempt
    terminate = False  # Whenever is True, server exit/shutdown

    # Initiate the server. Bind the tcp and udp socket and assign the n_port and req_code.
    def __init__(self, req_code):
        self.server_tcp_sock.bind(('', 0))  # Randomly bind to an available TCP port
        self.server_tcp_sock.listen(1)

        self.server_udp_sock.bind(('', 0))  # Randomly bind to an available UDP port

        self.n_port = self.server_tcp_sock.getsockname()[1]  # Assign the TCP port number
        self.req_code = req_code  # Assign the actual req_code
        print("SERVER_PORT=" + str(self.n_port))

    # Negotiate with the client. If succeed, create a thread to perform the UDP message transaction.
    def run(self):
        while True:
            client, address = self.server_tcp_sock.accept()
            req_code = client.recv(1024).decode()
            if int(req_code) != self.req_code:  # Negotiation with client failed
                client.send(b"0")
            else:  # Negotiation with client succeed
                client.send(str(self.server_udp_sock.getsockname()[1]).encode())
                client_thread = threading.Thread(target=self.message_handler)  # Create new thread
                client_thread.daemon = True # Reference: https://youtu.be/D0SLpD7JvZI
                client_thread.start()
            client.close()

    # Send the message from the buffer first then store the new message
    def message_handler(self):
        self.retrieve_message()
        self.store_message()

    # Send all message in the msg buffer to the client through UDP. Followed with "NO MSG.".
    def retrieve_message(self):
        msg, client_address = self.server_udp_sock.recvfrom(2048)
        if msg.decode() == "GET":
            for item in self.msg:
                convert_msg = "[" + str(item[0]) + "]: " + str(item[1])
                self.server_udp_sock.sendto(convert_msg.encode(), client_address)
            self.server_udp_sock.sendto("NO MSG.".encode(), client_address)

    # Store the new message from the client through UDP in format [CLIENTPORT, <MSG>] to the msg buffer
    # If the new message is "TERMINATE", the server should shut down.
    def store_message(self):
        msg, client_address = self.server_udp_sock.recvfrom(2048)
        if msg.decode() == "TERMINATE":
            self.terminate = True
        else:
            self.msg.append([client_address[1], msg.decode()])

    # Check if the server is shut down by any client.
    # If true, then clear all msg buffer and close all sockets.
    def shutdown(self):
        while True:
            if self.terminate:
                self.server_tcp_sock.close()
                self.server_udp_sock.close()
                exit(0)


# Performs input check from the command line.
def input_check(args):
    if len(args) != 2:
        print("Improper number of arguments")
        exit(1)
    try:
        c = int(args[1])
        return c
    except:
        print("Improper type of arguments")
        exit(1)


def main():
    code = input_check(sys.argv)
    server = Server(code)

    terminate_thread = threading.Thread(target=server.run)  # Create a sub-thread to actually run the server
    terminate_thread.daemon = True
    terminate_thread.start()

    server.shutdown()  # Main thread keeps checking if TERMINATE is sent by any of the sub-threads


if __name__ == '__main__':
    main()
