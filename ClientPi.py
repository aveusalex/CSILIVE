import socket

# ouvindo o csi na porta 5500
UDP_IP = "255.255.255.255"  # SEGUINDO O GITHUB DO NEXMON (SOURCE 10.10.10.10)
UDP_PORT = 5500

# preparando server do csi
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:  # UDP

    sock.bind((UDP_IP, UDP_PORT))

    # conectando no server do PC
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_pc:
        server_pc.connect(('192.168.0.179', 5501))

        while True:
            try:
                data, addr = sock.recvfrom(512 * 4)  # buffer size is 2048 + 18 bytes
                server_pc.sendall(data)

            except ConnectionError as e:
                decision = input("Servidor caiu. Reconectar? ([y]/n) ")
                if decision in ["n", "N"]:
                    exit(0)
                else:
                    continue
