import numpy as np
import matplotlib.pyplot as plt
from decoders.interleavedModificado import hampel_filter_forloop_numba, moving_average, busca_variancia
from time import time

'''
Amplitude and Phase plotter
---------------------------

Plot Amplitude and Phase of CSI frame_info
and update the plots in the same window.

Initiate Plotter with bandwidth, and
call update with CSI value.


Adicional:

'''

__all__ = [
    'Plotter'
]


class Plotter:
    def __init__(self, bandwidth, apply_hampel: bool, apply_smoothing: bool,
                 plot_phase: bool, plot_amp: bool, tam_janela: int, packets_refresh: int):
        self.bandwidth = bandwidth
        self.hampel = apply_hampel
        self.smoothing = apply_smoothing
        self.start = time()
        self._phase = plot_phase
        self._amp = plot_amp

        self.tamanho_janela = tam_janela
        self.atualizacao = packets_refresh

        self.janela_cheia = False  # nao mexer
        self.nsub = int(bandwidth * 3.2)

        self.fig, axs = plt.subplots(2, figsize=(15, 10))

        self.ax_amp = axs[0]
        self.ax_pha = axs[1]

        self.fig.suptitle('Nexmon CSI Real Time Explorer')

        # essa variavel de classe armazena os frames e seus valores de cada subportadora
        # a estrutura é um pouco confusa, mas a 1eira dimensão (com 2 pontos apenas) armazena amplitude e fase (0 e 1)
        # a segunda dimensao armazena os valores para cada subportadora
        # a terceira dimensao armazena os frames, serve como buffer.
        self.memoria_temporaria_frames = np.zeros((2, self.nsub, self.tamanho_janela))

        plt.ion()
        plt.show() 

    def cascata(self, csi, sequencia):
        """
        Essa função pega a matriz CSI e adiciona um novo frame à última posição colocando todos os frames anteriores
        uma posição a menos. O frame que ocupava a primeira posição da matriz é dropado.
        """
        if self._amp:
            amplitudes = np.abs(csi)
            a_entrar_amp = amplitudes

        if self._phase:
            fases = np.angle(csi, deg=True)
            a_entrar_phase = fases

        if self.janela_cheia:  # quando a janela está cheia, os frames entram somente na última posição.
            for i in range(self.tamanho_janela - 1, -1, -1):
                if self._amp:
                    copiar_amp = np.copy(self.memoria_temporaria_frames[0, :, i][:])
                    self.memoria_temporaria_frames[0, :, i] = a_entrar_amp
                    a_entrar_amp = copiar_amp

                if self._phase:
                    copiar_phase = np.copy(self.memoria_temporaria_frames[1, :, i])
                    self.memoria_temporaria_frames[1, :, i] = a_entrar_phase
                    a_entrar_phase = copiar_phase

        else:
            posicao = sequencia % self.tamanho_janela  # verificando qual posicao no buffer o csi vai entrar

            if self._amp:
                self.memoria_temporaria_frames[0, :, posicao] = amplitudes  # forma de obter as amplitudes
            if self._phase:
                self.memoria_temporaria_frames[1, :, posicao] = fases  # forma de obter as fases

    def update(self, csi, sequencia):
        if sequencia % self.atualizacao == 0 and self.janela_cheia:
            duracao = time() - self.start
            self.ax_amp.clear()
            self.ax_pha.clear()

            # These are also cleared with clear()
            self.ax_amp.set_ylabel('Amplitude')
            self.ax_pha.set_ylabel('Phase')
            self.ax_pha.set_xlabel('Sequencia Subportadora')
            self.fig.suptitle(f'Nexmon CSI Real Time Explorer - {duracao} s')
            self.start = time()

        self.cascata(csi, sequencia)

        if sequencia % self.tamanho_janela == 0 and sequencia != 0:
            self.janela_cheia = True

        if sequencia % self.atualizacao == 0 and sequencia != 0 and self.janela_cheia:
            amplitudes = self.memoria_temporaria_frames[0, :, -1*self.atualizacao:]

            if self.hampel:
                self.memoria_temporaria_frames[0, :, -1*self.atualizacao:] = hampel_filter_forloop_numba(amplitudes,
                                                                                      window_size=4,
                                                                                      n_subport=self.nsub)
                amplitudes = self.memoria_temporaria_frames[0, :, -1*self.atualizacao:]

            if self.smoothing:
                self.memoria_temporaria_frames[0, :, -1*self.atualizacao:] = moving_average(amplitudes, n_subport=self.nsub, window_size=10)
                amplitudes = self.memoria_temporaria_frames[0, :, -1*self.atualizacao:]

            subport_significativas = busca_variancia(amplitudes, self.nsub, k=12)

            # tenho que plotar todos os valores armazenados de cada subcarrier por vez
            try:
                for subportadora in subport_significativas:
                    amplitudes = self.memoria_temporaria_frames[0, subportadora, :]
                    fases = self.memoria_temporaria_frames[1, subportadora, :]

                    if self._amp:
                        self.ax_amp.plot(range(self.tamanho_janela), amplitudes, label=str(subportadora))

                    if self._phase:
                        np.unwrap(fases)
                        self.ax_pha.plot(range(self.tamanho_janela), fases, label=str(subportadora))

            except ValueError as err:
                print(
                    f'A ValueError occurred. Is the bandwidth {self.bandwidth} MHz correct?\nError: ', err
                )
                exit(-1)

            self.ax_amp.legend()
            self.ax_pha.legend()
            plt.draw()
            plt.pause(0.001)
    
    def __del__(self):
        pass
