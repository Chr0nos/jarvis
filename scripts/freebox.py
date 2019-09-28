#!/usr/bin/python3
""" Script script benchmarks the speed of a LAN connection
i use it to benchmark wifi setup and optimise them
"""

from getfile import getfile, hsize, SpeedOMetter
import matplotlib.pyplot as plt
import numpy as np
from time import time


if __name__ == "__main__":
    start_time = time()
    times = []
    speeds = []
    try:
        url = 'http://192.168.1.254/gen/100M'
        monitor = SpeedOMetter()
        for current, total in getfile(url, '/dev/null', chunksize=1000000):
            speed = monitor.update(current)
            speeds.append(speed / (1024 ** 2))
            times.append(time() - start_time)
            print(hsize(current), hsize(speed))
        plt.plot(times, speeds)
        plt.title('Freebox speed test')
        plt.xlabel = 'Time'
        plt.ylabel = 'Speed'
        plt.axhline(np.mean(speeds, 0), color='red', linestyle='--')
        plt.show()
    except KeyboardInterrupt:
        pass
