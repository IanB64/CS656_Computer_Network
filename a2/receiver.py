import sys
import socket
from packet import packet

arrival_log = []
expected_seq_num = 0
SEQ_MODULO = packet.SEQ_NUM_MODULO  # 32
firstTime = True


def receive(filename, emulatorAddr, emuReceiveACK, client_udp_sock):
    try:
        file = open(filename, 'w+')
    except IOError:
        print('Unable to open', filename)
        return

    while True:
        msg, address = client_udp_sock.recvfrom(4096)
        data_packet = packet.parse_udp_data(msg)
        pac_seq_num = data_packet.seq_num
        pac_data = data_packet.data
        pac_type = data_packet.type
        arrival_log.append(pac_seq_num)

        global expected_seq_num, firstTime

        if pac_type == 2:
            client_udp_sock.sendto(packet.create_eot(pac_seq_num).get_udp_data(), (emulatorAddr, emuReceiveACK))
            break

        if firstTime and pac_seq_num != 0:
            continue
        else:
            firstTime = False
            if pac_seq_num == expected_seq_num:
                client_udp_sock.sendto(packet.create_ack(pac_seq_num).get_udp_data(), (emulatorAddr, emuReceiveACK))

                expected_seq_num = (expected_seq_num + 1) % SEQ_MODULO

                file.write(pac_data)
            else:
                client_udp_sock.sendto(packet.create_ack((expected_seq_num - 1 + SEQ_MODULO) % SEQ_MODULO)
                                       .get_udp_data(), (emulatorAddr, emuReceiveACK))

    file.close()


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
