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


class ArchInstall():
    def __init__(self, hostname, mnt='/mnt', lang='fr_FR.UTF-8', username=None):
        self.mnt = mnt
        self.hostname = hostname
        self.lang = lang
        self.username = username

    def __str__(self):
        print(f'Archlinux Installer: {self.mnt} lang: {self.lang} host: {self.hostname}')

    def run(command):
        print('running', ' '.join(command))
        ret = subprocess.call(command)
        if ret != 0:
            raise CommandFail(command)

    def run_in(command):
        print('running in', ' '.join(command))
        self.run(['arch-chroot', self.mnt] + command)

    def install(self, packages):
       self.run(['pacstrap', mnt] + packages)
       self.run_in(['echo', self.hostname, '>', '/etc/hostname'])
       
       def services_enable(services):
           for service in services:
               self.run_in(['systemctl', 'enable', service])

        services_enable(['NetworkManager', 'gpm', 'fail2ban', 'smartd'])
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
        if self.username:
            self.setup_user(self.username)

    def setup_user(self, username, shell='/bin/zsh', groups=['audio', 'video', 'input', 'scanner', 'lp', 'render', 'games']):
        self.run_in(['useradd', '-s', shell, '-m', username])
        self.run_in(['chmod', '700', f'/home/{username}'])
        while True:
            try:
                self.run_in(['passwd', username])
                return
            except KeyboardInterrupt:
                print(f'setup of user {username} skipped: no password set')
                return
            except CommandFail:
                pass

    def install_grub(self):
        self.run_in(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])

    def install_refind(self, device):
        self.run_in(['refind-install', '--alldrivers', device])

    def mount(self, partition, mount_moint):
        self.run(['mount', partition, mount_moint])

    def run_as(self, username, command):
        """
        run the command 'command' into the chroot as username
        """
        self.run_in(['su', username, '-c', ' '.join(command)])

    def install_trizen(self, username):
        cmds = (
            ['git', 'clone', 'https://aur.archlinux.org/trizen.git',
             f'/home/{username}/trizen'],
            ['cd', f'/home/{username}/trizen', '&&', 'makepkg', '-si'],
            ['trizen', '-Sy']
        )

if __name__ == "__main__":
    arch = ArchInstall('localhost', username='adamaru')
    arch.install(DEFAULT)
    arch.install_refind('/dev/sda')
    arch.install_trizen(username='adamaru')
