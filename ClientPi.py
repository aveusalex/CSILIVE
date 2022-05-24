import socket

# ouvindo o csi na porta 5500
UDP_IP = "255.255.255.255"  # SEGUINDO O GITHUB DO NEXMON (SOURCE 10.10.10.10)
UDP_PORT = 5500

# preparando server do csi
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

sock.bind((UDP_IP, UDP_PORT))

# conectando no server do PC
server_pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_pc.connect(('192.168.0.3', 5501))

while True:
    try:
        data, addr = sock.recvfrom(512 * 4 + 18)  # buffer size is 2048 + 18 bytes
        server_pc.send(data)

    except ConnectionError as e:
        decision = input("Servidor caiu. Reconectar? ([y]/n) ")
        if decision in ["n", "N"]:
            exit(0)
        else:
            continue
