import os
from .mount import MountPoint


class Chroot():
    def __init__(self, path):
        self.real_root = os.open('/', os.O_RDONLY)
        self.path = path

    def start(self):
        os.chroot(self.path)
        os.chdir('/')

    def stop(self):
        os.chdir(self.real_root)
        os.chroot('.')
        os.close(self.real_root)

    def __enter__(self):
        self.start()

    def __exit__(self, a, b, c):
        self.stop()

    @staticmethod
    def decorator(path):
        def real_decorator(func):
            def wrapper(*args, **kwargs):
                with Chroot(path):
                    func(*args, **kwargs)
            return wrapper
        return real_decorator


class ArchChroot(Chroot):
    def __init__(self, path, unbind=False):
        super().__init__(path)
        self.mounts = [
            MountPoint(f'{path}/proc', opts='nosuid,noexec,nodev', fs_type='proc'),
            MountPoint(f'{path}/dev', opts='mode=0755,nosuid', fs_type='devtmpfs'),
            MountPoint(f'{path}/dev/pts', opts='mode=1777,nosuid,nodev', fs_type='devpts'),
            MountPoint(f'{path}/dev/shm', opts='nodev,nosuid', fs_type='tmpfs'),
            MountPoint(f'{path}/run', opts='nosuid,nodev,mode=0775', fs_type='tmpfs'),
            MountPoint(f'{path}/tmp', opts='mode=1777,strictatime,nodev,nosuid', fs_type='tmpfs'),
            MountPoint(f'{path}/sys', opts='nosuid,noexec,nodev,ro', fs_type='sysfs')
        ]
        if os.path.exists('/sys/firmware/efi'):
            self.mounts.append(
                MountPoint(f'{path}/sys/firmware/efi/efivars', opts='nosuid,noexec,nodev', fs_type='efivarfs')
            )
        self.unbind = unbind

    def start(self):
        for bind in self.mounts:
            if bind.is_mount() is not False:
                bind.mount()
        super().start()

    def stop(self):
        if self.unbind:
            for bind in self.mounts:
                bind.unmount()
        super().stop()


class Cd():
    """
    context manager to change dir and then goes back into the original dir.
    """
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.origin = os.getcwd()
        os.chdir(self.path)
        return (self.origin, self.path)

    def __exit__(self, a, b, c):
        os.chdir(self.origin)
