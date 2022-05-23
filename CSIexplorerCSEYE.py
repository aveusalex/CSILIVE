from plotters.AmpPhaPlotter import Plotter  # Amplitude and Phase plotter
import decoders.interleavedModificado as decoder
import socket


# TCP_IP = input("Qual o IP do raspberry? ")
TCP_IP = "192.168.0.4"
TCP_PORT = 5501
BUFFER_SIZE = 512*4 + 34  # 34 surge do NEXMON metadado + packet header

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
# s.send(MESSAGE)

remove_null_subcarriers = False
remove_pilot_subcarriers = False
bandwidth = 20

plotter = Plotter(bandwidth)

n_frame = 0
while True:
    # recebendo os frames
    frame = s.recv(BUFFER_SIZE)
    if n_frame == 0:
        print(frame[:16])
        print(frame[16:34])
        print(len(frame[34:34 + int(bandwidth * 3.2) * 4]))
        print("\n")
        n_frame += 1
        continue
    else:
        print(frame)
        #print(frame[50:68])
        #print(len(frame[68:68 + int(bandwidth * 3.2) * 4]))
        print("\n")
        continue
    # processando as informacoes do pacote CSI
    frame_info = decoder.read_frame(frame, bandwidth)
    frame_info.print(0, n_frame=n_frame)

    # Lendo o CSI de fato
    csi = frame_info.get_csi(
        0,
        remove_null_subcarriers,
        remove_pilot_subcarriers
    )

    plotter.update(csi)
    n_frame += 1
    del frame_info
