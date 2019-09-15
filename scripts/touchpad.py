#!/usr/bin/python3
from subprocess import run
import sys

MODULE = 'i2c_hid'

if __name__ == "__main__":
    argc = len(sys.argv)
    if argc < 2:
        raise ValueError
    if sys.argv[1] == 'pre':
        run(['rmmod', MODULE], check=True)
    elif sys.argv[1] == 'post':
        run(['modprobe', MODULE], check=True)

        # be able to see the screen could be nice
        brightness = int(run(['xbacklight'], capture_output=True).decode('utf-8')[0:-1])
        if brightness < 5:
            run(['xbacklight', '-set', 35])

        run(['setxkbmap', 'us_qwerty-fr'])

