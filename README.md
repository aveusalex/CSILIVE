# CSILIVE Explorer

A fast and simple CSI decoder written in Python.

You can:
- Plot CSI samples transmitted through your raspberry pi in real time.
- Read CSI samples to use in your Python programs!

## Plotting

1. Install dependencies: `pip install numpy matplotlib`
2. Only works (for now) with bcm43455c0 (Pi 4/3B+)
3. Specify the IP address of the server and the port to be used.
4. Run csi-explorer: `python3 CSIExplorerSERVER.py`




Null-subcarriers can be hidden, you can change this in the variables on the file.

## Using csi-explorer in your programs.

You can integrate csi-explorer into your python programs.
Here is an example for the 'Interleaved' decoder for bcm43455c0 and bcm4339,



## Original Authors
* [@Gi-z](https://github.com/Gi-z) - Glenn Forbes
* [@zeroby0](https://github.com/zeroby0) - Aravind Voggu
* [@tweigel-dev](https://github.com/tweigel-dev) - Thomas Weigel