#!/usr/bin/python3
import subprocess
import os

from .services import *
from .tools import ArchChroot
from .runner import CommandRunner
from .metapkg import *
from .bootloaders import BootLoaderRefind, BootLoaderGrub

class File():
    def __init__(self, filepath):
        self.filepath = filepath

    def put(self, content):
        print('writing into', self.filepath + ':')
        print(content)
        with open(self.filepath, 'w+') as fd:
            fd.write(content)

    def insert(self, content, line_index=0):
        """
        put "content" at the start of filepath
        """
        assert isinstance(content, str)
        print(f'inserting into {self.filepath} at line {line_index}:\n{content}')
        with open(self.filepath, 'r+') as fp:
            file_content = fp.readlines()
            fp.truncate(0)
            fp.seek(0)
            file_content.insert(line_index, content)
            fp.write('\n'.join(file_content))

    @staticmethod
    def to_config(data, separator='=', prepend=''):
        if isinstance(data, dict):
            return '\n'.join(list(f'{key}{separator}{value}' for key, value in data.items()))
        if isinstance(data, list):
            return '\n'.join(list(f'{prepend}{elem}' for elem in data))
        raise TypeError(data)


class FileFromHost(File):
    def __init__(self, filepath, mnt):
        super().__init__(filepath)
        self.filepath = os.path.join(mnt, filepath)


class ArchInstall(CommandRunner):
    def __init__(self, hostname, mnt='/mnt', lang='fr_FR.UTF-8'):
        """
        hostname: the machine hostname
        mnt: on wich mount point will you install arch ?
        this mountpoint must exists
        lang: a valid lang locale
        pretent: Dont run or change anything, just show what will be done.
        """
        super().__init__(mnt)
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
        # cloudflares dns by default
        self.dns = [
            '1.1.1.1',
            '1.0.0.1'
        ]

    def __str__(self):
        print(f'Archlinux Installer: {self.mnt} lang: {self.lang} host: {self.hostname}')

    def __hash__(self):
        # the class is unique by it's mount point: one install per mount_point
        return hash(self.mnt)

    def pkg_install(self, packages):
        self.run(['pacman', '-S', '--noconfirm'] + packages)

    def locale_genfile(self):
        """
        return the content of /etc/locale.gen file based on self.locales
        """
        file_content = ''
        for locale, encoding in self.locales:
            file_content += f'{locale} {encoding}\n'
        return file_content

    def set_sudo_free(self, state):
        wheel = FileFromHost('/etc/sudoers.d/wheel', self.mnt)
        if not state:
            wheel.put('%wheel ALL=(ALL) ALL\n')
        else:
            wheel.put('%wheel ALL=(ALL) NOPASSWD: ALL\n')

    def setup(self, fstab, vconsole):
        files_content = (
            ('/etc/hostname', self.hostname + '\n'),
            ('/etc/fstab', fstab),
            ('/etc/locale.conf', File.to_config({'LC_CTYPE': self.lang, 'LANG': self.lang})),
            ('/etc/locale.gen', self.locale_genfile()),
            ('/etc/vconsole.conf', File.to_config(vconsole)),
            ('/etc/resolv.conf', File.to_config(self.dns, prepend='nameserver ')),
            ('/etc/sudoers.d/targetpw', 'Defaults targetpw\n')
        )
        for filepath, content in files_content:
            FileFromHost(filepath, self.mnt).put(content)
        self.set_sudo_free(True)


    def install(self, packages, custom_servers=None, vconsole={'KEYMAP': 'us'}):
        self.run(['pacstrap', self.mnt, 'base', 'archlinux-keyring', 'sudo'])
        fstab = self.run(['genfstab', '-t', 'UUID', self.mnt], True)
        if custom_servers:
            mirrors = FileFromHost('/etc/pacman.d/mirrorlist', self.mnt)
            mirrors.insert(File.to_config(custom_servers, prepend='Server '), line_index=3)

        with ArchChroot(self.mnt):
            self.setup(fstab, vconsole)
            self.run(['pacman', '-Sy'])
            self.pkg_install(packages)
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
            refind = BootLoaderRefind(self, device)
            refind.install(alldrivers=kwargs.get('alldrivers', True))
        elif name == 'grub':
            grub = BootLoaderGrub(self, device)
            grub.install(**kwargs)
        elif name == 'grub-efi':
            egrub = BootLoaderGrub(self, device)
            egrub.install(target='x86_64-efi', **kwargs)
        else:
            raise ValueError(name)

    def efi_mkentry(self, label, efi_path, device, partition, efi_mnt=None):
        """
        create a new uefi entry into the bios
        also checks thats the provided informations are correct.
        """
        if not efi_mnt:
            efi_mnt = self.mnt + '/boot/efi'
        assert os.path.exists(efi_mnt + efi_path), '.efi file not found'
        assert os.path.exists(device), 'device not found'
        assert isinstance(partition, int)
        assert os.path.exists(device + partition), 'partition not found'
        self.run([
            'efibootmgr', '-c',
            '-L', label,
            '-l', efi_path,
            '-d', device,
            '-p', str(partition),
        ])
        # refind-install also create /boot/refind_linux.conf with the kernel parameters
        # we could add custom kernel parameter option here and these values are wrong on
        # a live iso img so they need fixing.

    def mount(self, partition, mount_moint):
        self.run(['mount', partition, mount_moint])
