import numpy as np
import matplotlib.pyplot as plt

'''
Amplitude and Phase plotter
---------------------------

Plot Amplitude and Phase of CSI frame_info
and update the plots in the same window.

Initiate Plotter with bandwidth, and
call update with CSI value.
'''

__all__ = [
    'Plotter'
]


class Plotter:
    def __init__(self, bandwidth):
        self.bandwidth = bandwidth
        self.janelamento = 30
        self.janela_cheia = False  # nao mexer
        self.atualizacao = 10

        self.nsub = int(bandwidth * 3.2)

        self.fig, axs = plt.subplots(2)

        self.ax_amp = axs[0]
        self.ax_pha = axs[1]

        self.fig.suptitle('Nexmon CSI Real Time Explorer')

        # essa variavel de classe armazena os frames e seus valores de cada subportadora
        # a estrutura é um pouco confusa, mas a 1eira dimensão (com 2 pontos apenas) armazena amplitude e fase (0 e 1)
        # a segunda dimensao armazena os valores para cada subportadora
        # a terceira dimensao armazena os frames, serve como buffer.
        self.memoria_temporaria_frames = np.zeros((2, self.nsub, self.janelamento))

        plt.ion()
        plt.show() 

    def cascata(self, csi, sequencia):
        amplitudes = np.abs(csi)
        fases = np.angle(csi, deg=True)

        if self.janela_cheia:
            a_entrar_amp = amplitudes
            a_entrar_phase = fases
            for i in range(self.janelamento-1, -1, -1):
                copiar_amp = np.copy(self.memoria_temporaria_frames[0, :, i][:])
                copiar_phase = np.copy(self.memoria_temporaria_frames[1, :, i])
                self.memoria_temporaria_frames[0, :, i] = a_entrar_amp
                self.memoria_temporaria_frames[1, :, i] = a_entrar_phase
                a_entrar_amp = copiar_amp
                a_entrar_phase = copiar_phase

        else:
            posicao = sequencia % self.janelamento  # verificando qual posicao no buffer o csi vai entrar

            self.memoria_temporaria_frames[0, :, posicao] = amplitudes  # forma de obter as amplitudes
            self.memoria_temporaria_frames[1, :, posicao] = fases  # forma de obter as fases

    def update(self, csi, sequencia):
        if sequencia % self.atualizacao == 0:
            self.ax_amp.clear()
            self.ax_pha.clear()

            # These are also cleared with clear()
            self.ax_amp.set_ylabel('Amplitude')
            self.ax_pha.set_ylabel('Phase')
            self.ax_pha.set_xlabel('Sequencia Subportadora')

        self.cascata(csi, sequencia)

        if sequencia % self.janelamento == 0 and sequencia != 0:
            self.janela_cheia = True

        if sequencia % self.atualizacao == 0 and sequencia != 0:
            # tenho que plotar todos os valores armazenados de cada subcarrier por vez
            try:
                for subportadora in range(self.nsub):
                    amplitudes = self.memoria_temporaria_frames[0, subportadora, :]
                    fases = self.memoria_temporaria_frames[1, subportadora, :]

                    self.ax_amp.plot(range(self.janelamento), amplitudes)
                    self.ax_pha.plot(range(self.janelamento), fases)

            except ValueError as err:
                print(
                    f'A ValueError occurred. Is the bandwidth {self.bandwidth} MHz correct?\nError: ', err
                )
                exit(-1)
            plt.draw()
            plt.pause(0.001)
    
    def __del__(self):
        pass
