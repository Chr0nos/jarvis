#!/usr/bin/python3
import subprocess
import os

from .services import *
from .tools import Cd, ArchChroot
from .exceptions import CommandFail, ConfigError
from .mount import MountPoint
from .metapkg import *

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


class FileFromHost(FileOperations):
    def __init__(self, filepath, mnt):
        super().__init__(filepath)
        self.filepath = os.path.join(mnt, filepath)


class BootLoader():
    device = None
    name = None
    ai = None

    def __init__(self, ai, device=None):
        self.device = device

    def install(self, **kwargs):
        raise NotImplementedError

    def get_partition_id(path):
        """
        returns the partition id of a mount point.
        """
        for mount in MountPoint.list():
            if mount['mnt'] == path:
                partition = int(mount['device'][-1])
                return partition
        raise ValueError(path)


class BootLoaderRefind(BootLoader):
    name = 'refind'
    efi = '/EFI/refind/refind_x64.efi'

    def install_alldrivers(self):
        # refind show error on --alldrivers ? okay :)
        self.ai.run(['cp', '-vr',
            '/usr/share/refind/drivers_x64',
            '/boot/efi/EFI/refind/drivers_x64'])

    def install(self, alldrivers=True, **kwargs):
        assert self.ai.efi_capable, 'This system was not booted in uefi mode.'
        mnt = self.ai.mnt
        if not os.path.ismount(mnt + '/boot/efi'):
            raise(ConfigError('please create and mount /boot/efi (vfat)'))

        with ArchChroot(mnt):
            self.ai.run(['mkdir', '-vp', '/boot/efi/EFI/refind'])
            self.ai.pkg_install(['extra/refind-efi'])
            if alldrivers:
                self.install_alldrivers()

        # launching the install from outside of the chroot (host system)
        self.ai.run(['refind-install', '--root', mnt + '/boot/efi'])

        # TODO: check if this call is needed in a further test with vmware
        # partition = self.get_partition_id(mnt + '/boot/efi')
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
        # cloudflares dns by default
        self.dns = [
            '1.1.1.1',
            '1.0.0.1'
        ]
        self.efi_capable = os.path.exists('/sys/firmware/efi')

    def __str__(self):
        print(f'Archlinux Installer: {self.mnt} lang: {self.lang} host: {self.hostname}')

    def __hash__(self):
        # the class is unique by it's mount point: one install per mount_point
        return hash(self.mnt)

    def run(self, command, capture=False, critical=True, **kwargs):
        if kwargs.get('debug_run'):
            del(kwargs['debug_run'])
            print('running', ' '.join(command), kwargs)
        if capture:
            return subprocess.check_output(command, **kwargs).decode('utf-8')
        ret = subprocess.run(command, **kwargs)
        if ret.returncode != 0 and critical:
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

    def locale_genfile(self):
        """
        return the content of /etc/locale.gen file based on self.locales
        """
        file_content = ''
        for locale, encoding in self.locales:
            file_content += f'{locale} {encoding}\n'
        return file_content

    def set_sudo_free(self, state):
        wheel = FileFromHost('/etc/sudoers.d/wheel')
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
        self.run(['pacstrap', self.mnt, 'base', 'archlinux-keyring'])
        fstab = self.run(['genfstab', '-t', 'UUID', self.mnt], True)
        if custom_servers:
            mirrors = FileFromHost('/etc/pacman.d/mirrorlist', self.mnt)
            mirrors.insert(File.to_config(custom_servers, prepend='Server '), line_index=3)

        with ArchChroot(self.mnt):
            self.pkg_install(packages))
            self.setup(fstab, vconsole)
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
            egrub.install(target='x86_64-efi' **kwargs)
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

    def mount(self, partition, mount_moint):
        self.run(['mount', partition, mount_moint])
