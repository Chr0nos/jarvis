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
        # TODO : a critical flag to let the caller choose the fate of the
        # current script execution. If a non critical part of the script
        # fail we just want a message displayed, not a full fail
        # Could be done just with try ... except on this error when non critical
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

    def file_insert(self, filepath, content, line_index=0):
        """
        put "content" at the start of filepath
        """
        assert isinstance(content, str)
        print(f'inserting into {filepath} at line {line_index}:\n{content}')
        with open(os.path.join(self.mnt, filepath), 'r+') as fp:
            file_content = fp.readlines()
            fp.truncate(0)
            fp.seek(0)
            file_content.insert(line_index, content)
            fp.write('\n'.join(file_content))

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

    def install(self, packages, custom_servers=None):
        self.run(['pacstrap', self.mnt, 'base', 'archlinux-keyring'])
        fstab = self.run(['genfstab', '-t', 'UUID', self.mnt], True)
        if custom_servers:
            self.file_insert(
                filepath=os.path.join(self.mnt, '/etc/pacman.d/mirrorlist'),
                content='\n'.join([f'Server {server}' for server in custom_servers]),
                line_index=3)

        with ArchChroot(self.mnt):
            self.pkg_install(packages)
            self.file_put('/etc/hostname', self.hostname + '\n')
            self.file_put('/etc/fstab', fstab)
            self.file_put('/etc/locale.conf', f'LC_CTYPE={self.lang}\nLANG={self.lang}\n')
            self.file_put('/etc/locale.gen', self.locale_genfile())
            # TODO : Need to put keymap in /etc/vconsole.conf
            # Here is a very basic implementation, need a better option :
            self.file_put('/etc/vconsole.conf', f'KEYMAP={self.lang[:2]}\n')
            # Should be optional, not everyone wants to go through cloudflare's DNS
            # maybe a "system_config" section in the json/ --system-config in cmd
            self.file_put('/etc/resolv.conf', 'nameserver 1.1.1.1\nnameserver 1.0.0.1\n')
            # "set dufo free" XD tu m'as tué là
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
            # community/os-prober could be useful, the auto detection of windows
            # won't work without it
            self.pkg_install(['grub'])
            if not os.path.exists('/boot/grub'):
                os.mkdir('/boot/grub')
            self.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
            self.run(['grub-install', '--target', target, device])

    def install_refind(self, device, efi_path='/EFI/refind/refind_x64.efi', **kwargs):
        # @Chr0nos the esp can be mounted as /boot or /efi with current standard according to 
        # Arch wiki, and /boot/efi is an old path still used by other distro.
        # Note : in my case I tried to mount --bind /efi to /boot/efi to get around this test
        # and it fucked up everything
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

        # The /boot/efi path here should be an optional arg, because by default
        # refind-install will search for the esp by checking the gpt flags of
        # the partition which is better than hardcoding the path :P
        partition = partition_id(self.mnt + '/boot/efi')
        with ArchChroot(self.mnt):
            # Not needed
            self.run(['mkdir', '-vp', '/boot/efi/EFI/refind'])
            self.pkg_install(['extra/refind-efi'])
            # refind show error on --alldrivers ? okay :)
            # @Chr0nos rEFInd just warn about --alldrivers not being suitable for 
            # a normal install so it should be optional too
            self.run(['cp', '-vr',
                      '/usr/share/refind/drivers_x64',
                      '/boot/efi/EFI/refind/drivers_x64'])
        self.run(['refind-install', '--root', self.mnt + '/boot/efi'])
        # efi_path should be parsed from refind-install stdout, so maybe
        # self.run(capture=True) and a parsing function ? 
        if not os.path.exists(self.mnt + '/boot/efi' + efi_path):
            print(efi_path)
            raise ConfigError('unable to found the efi path on /boot/efi disk')
        # This should be Already done by refind-install, I got two EFI entry for rEFInd 
        # because of that, could be parsed from refind-install stdout too
        self.run([
            'efibootmgr', '-c',
            '-L', 'rEFInd',
            '-l', efi_path,
            '-d', device,
            '-p', str(partition),
        ])
        # refind-install also create /boot/refind_linux.conf with the kernel parameters
        # we could add custom kernel parameter option here and these values are wrong on
        # a live iso img so they need fixing.

    def mount(self, partition, mount_moint):
        self.run(['mount', partition, mount_moint])
