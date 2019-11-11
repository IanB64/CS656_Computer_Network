import sys
import socket
import threading
import time
from packet import packet
import math

# Global Variables
# Fixed
WINDOW_SIZE = 10
TIMEOUT = 0.010  # in second
DATA_SIZE = packet.MAX_DATA_LENGTH  # 500 bytes
SEQ_MODULO = packet.SEQ_NUM_MODULO  # 32
lock = threading.Lock()  # lock for multi thread critical sections

# To-change
send_base = 0  # 0 - 31
nextseqnum = 0
terminate = False
# log file tracking
seq_num_log = []
ack_log = []
time_log = []

NUM_OF_PACKETS = 0


def timeout():
    global nextseqnum, terminate, NUM_OF_PACKETS, timer

    lock.acquire()
    nextseqnum = send_base
    lock.release()

    if send_base == NUM_OF_PACKETS - 1:
        lock.acquire()
        terminate = True
        lock.release()
        return

    if not terminate:
        lock.acquire()
        timer = threading.Timer(TIMEOUT, timeout)
        timer.start()
        lock.release()


timer = threading.Timer(TIMEOUT, timeout)


def sendPacket(packets, emulatorAddr, emuReceiveData, client_udp_sock):
    global nextseqnum, timer

    ack_thread = threading.Thread(target=receiveACK,
                                  args=(client_udp_sock,))  # start listening to the ACKs in new thread
    ack_thread.start()

    start_time = time.time()
    timer.start()
    while not terminate:
        if nextseqnum < min(send_base + WINDOW_SIZE, len(packets)):  # if window is not full, send segments
            client_udp_sock.sendto(packets[nextseqnum].get_udp_data(), (emulatorAddr, emuReceiveData))
            seq_num_log.append(packets[nextseqnum].seq_num)

            lock.acquire()
            nextseqnum += 1
            lock.release()

    end_time = time.time()
    time_log.append(end_time - start_time)


def receiveACK(client_udp_sock):
    global send_base, terminate, timer

    while not terminate:
        msg, _ = client_udp_sock.recvfrom(4096)
        ack_packet = packet.parse_udp_data(msg)
        ack_seq_num = ack_packet.seq_num
        ack_type = ack_packet.type
        ack_log.append(ack_packet.seq_num)

        if ack_type == 2:  # when receive an ack for EOT
            lock.acquire()
            terminate = True
            lock.release()
            break

        distance = 0
        if send_base % SEQ_MODULO < ack_seq_num:
            distance = ack_seq_num - send_base % SEQ_MODULO
        elif send_base % SEQ_MODULO > ack_seq_num:
            distance = ack_seq_num + SEQ_MODULO - send_base % SEQ_MODULO
        if distance < WINDOW_SIZE:
            send_base += distance + 1

        if timer.isAlive():
            timer.cancel()

        lock.acquire()
        timer = threading.Timer(TIMEOUT, timeout)
        lock.release()
        timer.start()


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
