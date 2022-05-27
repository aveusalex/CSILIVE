import time

from plotters.AmpPhaPlotter import Plotter  # Amplitude and Phase plotter
import decoders.interleavedModificado as decoder
import socket


remove_null_subcarriers = True
remove_pilot_subcarriers = True
bandwidth = int(input("Qual a largura de banda a ser usada? "))

TCP_IP = "10.0.0.164"
TCP_PORT = 5501
BUFFER_SIZE = 512*4  # 34 surge do NEXMON metadado + packet header

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((TCP_IP, TCP_PORT))
    print("Waiting for connections...")
    s.listen(1)
    conn, addr = s.accept()
    print('Connected by', addr)
    print("\n\n")
    time.sleep(1)

    plotter = Plotter(bandwidth)

    n_frame = 0
    while True:
        # recebendo os frames
        frame = conn.recv(BUFFER_SIZE)

        # processando as informacoes do pacote CSI
        frame_info = decoder.read_frame(frame, bandwidth)
        frame_info.print(0, n_frame=n_frame)

        # Lendo o CSI de fato
        csi = frame_info.get_csi(
            0,
            remove_null_subcarriers,
            remove_pilot_subcarriers
        )

        plotter.update(csi, n_frame)
        n_frame += 1
        del frame_info
