#!/usr/bin/python3
import subprocess


class KernelOpts:
    def __init__(self):
        self.data = self.dict()

    def get_boot_line(self):
        with open('/proc/cmdline') as fp:
            line = fp.read()
        return line[0:-1]

    def dict(self):
        d = {}
        params = self.get_boot_line().split(' ')
        for param in params:
            try:
                key, value = param.split('=', 1)
                d[key] = value
            except ValueError:
                pass
        return d

    def get(self, *args, **kwargs):
        return self.data.get(*args, **kwargs)


class Modprobe:
    blacklist = []
    load = []

    def run(self, **kwargs):
        for m in self.blacklist:
            subprocess.run(['rmmod', m], **kwargs)
        for m in self.load:
            subprocess.run(['modprobe', m], **kwargs)


def run():
    kernel = KernelOpts()
    prober = Modprobe()
    prober.blacklist = kernel.get('modprobe.blacklist').split(',')
    prober.load = kernel.get('modprobe.load').split(',')
    prober.run()

if __name__ == "__main__":
    run()
