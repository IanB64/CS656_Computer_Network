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


def timeout():
    global nextseqnum, send_base

    lock.acquire()
    nextseqnum = send_base
    lock.release()
    timer.cancel()


timer = threading.Timer(0.1, timeout)


def sendPacket(packets, emulatorAddr, emuReceiveData, client_udp_sock):
    global nextseqnum, lock, send_timer, start_time, end_time, time_log, multiplier

    print("im in send")

    ack_thread = threading.Thread(target=receiveACK,
                                  args=(client_udp_sock,))  # start listening to the ACKs in new thread
    ack_thread.start()

    print("Im here")

    start_time = time.time()
    timer = threading.Timer(0.1, timeout)
    while send_base < NUM_OF_PACKETS:  # check if there are packets to be sent
        if nextseqnum < min(send_base + WINDOW_SIZE, len(packets)):  # if window is not full, send segments
            client_udp_sock.sendto(packets[nextseqnum].get_udp_data(), (emulatorAddr, emuReceiveData))
            if not timer.isAlive():
                timer.start()
                timer = threading.Timer(0.1, timeout)

            lock.acquire()
            seq_num_log.append(packets[nextseqnum].seq_num)
            print("S", end='')
            print(nextseqnum, end=' ')

            if send_base == nextseqnum:
                send_timer = time.time()  # start the timer

            nextseqnum += 1

            lock.release()

    end_time = time.time()
    time_log.append(int(round((end_time - start_time) * 1000)))


def receiveACK(client_udp_sock):
    global send_base, send_timer, multiplier, max_seq_num

    print("im in receive ack")
    while True:
        msg, _ = client_udp_sock.recvfrom(4096)
        ack_packet = packet.parse_udp_data(msg)
        ack_seq_num = ack_packet.seq_num
        ack_type = ack_packet.type
        ack_log.append(ack_packet.seq_num)

        lock.acquire()

        if send_base % 32 < ack_seq_num:
            send_base += ack_seq_num - send_base % 32
        elif send_base % 32 > ack_seq_num:
            send_base += ack_seq_num + 32 - send_base % 32

        if ack_type == 2:  # when receive an ack for EOT
            send_base += 1
            lock.release()
            break

        lock.release()


def fileToPacket(filename):
    packets = []
    file = open(filename, "rb").read().decode()

    global NUM_OF_PACKETS
    NUM_OF_PACKETS = math.ceil(len(file) / DATA_SIZE) + 1  # all data packets + 1 EOT packet

    for i in range(0, NUM_OF_PACKETS - 1):
        data = file[i * DATA_SIZE:min((i + 1) * DATA_SIZE, len(file))]
        packets.append(packet.create_packet(i, str(data)))  # in bytes

    packets.append(packet.create_eot(NUM_OF_PACKETS - 1))  # last packet is the EOT packet

    print("total number of packets is: ", len(packets))
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

    print("\nseq_num_log", end=' ')
    print(seq_num_log)

    print("ack_log    ", end=' ')
    print(ack_log)


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