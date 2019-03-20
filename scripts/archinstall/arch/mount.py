import os
import subprocess


class MountPoint():
    def __init__(self, dest, opts='defaults', fs_type=None, device=None):
        self.dest = dest
        self.opts = opts
        self.fs_type = fs_type
        self.device = device or fs_type

    def __str__(self):
        return self.dest

    def __hash__(self):
        return hash(self.dest)

    def is_mount(self):
        return os.path.ismount(self.dest)

    def get_cmd(self):
        cmd = ['mount']
        if self.fs_type:
            cmd += ['-t', self.fs_type]
        if self.opts:
            cmd += ['-o', self.opts]
        return cmd + [self.device, self.dest]

    def mount(self):
        print('mounting', self.dest)
        if not os.path.exists(self.dest):
            os.makedirs(self.dest, exist_ok=True)
        ret = subprocess.run(self.get_cmd())
        assert ret.returncode == 0, ret.returncode

    def unmount(self):
        if not self.is_mount:
            return
        ret = subprocess.run(['umount', self.dest])
        assert ret.returncode == 0, ret

    @staticmethod
    def list():
        lst = []
        with open('/proc/mounts', 'r') as fd:
            for line in fd.readlines():
                try:
                    device, mount_point, fs, opts, dump, pas = line.split()
                    lst.append({
                        'device': device,
                        'mnt': mount_point,
                        'fs': fs,
                        'opts': opts,
                        'dump': dump,
                        'pass': pas
                    })
                except ValueError:
                    pass
        return lst
