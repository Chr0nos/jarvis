#!/usr/bin/python3
import subprocess
import os


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

class XorgSection:
    kind = None
    identifier = None


class XorgDevice(XorgSection):
    driver = None
    kind = "Device"
    fields = ()

    def __str__(self):
        content = []
        class_fields = [
            ('Identifier', self.identifier)
        ]
        if self.driver:
            class_fields.append(('Driver', self.driver))
        for key, value in (tuple(class_fields)) + self.fields:
            if isinstance(value, str):
                value = f'"{value}"'
            # transorm: ['a', 'b', 'c'] to: "a" "b" "c"
            elif isinstance(value, list):
                line = ''
                for x in value:
                    line += f'"{x}" '
                value = line[0:-1]
            content.append(f'\t{key:<15} {value}')
        extra = self.extra()
        if extra:
            content.append('\n'.join(extra))
        return \
            f'Section "{self.kind}"\n' + '\n'.join(content) + '\nEndSection\n'

    def extra(self):
        return None


class XorgNvidiaCard(XorgDevice):
    driver = 'nvidia'
    identifier = 'Nvidia graphic card'
    fields = (
        ('VendorName', 'Nvidia Corporation'),
    )


class NouveauCard(XorgDevice):
    driver = 'nouveau'
    identifier = 'Nouveau graphic card'


class VesaCard(XorgDevice):
    driver = 'vesa'
    identifier = 'vesa device'


class XorgMonitor(XorgDevice):
    identifier = 'Monitor0'
    kind = 'Monitor'
    fields = (
        ('Option', 'DPMS'),
    )


class XorgScreen(XorgDevice):
    identifier = 'Screen0'
    kind = 'Screen'
    fields = (
        ('DefaultDepth', 24),
        ('Option', ['Stereo', '0']),
        ('Option', ['nvidiaXineramaInfoOrder', 'DFP-0']),
        ('Option', ['SLI', 'Off']),
        ('Option', ['BaseMosaic', 'Off']),
    )

    def __init__(self, card):
        self.card = card
        self.fields = (('Device', card.identifier),) + self.fields

    def extra(self) -> tuple:
        depth_name = 'Depth'
        depth = 24
        return ('\tSubSection "Display"', f'\t\t{depth_name:<8}{depth}', '\tEndSubSection')


def run():
    kernel = KernelOpts()
    prober = Modprobe()
    prober.blacklist = kernel.get('modprobe.blacklist').split(',')
    prober.load = kernel.get('modprobe.load').split(',')
    prober.run()

    nvidia_cfg = '/etc/X11/xorg.conf.d/20-nvidia.conf'
    if 'nvidia' in prober.load:
        nv = XorgNvidiaCard()
        sc = XorgScreen(nv)
        mo = XorgMonitor()
        config = '\n'.join([sc, mo, nv])
        with open(nvidia_cfg, 'w') as cfg:
            cfg.write(config)
    else:
        os.unlink(nvidia_cfg)


if __name__ == "__main__":
    nv = XorgNvidiaCard()
    sc = XorgScreen(nv)
    mo = XorgMonitor()
    print(nv, mo, sc, sep='\n', end='')
    #run()
