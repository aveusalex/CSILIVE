"""
Interleaved
===========

Fast and efficient methods to extract
Interleaved CSI frame_info in PCAP files.

~230k frame_info per second.

Suitable for bcm43455c0 and bcm4339 chips.

Requires Numpy.

Usage
-----

import decoders.interleaved as decoder

frame_info = decoder.read_pcap('path_to_pcap_file')

Bandwidth is inferred from the pcap file, but
can also be explicitly set:
frame_info = decoder.read_pcap('path_to_pcap_file', bandwidth=40)
"""

__all__ = [
    'read_frame',
    'hampel_filter_forloop_numba',
    'moving_average',
    'busca_variancia'
]

import numpy as np
# from numba import jit
from statistics import variance


np.seterr(all="ignore")

# Indexes of Null and Pilot OFDM subcarriers
# https://www.oreilly.com/library/view/80211ac-a-survival/9781449357702/ch02.html
nulls = {
    20: [x+32 for x in [
        -32, -31, -30, -29,
        31,  30,  29,  0
    ]],

    40: [x+64 for x in [
        -64, -63, -62, -61, -60, -59, -1, 
        63,  62,  61,  60,  59,  1,  0
    ]],

    80: [x+128 for x in [
        -128, -127, -126, -125, -124, -123, -1,
        127,  126,  125,  124,  123,  1,  0
    ]],

    160: [x+256 for x in [
        -256, -255, -254, -253, -252, -251, -129, -128, -127, -5, -4, -3, -2, -1,
        255,  254,  253,  252,  251,  129,  128,  127,  5,  4,  3,  3,  1,  0
    ]]
}

pilots = {
    20: [x+32 for x in [
        -21, -7,
         21,  7
    ]],

    40: [x+64 for x in [
        -53, -25, -11, 
         53,  25,  11
    ]],

    80: [x+128 for x in [
        -103, -75, -39, -11,
         103,  75,  39,  11
    ]],

    160: [x+256 for x in [
        -231, -203, -167, -139, -117, -89, -53, -25,
         231,  203,  167,  139,  117,  89,  53,  25
    ]]
}


class SampleSet(object):
    """
        A helper class to contain data read
        from pcap files.
    """
    def __init__(self, sampless, bandwidth):
        self.mac, self.seq, self.css, self.csi = sampless

        self.nsamples = self.csi.shape[0]
        self.bandwidth = bandwidth

    def get_mac(self, index):
        return self.mac[index*6: (index+1)*6]

    def get_seq(self, index):
        sc = int.from_bytes(  # uint16: SC
            self.seq[index*2: (index+1)*2],
            byteorder='little',
            signed=False
        )
        fn = sc % 16  # Fragment Number
        sc = int((sc - fn)/16)  # Sequence Number

        return sc, fn
    
    def get_css(self, index):
        return self.css[index*2: (index+1)*2]

    def get_csi(self, index, rm_nulls=False, rm_pilots=False):
        csi = self.csi[index].copy()
        if rm_nulls:
            csi[nulls[self.bandwidth]] = 0
        if rm_pilots:
            csi[pilots[self.bandwidth]] = 0

        return csi
   
    def print(self, index, n_frame):
        # Mac ID
        macid = self.get_mac(index).hex()
        macid = ':'.join([macid[i:i+2] for i in range(0, len(macid), 2)])

        # Sequence control
        sc, fn = self.get_seq(index)

        # Core and Spatial Stream
        css = self.get_css(index).hex()

        print(
            f'''
Sample #{n_frame}
---------------
Source Mac ID: {macid}
Sequence: {sc}.{fn}
Core and Spatial Stream: 0x{css}
            '''
        )


def __find_bandwidth(incl_len):  # incl_len é o tamanho do pacote
    """
        Determines bandwidth
        from length of packets.

        incl_len is the 4 bytes
        indicating the length of the
        packet in packet header
        https://wiki.wireshark.org/Development/LibpcapFileFormat/

        This function is immune to small
        changes in packet lengths.
    """

    pkt_len = incl_len

    # The number of bytes before we
    # have CSI data is 60. By adding
    # 128-60 to frame_len, bandwidth
    # will be calculated correctly even
    # if frame_len changes +/- 128
    # Some packets have zero padding.
    # 128 = 20 * 3.2 * 4
    nbytes_before_csi = 0
    pkt_len += (128 - nbytes_before_csi)

    bandwidth = 20 * int(
        pkt_len // (20 * 3.2 * 4)
    )

    return bandwidth


def read_frame(frame, bandwidth=0, nsamples_max=1):
    """
        Reads CSI frame_info from
        a pcap file. A SampleSet
        object is returned.

        Bandwidth and maximum frame_info
        are inferred from the pcap file by
        default, but you can also set them explicitly.
    """

    # Number of OFDM sub-carriers
    nsub = int(bandwidth * 3.2)
    fc = frame[:18 + nsub*4]

    # Preallocating memory
    mac = bytearray(nsamples_max * 6)
    seq = bytearray(nsamples_max * 2)
    css = bytearray(nsamples_max * 2)
    csi = bytearray(nsamples_max * nsub * 4)

    # Pointer to current location in file.
    # This is faster than using file.tell()
    # =24 to skip pcap global header
    ptr = 0  # nao temos global header, apenas packet header + nexmon metadata

    nsamples = 0
############################## essa é a parte que nos interessa ##################################

    # 4 bytes: Magic Bytes               @ 0 - 4
    # 6 bytes: Source Mac ID             @ 4 - 10
    # 2 bytes: Sequence Number           @ 10 - 12
    # 2 bytes: Core and Spatial Stream   @ 12 - 14
    # 2 bytes: ChanSpec                  @ 14 - 16
    # 2 bytes: Chip Version              @ 16 - 18
    # nsub*4 bytes: CSI Data             @ 18 - 18 + nsub*4

    mac[nsamples*6: (nsamples+1)*6] = fc[ptr+4: ptr+10]
    seq[nsamples*2: (nsamples+1)*2] = fc[ptr+10: ptr+12]
    css[nsamples*2: (nsamples+1)*2] = fc[ptr+12: ptr+14]
    csi[nsamples*(nsub*4): (nsamples+1)*(nsub*4)] = fc[ptr+18: ptr+18 + nsub*4]

    # ptr += (frame_len - 42)
    nsamples += 1

    # Convert CSI bytes to numpy array
    try:
        csi_np = np.frombuffer(
            csi,
            dtype=np.int16,
            count=nsub * 2 * nsamples
        )
    except:
        print("Buffer recebido menor do que o esperado...")
        return -1

    # Cast numpy 1-d array to matrix
    csi_np = csi_np.reshape((nsamples, nsub * 2))

    # Convert csi into complex numbers
    csi_cmplx = np.fft.fftshift(
            csi_np[:nsamples, ::2] + 1.j * csi_np[:nsamples, 1::2], axes=(1,)
    )

    return SampleSet(
        (mac,
         seq,
         css,
         csi_cmplx),
        bandwidth
    )


# A partir daqui estarão descritas funções de processamento dos sinais e filtragem.


# @jit(nopython=True)
# reference: https://towardsdatascience.com/outlier-detection-with-hampel-filter-85ddf523c73d
def hampel_filter_forloop_numba(input_series, window_size, n_subport, n_sigmas=3):
    new_series = input_series.copy()
    k = 1.4826  # scale factor for Gaussian distribution
    n = len(new_series[0, :])
    for subportadora in range(n_subport):
        amps_subportadora = new_series[subportadora, :].copy()

        for i in range(window_size, n - window_size):
            x0 = np.nanmedian(amps_subportadora[i - window_size:i + window_size])
            S0 = k * np.nanmedian(np.abs(amps_subportadora[i - window_size:i + window_size] - x0))

            if i - window_size == 0:  # tanto os primeiros quantos os ultimos valores não estão sendo pegos
                for j in range(window_size+1):
                    if np.abs(amps_subportadora[j] - x0) > n_sigmas * S0:
                        new_series[subportadora, j] = x0
            elif i + window_size == n - 1:
                for j in range(n - window_size, n):
                    if np.abs(amps_subportadora[j] - x0) > n_sigmas * S0:
                        new_series[subportadora, j] = x0
            else:
                if np.abs(amps_subportadora[i] - x0) > n_sigmas * S0:
                    new_series[subportadora, i] = x0

    return new_series


# @jit(nopython=True)
# Inspired by https://towardsdatascience.com/moving-averages-in-python-16170e20f6c
def moving_average(input_series, window_size, n_subport):
    mean_series = input_series.copy()
    n = len(mean_series[0, :])
    for subportadora in range(n_subport):
        amps_subportadora = mean_series[subportadora, :].copy()

        for idx in range(n):
            if idx - window_size >= 0:
                mean = amps_subportadora[idx-window_size:idx].sum() / window_size
            else:
                mean = amps_subportadora[:idx+1].sum() / (idx+1)

            mean_series[subportadora, idx] = mean

    return mean_series


def busca_variancia(input_series, n_subport, plot=0, k=12):
    variancias_por_sub = {}

    for subportadora in range(n_subport):
        amps_subportadora = input_series[subportadora, :]
        variancia = variance(amps_subportadora)
        variancias_por_sub[variancia] = subportadora



    variancias = list(variancias_por_sub.keys())
    variancias = sorted(variancias, reverse=True)
    return [variancias_por_sub[x] for x in variancias[:k]]


if __name__ == "__main__":
    samples = read_frame('pcap_files/output-40.pcap')
