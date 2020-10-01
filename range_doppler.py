import signal
import sys
import time
import numpy as np
from matplotlib import animation
from matplotlib import pyplot as plt
from xwr18xx.xwr18xx import XWR18xx
from xwr18xx.tlv import MmwDemoOutputMessageType
from tabulate import tabulate

# For unix systems
xwr = XWR18xx('range_doppler.cfg', '/dev/ttyACM0', '/dev/ttyACM1')

# For widows systems
# xwr = XWR18xx('profile.cfg', 'COM9', 'COM11')


def interrupt_handler(signum, frame):
    print('\nExiting')
    xwr.close()
    sys.exit()


signal.signal(signal.SIGINT, interrupt_handler)

xwr.load_config()

print()
print(tabulate([[k, v]
                for k, v in vars(xwr.config).items() if k != 'config_file'], headers=['config', 'value']))
print()


def data_gen():
    data = xwr.read()
    yield data[MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP]


def update(data):
    data = np.fft.fftshift(data.T, axes=(0,))
    c = ax.contourf(r, d, data)
    return c,


fig = plt.figure('Range-Doppler Heatmap')
ax = fig.add_subplot(111)
ax.set_xlabel('Range (m)')
ax.set_ylabel('Doppler (m/s)')
r = np.linspace(0, xwr.config.range_max, xwr.config.range_fft_size)
d = np.linspace(-xwr.config.doppler_max, xwr.config.doppler_max,
                xwr.config.doppler_fft_size)
ani = animation.FuncAnimation(
    fig, update, data_gen, interval=xwr.config.frame_periodicity)
plt.show()

while True:
    try:
        packet = xwr.read()
    except Exception as e:
        print('Failed to read the board')
        xwr.close()
        sys.exit()

    for t, v in packet.items():
        print(MmwDemoOutputMessageType(t).name)
        print(v)

xwr.close()
