import time

from plotters.AmpPhaPlotter import Plotter  # Amplitude and Phase plotter
import decoders.interleavedModificado as decoder
import socket


remove_null_subcarriers = True
remove_pilot_subcarriers = True
apply_hampel = True
apply_smoothing = False
_amplitude = True
_fase = False

tamanho_janela_exibicao = 200
quantidade_pacotes_atualiza = 10

bandwidth = int(input("Qual a largura de banda a ser usada? "))

TCP_IP = "192.168.40.129"
TCP_PORT = 5501
BUFFER_SIZE = 512*4  # deve armazenar os bytes de cada pacote (n_sub * 4) + header nexmon (18 bytes)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((TCP_IP, TCP_PORT))
    print("Waiting for connections...")
    s.listen(1)
    conn, addr = s.accept()
    print('Connected by', addr)
    print("\n\n")
    time.sleep(1)

    plotter = Plotter(bandwidth, apply_hampel=apply_hampel, apply_smoothing=apply_smoothing,
                      plot_phase=_fase, plot_amp=_amplitude, tam_janela=tamanho_janela_exibicao,
                      packets_refresh=quantidade_pacotes_atualiza)

    n_frame = 0
    while True:
        # recebendo os frames
        frame = conn.recv(BUFFER_SIZE)
        if frame[:4] != b'\x11\x11\x11\x11':  # checa se o frame veio adequadamente
            continue

        # processando as informacoes do pacote CSI
        frame_info = decoder.read_frame(frame, bandwidth)
        if frame_info == -1:
            continue

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
