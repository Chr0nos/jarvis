
BASE = [
    'base', 'base-devel', 'networkmanager', 'htop', 'vim', 'net-tools',
    'zsh', 'terminator', 'fish', 'openssh', 'openssl',
    'gnome-keyring', 'hdparm', 'idle3-tools', 'iw',
    'gparted', 'ntfs-3g', 'exfat-utils', 'sshfs',
    'ffmpegthumbnailer', 'mdadm', 'wget', 'git'
]

DEV = [
    'git',
    'htop',
    'vim',
    'terminator',
    'clang',
    'gdb',
    'valgrind'
]

AUDIO = [
    'pulseaudio',
    'extra/pulseaudio-alsa',
    'pavucontrol'
]

EXTRA = [
    'extra/adwaita-icon-theme',
    'linux-headers',
    'firefox',
    'extra/firefox-i18n-fr',
    'community/firefox-adblock-plus',
    'community/mtpfs',
    'tree',
    'tmux'
]

FONTS = [
    'ttf-ubuntu-font-family',
    'ttf-dejavu',
    # 'ttf-freefont',
    'ttf-liberation',
    'otf-font-awesome',
	'ttf-croscore',
    'ttf-droid'
]

MATE = [
    'mate', 'mate-extra', 'mate-media', 'mate-power-manager', 'mate-menu'
]

XFCE = ['xfce4']
KDE = ['extra/plasma']
I3 = ['i3-gaps', 'community/i3status', 'i3blocks', 'i3lock']
GNOME = ['gnome']
CINNAMON = ['community/cinnamon']

PYTHON = [
    'extra/python',
    'extra/python-pip',
    'community/ipython'
]

META = {
    'audio': AUDIO,
    'base': BASE,
    'default': BASE + AUDIO + FONTS + MATE + EXTRA + PYTHON,
    'dev': DEV,
    'cinnamon': CINNAMON,
    'extra': EXTRA,
    'fonts': FONTS,
    'gnome': GNOME,
    'i3': I3,
    'kde': KDE,
    'mate': MATE,
    'python': PYTHON,
    'xfce': XFCE,
}

DEFAULT = BASE + AUDIO + FONTS + MATE + EXTRA + PYTHON
