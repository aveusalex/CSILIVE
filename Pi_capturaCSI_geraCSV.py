import numpy as np
import pandas as pd
import time
import os
import decoders.interleavedModificado as decoder
import socket


remove_null_subcarriers = False
remove_pilot_subcarriers = False

qtd_pacotes = int(input("Quantos pacotes deseja armazenar? "))
nome_salvamento = input("Qual o nome de salvamento que deseja? ")
bandwidth = int(input("Qual a largura de banda a ser usada? "))
nsub = bandwidth * 3.2
memoria_temporaria_frames_ant1 = np.zeros((2, int(nsub), qtd_pacotes))

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

    n_frame = 0
    start = time.time()
    while n_frame < qtd_pacotes:
        print(f"Lendo Frame {n_frame}")

        # recebendo os frames
        frame = conn.recv(BUFFER_SIZE)
        if frame[:4] != b'\x11\x11\x11\x11':  # checa se o frame veio adequadamente
            continue

        # processando as informacoes do pacote CSI
        frame_info = decoder.read_frame(frame, bandwidth)
        if frame_info == -1:
            continue

        csi1 = frame_info.get_csi(
            0,
            remove_null_subcarriers,
            remove_pilot_subcarriers
        )

        amplitudes1 = np.abs(csi1)
        fases1 = np.angle(csi1)
        memoria_temporaria_frames_ant1[0, :, n_frame] = amplitudes1
        memoria_temporaria_frames_ant1[1, :, n_frame] = fases1

        n_frame += 1
        del frame_info


tempo_total = time.time() - start
print(f"Durou {tempo_total:.2f} segundos para capturar {n_frame} pacotes.")
frequencia = f"{(n_frame / tempo_total):.2f}".split(".")
frequencia = "_".join(frequencia)

dados_amp_ant1 = pd.DataFrame(memoria_temporaria_frames_ant1[0])
dados_phase_ant1 = pd.DataFrame(memoria_temporaria_frames_ant1[1])

# salvando
current_dir = os.getcwd()
qts_respiradas = input("Quantas respiradas deu? ")

sair = False
while not sair:
    try:
        save = current_dir + '/' + nome_salvamento
        os.mkdir(save)
        sair = True
    except OSError as error:
        nome_salvamento = input("Esse save ja existe! Ponha outro nome: ")

dados_amp_ant1.to_csv(f"{save}/{nome_salvamento}-amp-ant1-{frequencia}Hz-{qts_respiradas}R.csv", index=False)
dados_phase_ant1.to_csv(f"{save}/{nome_salvamento}-phase-ant1-{frequencia}Hz-{qts_respiradas}R.csv", index=False)
