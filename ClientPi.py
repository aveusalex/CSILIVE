import socket
import threading

janela = 1000
buffer = [b'\x00'] * janela
start = False
stop = False


def listen_5500(janela_k):  # janela é o tamanho k de frames armazenados em um array/buffer
    # ouvindo o csi na porta 5500
    global start, buffer
    UDP_IP = "255.255.255.255"  # SEGUINDO O GITHUB DO NEXMON (SOURCE 10.10.10.10)
    UDP_PORT = 5500

    # preparando server do csi
    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_DGRAM)  # UDP

    sock.bind((UDP_IP, UDP_PORT))

    counter = 0
    while True and not stop:
        if counter >= janela_k:
            counter = 0
        if counter == 5:
            start = True
        # recebendo os frames (nexmon metadata + CSI data) (18 bytes + numero subcarriers * 4)
        data, addr = sock.recvfrom(512 * 4 + 18)  # buffer size is 2048 + 18 bytes
        buffer[counter] = data
        counter += 1


# iniciando o thread do servidor Nexmon
t = threading.Thread(target=listen_5500, args=[janela])
try:
    t.start()
    print("Servidor Nexmon iniciado. Escutando pacotes na porta 5500.")
except ConnectionError:
    print("Não foi possível conectar na porta 5500. Tem certeza que o modo monitor está ativo?")
    stop = True
    exit(-1)

# conectando no server do PC
try:
    server_pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_pc.connect(('192.168.0.3', 5501))
except ConnectionError:
    print("Não foi possível conectar ao computador. Verifique se o CSIExplorerSERVER está rodando.")
    exit(-1)

# contador auxiliar que serve como ponteiro para o buffer
counter = 0
while True and start and not stop:
    if counter >= janela:
        counter = 0
    data = buffer[counter]

    # enviando os dados para o computador de destino
    try:
        server_pc.send(data)
        counter += 1

    except ConnectionError:
        decision = input("Servidor caiu. Reconectar? ([y]/n) ")
        if decision in ["n", "N"]:
            stop = True
            exit(0)
        else:
            continue
