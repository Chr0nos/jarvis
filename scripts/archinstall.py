#!/usr/bin/python3
import subprocess
import argparse


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

DEFAULT = BASE + XORG + MATE

class CommandFail(Exception):
    pass


class ArchInstall():
    def __init__(self, hostname, mnt='/mnt', lang='fr_FR.UTF-8', username=None):
        self.mnt = mnt
        self.hostname = hostname
        self.lang = lang
        self.username = username

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
        self.run_in(['localctl', 'set-locale', f'LC_CTYPE={self.lang}'])
        self.run_in(['localctl', 'set-locale', f'LANG={self.lang}'])
        self.run_in(['locale-gen'])
        self.run_in(['chmod', '751', '/home'])
        self.run_in(['ln', '-s', '/usr/share/zoneinfo/Europe/Paris',
                     '/etc/localtime'])
        self.run_in(['mkdir', '-pv', '/etc/polkit-1/rules.d/'])
        if self.username:
            self.setup_user(self.username)
        self.run_in(['passwd'])


    def setup_user(self, username, shell='/bin/zsh', groups=['audio', 'video', 'input', 'scanner', 'lp', 'render', 'games']):
        self.run_in(['useradd', '-s', shell, '-m', username])
        self.run_in(['chmod', '700', f'/home/{username}'])
        while True:
            try:
                self.run_in(['passwd', username])
                return
            except KeyboardInterrupt:
                return
            except CommandFail:
                pass

    def install_grub(self):
        self.run_in(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])

    def install_refind(self, device):
        self.run_in(['refind-install', '--alldrivers', device])


if __name__ == "__main__":
    arch = ArchInstall('localhost', username='adamaru')
    arch.install(DEFAULT)
    arch.install_refind('/dev/sda')

