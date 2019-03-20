import os
from arch.mount import ArchChroot, MountPoint


class BootLoader():
    device = None
    name = None
    ai = None

    def __init__(self, ai, device=None):
        self.device = device

    def install(self, **kwargs):
        raise NotImplementedError

    @staticmethod
    def get_partition_id(path):
        """
        returns the partition id of a mount point.
        if the path is not a mount point a ValueError will be raised.
        """
        for mount in MountPoint.list():
            if mount['mnt'] == path:
                partition = int(mount['device'][-1])
                return partition
        raise ValueError(path)


class BootLoaderRefind(BootLoader):
    name = 'refind'
    efi = '/EFI/refind/refind_x64.efi'
    boot = '/boot/efi'

    def install_alldrivers(self):
        # refind show error on --alldrivers ? okay :)
        self.ai.run(['cp', '-vr',
            '/usr/share/refind/drivers_x64',
            '/boot/efi/EFI/refind/drivers_x64'])

    def install(self, alldrivers=True, **kwargs):
        assert self.ai.efi_capable, 'This system was not booted in uefi mode.'
        mnt = self.ai.mnt
        if not os.path.ismount(mnt + self.boot):
            raise(ConfigError('please create and mount /boot/efi (vfat)'))

        with ArchChroot(mnt):
            self.ai.run(['mkdir', '-vp', '/boot/efi/EFI/refind'])
            self.ai.pkg_install(['extra/refind-efi'])
            if alldrivers:
                self.install_alldrivers()

        # launching the install from outside of the chroot (host system)
        self.ai.run(['refind-install', '--root', mnt + self.boot])

        # TODO: check if this call is needed in a further test with vmware
        # partition = self.get_partition_id(mnt + self.boot)
        # self.ai.efi_mkentry('rEFInd', self.efi, device, partition)


class BootLoaderGrub(BootLoader):
    name = 'grub'

    def install(self, **kwargs):
        target = kwargs.get('target', 'i386-pc')
        with ArchChroot(self.ai.mnt):
            self.ai.pkg_install(['grub'] + ['community/os-prober'] if kwargs.get('os-prober') else [])
            if not os.path.exists('/boot/grub'):
                os.mkdir('/boot/grub')
            self.ai.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
            self.ai.run(['grub-install', '--target', target, self.device])

