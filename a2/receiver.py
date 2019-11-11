import sys
import socket
from packet import packet

arrival_log = []
expected_pkt_num = 0
SEQ_MODULO = packet.SEQ_NUM_MODULO  # 32


def receive(filename, emulatorAddr, emuReceiveACK, client_udp_sock):
    global expected_pkt_num
    save_data = bytearray()

    try:
        file = open(filename, 'wb')
    except IOError:
        print('Unable to open', filename)
        return

    while True:
        msg, _ = client_udp_sock.recvfrom(4096)
        data_packet = packet.parse_udp_data(msg)
        type = data_packet.type
        seq_num = data_packet.seq_num
        data = data_packet.data
        arrival_log.append(seq_num)

        print("P", end='')
        print(expected_pkt_num, end=' ')

        if type == 2:
            client_udp_sock.sendto(packet.create_eot(seq_num).get_udp_data(), (emulatorAddr, emuReceiveACK))
            # print("A",end= '')
            # print(seq_num,end= ' ')
            break

        if seq_num == expected_pkt_num % SEQ_MODULO:
            expected_pkt_num += 1
            save_data.extend(data.encode())

        if expected_pkt_num != 0:
            ack_num = (expected_pkt_num - 1) % SEQ_MODULO
            client_udp_sock.sendto(packet.create_ack(ack_num).get_udp_data(), (emulatorAddr, emuReceiveACK))
            # print("A",end= '')
            # print(ack_num,end= ' ')


    file.write(save_data)
    file.close()
    print("\narrival_log",end=' ')
    print(arrival_log)


def writeLogFile():
    # Writing log file
    # arrival.log
    f = open('arrival.log', 'w+')
    for log in arrival_log:
        f.write(str(log) + "\n")
    f.close()


def main():
    if len(sys.argv) != 5:
        print("Improper number of arguments")
        exit(1)

    emulatorAddr = sys.argv[1]
    emuReceiveACK = int(sys.argv[2])
    rcvrReceiveData = int(sys.argv[3])
    filename = sys.argv[4]

    client_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_udp_sock.bind(('', rcvrReceiveData))

    receive(filename, emulatorAddr, emuReceiveACK, client_udp_sock)
    writeLogFile()


if __name__ == '__main__':
    main()