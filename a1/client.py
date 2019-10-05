import sys
import socket


class Client:
    client_tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    c_port = 0  # Communication port

    def __init__(self, server_address, n_port, req_code):
        try:
            self.client_tcp_sock.connect((server_address, n_port))
        except:
            print("Negotiation port is unable to connect.")
            exit(1)
        self.c_port = self.negotiation(req_code)    # Get communication port from the server

    # Negotiate with the server. Using the req_code to validate the connection.
    # If the req_code doesn't match, then client should terminate.
    def negotiation(self, req_code):
        self.client_tcp_sock.send(req_code.encode())
        c_port = int(self.client_tcp_sock.recv(1024).decode())
        if c_port == 0:
            print("Invalid req_code.")
            self.client_tcp_sock.close()
            self.client_udp_sock.close()
            exit(1)
        else:
            return c_port

    # Retrieve and print all existing stored msg from the server through UDP.
    def receive_msg(self, server_address):
        self.client_udp_sock.sendto("GET".encode(), (server_address, self.c_port))
        while True:
            dialog, addr = self.client_udp_sock.recvfrom(2048)
            print(str(dialog.decode()))
            if dialog.decode() == "NO MSG.":
                print("")
                break

    # Send the new message to the server through UDP.
    def send_msg(self, server_address, msg):
        self.client_udp_sock.sendto(str(msg).encode(), (server_address, self.c_port))

    # Shut down the client after an input.
    def shutdown(self):
        k = input("Press any key to exit.")
        if type(k) is str:
            self.client_udp_sock.close()
            self.client_tcp_sock.close()
            exit(0)


def main():
    if len(sys.argv) != 5:          # Valid the number of input arguments.
        print("Improper number of arguments.")
        exit(1)
    else:
        server_address = sys.argv[1]
        n_port = sys.argv[2]
        req_code = sys.argv[3]
        msg = sys.argv[4]
        client = Client(str(server_address), int(n_port), req_code)
        client.receive_msg(str(server_address))
        client.send_msg(str(server_address), msg)
        client.shutdown()


if __name__ == '__main__':
    main()
