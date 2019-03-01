#!/usr/bin/python3
import subprocess
import argparse
import os


BASE = [
    'base', 'base-devel', 'networkmanager', 'htop', 'vim', 'net-tools',
    'pulseaudio', 'lightdm', 'lightdm-gtk-greeter', 'mpv', 'gpm', 'zsh',
    'terminator', 'fish', 'openssh', 'openssl', 'networkmanager-openvpn',
    'network-manager-applet', 'ttf-liberation', 'ttf-ubuntu-font-family',
    'ttf-dejavu', 'extra/pulseaudio-alsa', 'ttf-freefont', 'otf-font-awesome',
    'gnome-keyring', 'smartmontools', 'hdparm', 'idle3-tools', 'iw', 'fail2ban',
    'pavucontrol', 'gparted', 'ntfs-3g', 'exfat-utils', 'sshfs',
    'ffmpegthumbnailer'
]

XORG = [
    'xorg-server',
    'xorg-fonts-75dpi',
    'xorg-fonts-100dpi',
    'xorg-xrandr xorg-xinit',
    'extra/nvidia-dkms', 'extra/nvidia-settings',
    #'extra/xf86-video-vesa',
    #'extra/xf86-video-intel',
    #'extra/xf86-video-ati',
    #'extra/xf86-video-amdgpu',
    #'extra/xf86-video-vmware',
]

EXTRA = [
    'extra/adwaita-icon-theme',
    'linux-headers',
    'firefox', 'extra/firefox-i18n-fr', 'community/firefox-adblock-plus'
]

MATE = [
    'mate', 'mate-extra', 'mate-media', 'mate-power-manager', 'mate-menu',
    'system-config-printer'
]

XFCE = ['xfce4']
KDE = ['extra/plasma']
I3 = ['i3-gaps', 'community/i3status', 'i3blocks', 'i3lock']
GNOME = ['gnome']
CINNAMON = ['community/cinnamon']

PRINTER = [
    'extra/cups',
    'extra/cups-pdf',
    'extra/gutenprint',
    'extra/foomatic-db-gutenprint-ppds',
]

DEFAULT = BASE + XORG + MATE

class CommandFail(Exception):
    pass


class ArchUser():
    def __init__(self, ai, username):
        if not isinstance(ai, ArchInstall):
            raise ValueError(ai)
        self.username = username
        self.ai = ai

    def __str__(self):
        return f'ArchUser {self.username}'

    def __hash__(self):
        return hash(str(self))

    def run(self, command):
        self.ai.run_as(self.username, command)

    def get_defaults_groups(self):
        return ['audio', 'video', 'render', 'lp', 'input', 'scanner', 'games']

    def add_groups(self, groups):
        for group in groups:
            self.ai.run_in(['gpasswd', '-a', self.username, group])

    def create(self, shell='/bin/zsh'):
        self.ai.run_in(['useradd', '-m', '-s', shell, self.username])
        self.ai.run_in(['chown', f'{self.username}:{self.username}', f'/home/{self.username}'])
        self.ai.run_in(['chmod', '700', f'/home/{self.username}'])

    def set_pass(self):
        while True:
            try:
                self.ai.run_in(['passwd', self.username])
                return
            except KeyboardInterrupt:
                print(f'setup of user {self.username} skipped: no password set')
                return
            except CommandFail:
                pass

    def install_trizen(self):
        cmds = (
            ['git', 'clone', 'https://aur.archlinux.org/trizen.git',
             f'/home/{self.username}/trizen'],
            ['cd', f'/home/{self.username}/trizen', '&&', 'makepkg', '-si'],
            ['trizen', '-Sy']
        )
        for command in cmds:
            self.ai.run_as(self.username, command)

    def install(self, packages):
        self.run(['trizen', '-S', '--noedit', '--noconfirm'] + packages)

class ArchInstall():
    def __init__(self, hostname, mnt='/mnt', lang='fr_FR.UTF-8', pretend=True):
        self.mnt = mnt
        self.hostname = hostname
        self.lang = lang
        self.pretend = pretend

    def __str__(self):
        print(f'Archlinux Installer: {self.mnt} lang: {self.lang} host: {self.hostname}')

    def run(self, command):
        print('running', ' '.join(command))
        if self.pretend:
            return
        ret = subprocess.call(command)
        if ret != 0:
            raise CommandFail(command)

    def run_in(self, command):
        self.run(['arch-chroot', self.mnt] + command)

    def services_enable(self, services):
           for service in services:
               self.run_in(['systemctl', 'enable', service])

    def file_put(self, filepath, content):
        print('writing into', filepath + ':')
        print(content)
        if self.pretend:
            return
        filepath = os.path.join(self.mnt, filepath)
        with open(filepath, 'w+') as fd:
            fd.write(content)

    def install(self, packages):
        self.run(['pacstrap', self.mnt] + packages)
        self.file_put('/etc/hostname', self.hostname + '\n')
        self.services_enable(['NetworkManager', 'gpm', 'fail2ban', 'smartd'])
        self.run(['sh', '-c', 'genfstab', self.mnt, '>', self.mnt + '/etc/fstab'])
        commands = (
            ['localctl', 'set-locale', f'LC_CTYPE={self.lang}'],
            ['localctl', 'set-locale', f'LANG={self.lang}'],
            ['locale-gen'],
            ['chmod', '751', '/home'],
            ['ln', '-s', '/usr/share/zoneinfo/Europe/Paris', '/etc/localtime'],
            ['mkdir', '-pv', '/etc/polkit-1/rules.d/'],
            ['passwd'],
            ['mkinitcpio', '-p', 'linux'],
        )
        for cmd in commands:
            self.run_in(cmd)

    def install_grub(self):
        self.run_in(['pacman', '-S', 'grub'])
        self.run_in(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])

    def install_refind(self, device):
        self.run_in(['pacman', '-S', 'refind'])
        self.run_in(['refind-install', '--alldrivers', device])

    def mount(self, partition, mount_moint):
        self.run(['mount', partition, mount_moint])

    def run_as(self, username, command):
        """
        run the command 'command' into the chroot as username
        """
        self.run_in(['su', username, '-c', ' '.join(command)])


if __name__ == "__main__":
    arch = ArchInstall(hostname='localhost')
    arch.install(DEFAULT)
    arch.install_refind('/dev/sda')

    user = ArchUser(arch, username='adamaru')
    user.create()
    user.add_groups(user.get_defaults_groups() + ['wheel'])
    user.install_trizen()
    user.install(['visual-studio-code-bin', 'spotify'])

