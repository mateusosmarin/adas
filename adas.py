import signal
import sys
import time
import numpy as np
from matplotlib import animation
from matplotlib import pyplot as plt
from sklearn.cluster import OPTICS, DBSCAN, KMeans
from xwr18xx.xwr18xx import XWR18xx
from xwr18xx.tlv import MmwDemoOutputMessageType
from tabulate import tabulate

# For unix systems
xwr = XWR18xx('profile_no_grouping.cfg', '/dev/ttyACM0', '/dev/ttyACM1')

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
    if MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_DETECTED_POINTS in data.keys():
        yield data[MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_DETECTED_POINTS]


def update(data):
    x, y, z = data.T[0:3, :]

    global sc

    ax.cla()

    if len(data) >= min_samples_per_cluster:
        try:
            clust.fit(data)
        except Exception as e:
            print(data)
            print(e)
        c = np.array([colors[label] for label in clust.labels_])
        sc = ax.scatter(x, y, z, s=100, c=c)
    else:
        ax.cla()
        sc = ax.scatter(x, y, z, s=50)

    ax.set_title('DBSCAN')
    ax.set_xlim(-xlim, xlim)
    ax.set_ylim(-ylim, ylim)
    ax.set_zlim(-zlim, zlim)
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_zlabel('z (m)')
    fig.canvas.draw()

    return sc,


xlim = 5
ylim = 5
zlim = 5

min_samples_per_cluster = 2

fig = plt.figure('Detected objects')
ax = fig.add_subplot(projection='3d')
ax.set_title('DBSCAN')
ax.set_xlabel('x (m)')
ax.set_ylabel('y (m)')
ax.set_zlabel('z (m)')
sc = ax.scatter([], [], [])
clust = DBSCAN(min_samples=min_samples_per_cluster)
colors = [np.random.rand(3) for _ in range(256)]
colors.append(np.zeros(3))
ani = animation.FuncAnimation(
    fig, update, data_gen, interval=xwr.config.frame_periodicity)
plt.show()

while True:
    try:
        packet = xwr.read()
    except Exception as e:
        print('Failed to read the board')

    for t, v in packet.items():
        print(MmwDemoOutputMessageType(t).name)
        print(v)

xwr.close()
