# CSILIVE Explorer

A fast and simple CSI decoder written in Python.

You can:
- Plot CSI samples transmitted through your raspberry pi in real time.
- Read CSI samples to use in your Python programs!

Requires:
- [Nexmon CSI](https://github.com/seemoo-lab/Nexmon_csi) installed on Raspberry Pi!

## Plotting

1. Install dependencies: `pip install numpy matplotlib`
2. Only works (for now) with bcm43455c0 (Pi 4/3B+)
3. Specify the IP address of the server and the port to be used.
4. Run csi-explorer: `python3 CSIExplorerSERVER.py`
5. Run CSI client in your raspberry Pi: `python3 Clientpi.py`

Null and pilot-subcarriers can be hidden, you can change this in the variables on the file.


## Original Authors
* [@Gi-z](https://github.com/Gi-z) - Glenn Forbes
* [@zeroby0](https://github.com/zeroby0) - Aravind Voggu
* [@tweigel-dev](https://github.com/tweigel-dev) - Thomas Weigel

## Modifications by:
* [@aveusalex](https://github.com/aveusalex) - Alex Echeverria

## Original Repository
* [CSI Explorer](https://github.com/nexmonster/nexmon_csi/tree/feature/python/utils/python)