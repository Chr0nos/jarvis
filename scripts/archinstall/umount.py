#/usr/bin/python3

from arch.tools import ArchChroot

if __name__ == "__main__":
    with ArchChroot('/mnt', undind=True):
        print('unmounting all arch-chroot binds')
