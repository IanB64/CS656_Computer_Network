# CS656 - Computer Network - Fall 2019
# Assignment 2
# Introduction to Socket Programming
#
# sender.py
# Implement the Go-Back-N protocol, which could be used to transfer a text file from one host to another
# across an unreliable network. The protocol should be able to handle network errors such as packet loss and
# duplicate packets.
# The sender program reads data from the specified file and send it using the Go-Back-N protocol
# to the receiver via the network emulator

import sys
import socket
import threading
import time
from packet import packet
import math

# Global Variables
# Fixed
WINDOW_SIZE = 10
TIMEOUT = 0.100  # in second
DATA_SIZE = packet.MAX_DATA_LENGTH  # 500 bytes
SEQ_MODULO = packet.SEQ_NUM_MODULO  # 32
lock = threading.Lock()  # lock for multi thread critical sections

# To-change
send_base = 0  # 0 - 31
nextseqnum = 0
terminate = False
timer_base = None

# log file tracking
seq_num_log = []
ack_log = []
time_log = []

NUM_OF_PACKETS = 0


def sendPacket(packets, emulatorAddr, emuReceiveData, client_udp_sock):
    global nextseqnum, timer_base

    # start listening to the ACKs in a new thread
    ack_thread = threading.Thread(target=receiveACK, args=(client_udp_sock,))
    ack_thread.start()

    # record the start time before sending the first packet
    time_log.append(time.time())

    # initiate the timer base time
    lock.acquire()
    timer_base = time.time()
    lock.release()

    while not terminate:
        if time.time() - timer_base < TIMEOUT:
            if nextseqnum < min(send_base + WINDOW_SIZE, len(packets)):  # if window is not full, send segments
                client_udp_sock.sendto(packets[nextseqnum].get_udp_data(), (emulatorAddr, emuReceiveData))
                seq_num_log.append(packets[nextseqnum].seq_num)

                lock.acquire()
                nextseqnum += 1
                lock.release()
        else:  # TIMEOUT occur
            lock.acquire()
            nextseqnum = send_base  # resend un-ACKed packets in the window
            timer_base = time.time()  # update timer base time
            lock.release()

    time_log.append(time.time())  # record the end time
    time_log.append(int(round((time_log[1] - time_log[0]) * 1000)))  # record the transmission time


def receiveACK(client_udp_sock):
    global send_base, terminate, timer_base

    while not terminate:
        msg, _ = client_udp_sock.recvfrom(4096)
        ack_packet = packet.parse_udp_data(msg)
        ack_seq_num = ack_packet.seq_num
        ack_type = ack_packet.type

        # if received an ack for EOT, exit
        if ack_type == 2:
            lock.acquire()
            terminate = True
            lock.release()
            break

        ack_log.append(ack_packet.seq_num)

        distance = 0
        if send_base % SEQ_MODULO < ack_seq_num:
            distance = ack_seq_num - send_base % SEQ_MODULO
        elif send_base % SEQ_MODULO > ack_seq_num:
            distance = ack_seq_num + SEQ_MODULO - send_base % SEQ_MODULO

        if distance < WINDOW_SIZE:  # update the base
            send_base += distance + 1
            lock.acquire()
            timer_base = time.time()  # update the timer base time
            lock.release()


def fileToPacket(filename):
    global NUM_OF_PACKETS
    packets = []
    file = open(filename, "rb").read().decode()

    NUM_OF_PACKETS = math.ceil(len(file) / DATA_SIZE) + 1  # all data packets + 1 EOT packet

    for i in range(0, NUM_OF_PACKETS - 1):
        data = file[i * DATA_SIZE:min((i + 1) * DATA_SIZE, len(file))]
        packets.append(packet.create_packet(i, str(data)))  # in bytes

    packets.append(packet.create_eot(NUM_OF_PACKETS - 1))  # last packet is the EOT packet
    return packets


def writeLogFile():
    # Writing log files

    # seqnum.log
    f = open('seqnum.log', 'w+')
    for log in seq_num_log:
        f.write(str(log) + "\n")
    f.close()

    # ack.log
    f = open('ack.log', 'w+')
    for log in ack_log:
        f.write(str(log) + "\n")
    f.close()

    # time.log
    f = open('time.log', 'w+')
    f.write(str(time_log[2]) + "\n")
    f.close()


def main():
    if len(sys.argv) != 5:
        print("Improper number of arguments")
        exit(1)

    emulatorAddr = sys.argv[1]
    emuReceiveData = int(sys.argv[2])
    senderReceiveACK = int(sys.argv[3])
    filename = sys.argv[4]

    packets = fileToPacket(filename)

    client_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_udp_sock.bind(('', senderReceiveACK))

    sendPacket(packets, emulatorAddr, emuReceiveData, client_udp_sock)

    writeLogFile()

    print("\ntime_log: ", time_log[2])


if __name__ == '__main__':
    main()
