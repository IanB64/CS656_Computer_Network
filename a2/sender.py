import sys
import socket
import threading
import time
from packet import packet
import math

# Global Variables
# Fixed
WINDOW_SIZE = 10
TIMEOUT = 100  # in millisecond     # int(round(time.time() * 1000))
DATA_SIZE = packet.MAX_DATA_LENGTH  # 500 bytes
SEQ_MODULO = packet.SEQ_NUM_MODULO  # 32
lock = threading.Lock()  # lock for multi thread critical sections

# To-change
NUM_OF_PACKETS = 0  # total number of packets for the file
send_base = 0  # 0 - 31
nextseqnum = 0
ackedpackets = 0  # 0 - NUM_OF_PACKETS
multiplier = 0  # multiplier * SEQ_MODULO + nexseqnum = actual index of packets
send_timer = -1
max_seq_num = send_base + WINDOW_SIZE - 1

start_time = None  # the time just before sending the first packet
end_time = None  # the time immediately after receiving the EOT from the receiver

# log file tracking
seq_num_log = []
ack_log = []
time_log = []


def sendPacket(packets, emulatorAddr, emuReceiveData, client_udp_sock):
    global nextseqnum, lock, send_timer, start_time, end_time, time_log, multiplier

    # start a new thread for listening to the ACKs
    ack_thread = threading.Thread(target=receiveACK, args=(client_udp_sock,))
    ack_thread.start()

    # record the start time right before sending the very first packet.
    start_time = time.time()
    while send_base < NUM_OF_PACKETS:  # check if there are packets to be sent
        lock.acquire()

        if nextseqnum < send_base + WINDOW_SIZE:  # if window is not full, send segments
            client_udp_sock.sendto(packets[nextseqnum].get_udp_data(), (emulatorAddr, emuReceiveData))
            seq_num_log.append(packets[nextseqnum].seq_num)

            if send_base == nextseqnum:
                send_timer = int(round(time.time() * 1000))  # start the timer
            nextseqnum += 1

            if nextseqnum % SEQ_MODULO == 0:  # update multiplier every 32 packets
                multiplier += 1

        if int(round(time.time() * 1000)) - send_timer > TIMEOUT:  # if timeout occur, resend
            send_timer = -1  # reset the timer
            nextseqnum = send_base

        lock.release()

    # record the end time after sending all packets.
    end_time = time.time()
    time_log.append(int(round((end_time - start_time) * 1000)))


def resendPacket():
    lock.acquire()
    global nextseqnum, send_base
    nextseqnum = send_base
    lock.release()


def receiveACK(client_udp_sock):
    global send_base, send_timer, multiplier, max_seq_num

    print("im in receive ack")
    while True:
        msg, address = client_udp_sock.recvfrom(4096)
        ack_packet = packet.parse_udp_data(msg)
        ack_seq_num = ack_packet.seq_num
        ack_type = ack_packet.type
        ack_log.append(ack_packet.seq_num)

        if ack_packet.seq_num >= send_base:
            lock.acquire()
            if ack_seq_num + multiplier * SEQ_MODULO > max_seq_num:
                send_base = ack_packet.seq_num + (multiplier - 1) * SEQ_MODULO + 1
            else:
                send_base = ack_packet.seq_num + multiplier * SEQ_MODULO + 1

            max_seq_num = send_base + WINDOW_SIZE - 1
            send_timer = -1
            lock.release()

        if ack_type == 2:  # when receive an ack for EOT
            break


def fileToPacket(filename):
    packets = []
    file = open(filename, "r").read()

    global NUM_OF_PACKETS
    NUM_OF_PACKETS = math.ceil(len(file) / DATA_SIZE) + 1  # all data packets + 1 EOT packet

    for i in range(0, NUM_OF_PACKETS - 1):
        data = file[i * DATA_SIZE:min((i + 1) * DATA_SIZE, len(file))]
        packets.append(packet.create_packet(i, str(data)))

    packets.append(packet.create_eot(NUM_OF_PACKETS - 1))  # the last index of packets stores the EOT packet

    print("total number of packets is: ", len(packets), " = ", NUM_OF_PACKETS)
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
    for log in time_log:
        f.write(str(log) + "\n")
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


if __name__ == '__main__':
    main()
