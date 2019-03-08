#!/usr/bin/python3
import subprocess
import os

from .services import *
from .tools import Cd, ArchChroot
from .exceptions import CommandFail, ConfigError
from .mount import MountPoint
from .metapkg import *

class ArchInstall():
    def __init__(self, hostname, mnt='/mnt', lang='fr_FR.UTF-8'):
        """
        hostname: the machine hostname
        mnt: on wich mount point will you install arch ?
        this mountpoint must exists
        lang: a valid lang locale
        pretent: Dont run or change anything, just show what will be done.
        """
        if not os.path.exists(mnt):
            raise ValueError('invalid mount point you morron: ' + mnt)
        self.mnt = mnt
        self.hostname = hostname
        self.lang = lang
        self.timezone = 'Europe/Paris'
        self.locales = [
            ('fr_FR.UTF-8', 'UTF-8'),
            ('fr_FR', 'ISO-8859-1'),
            ('fr_FR@euro', 'ISO-8859-15'),
            ('en_US.UTF-8', 'UTF-8'),
            ('en_US', 'ISO-8859-1')
        ]
        self.efi_capable = os.path.exists('/sys/firmware/efi')

    def __str__(self):
        print(f'Archlinux Installer: {self.mnt} lang: {self.lang} host: {self.hostname}')

    def __hash__(self):
        # the class is unique by it's mount point: one install per mount_point
        return hash(self.mnt)

    def run(self, command, capture=False, **kwargs):
        if kwargs.get('debug_run'):
            del(kwargs['debug_run'])
            print('running', ' '.join(command), kwargs)
        if capture:
            return subprocess.check_output(command, **kwargs).decode('utf-8')
        ret = subprocess.run(command, **kwargs)
        if ret.returncode != 0:
            raise CommandFail(command)

    def run_in(self, command, user=None, **kwargs):
        with ArchChroot(self.mnt):
            if not user:
                return self.run(command, **kwargs)
            assert isinstance(user, ArchUser)
            return self.run(command, preexec_fn=user.demote(), **kwargs)

    def pkg_install(self, packages):
        self.run(['pacman', '-S', '--noconfirm'] + packages)

    def edit(self, filepath):
        self.run_in(['vim', filepath])

    def file_put(self, filepath, content):
        print('writing into', filepath + ':')
        print(content)
        filepath = os.path.join(self.mnt, filepath)
        with open(filepath, 'w+') as fd:
            fd.write(content)

    def locale_genfile(self):
        """
        return the content of /etc/locale.gen file based on self.locales
        """
        file_content = ''
        for locale, encoding in self.locales:
            file_content += f'{locale} {encoding}\n'
        return file_content

    def set_sudo_free(self, state):
        if not state:
            self.file_put('/etc/sudoers.d/wheel', '%wheel ALL=(ALL) ALL\n')
        else:
            self.file_put('/etc/sudoers.d/wheel', '%wheel ALL=(ALL) NOPASSWD: ALL\n')

    def install(self, packages):
        if packages:
            self.run(['pacstrap', self.mnt] + packages)
        fstab = self.run(['genfstab', self.mnt], True)
        with ArchChroot(self.mnt):
            # reinstall keyrings...
            self.pkg_install(['archlinux-keyring'])
            self.file_put('/etc/hostname', self.hostname + '\n')
            self.file_put('/etc/fstab', fstab)
            self.file_put('/etc/locale.conf', f'LC_CTYPE={self.lang}\nLANG={self.lang}\n')
            self.file_put('/etc/locale.gen', self.locale_genfile())
            self.file_put('/etc/resolv.conf', 'nameserver 1.1.1.1\nnameserver 1.0.0.1\n')
            self.set_sudo_free(True)
            self.file_put('/etc/sudoers.d/targetpw', 'Defaults targetpw\n')
            commands = (
                # System has not been booted with systemd as init (PID 1). Can't operate.
                # ['timedatectl', 'set-ntp', 'true'],
                ['locale-gen'],
                ['chmod', '751', '/home'],
                ['ln', '-sf', f'/usr/share/zoneinfo/{self.timezone}', '/etc/localtime'],
                ['mkdir', '-pv', '/etc/polkit-1/rules.d/'],
                ['mkinitcpio', '-p', 'linux'],
            )
            for cmd in commands:
                self.run(cmd)

    def passwd(self):
        print('set root password')
        with ArchChroot(self.mnt):
            self.run(['passwd'])

    def install_bootloader(self, name, device, **kwargs):
        if name == 'refind':
            self.install_refind(device)
        elif name == 'grub':
            self.install_grub(device, **kwargs)
        elif name == 'grub-efi':
            self.install_grub(device, target='x86_64-efi', **kwargs)
        else:
            raise ValueError(name)

    def install_grub(self, device, target='i386-pc', **kwargs):
        with ArchChroot(self.mnt):
            self.pkg_install(['grub'])
            if not os.path.exists('/boot/grub'):
                os.mkdir('/boot/grub')
            self.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
            self.run(['grub-install', '--target', target, device])

    def install_refind(self, device, efi_path='/EFI/refind/refind_x64.efi', **kwargs):
        if not os.path.ismount(self.mnt + '/boot/efi'):
            raise(ConfigError('please create and mount /boot/efi (vfat)'))

        def partition_id(mount_path):
            """
            returns the partition id of a mount point.
            """
            for mount in MountPoint.list():
                if mount['mnt'] == mount_path:
                    partition = int(mount['device'][-1])
                    return partition
            raise ValueError(mount_path)

        partition = partition_id(self.mnt + '/boot/efi')
        with ArchChroot(self.mnt):
            self.run(['mkdir', '-vp', '/boot/efi/EFI/refind'])
            self.pkg_install(['extra/refind-efi'])
            # refind show error on --alldrivers ? okay :)
            self.run(['cp', '-vr',
                      '/usr/share/refind/drivers_x64',
                      '/boot/efi/EFI/refind/drivers_x64'])
        self.run(['refind-install', '--root', self.mnt + '/boot/efi'])
        if not os.path.exists(self.mnt + '/boot/efi' + efi_path):
            print(efi_path)
            raise ConfigError('unable to found the efi path on /boot/efi disk')
        self.run([
            'efibootmgr', '-c',
            '-L', 'rEFInd',
            '-l', efi_path,
            '-d', device,
            '-p', str(partition),
        ])

    def mount(self, partition, mount_moint):
        self.run(['mount', partition, mount_moint])
