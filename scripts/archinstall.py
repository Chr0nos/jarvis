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
    'gnome-keyring', 'hdparm', 'idle3-tools', 'iw',
    'pavucontrol', 'gparted', 'ntfs-3g', 'exfat-utils', 'sshfs',
    'ffmpegthumbnailer', 'mdadm', 'wget', 'git', 'archlinux-keyring'
]

XORG = [
    'xorg-server',
    'xorg-fonts-75dpi',
    'xorg-fonts-100dpi',
    'xorg-xrandr',
    'xorg-xinit',
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
    'firefox', 'extra/firefox-i18n-fr', 'community/firefox-adblock-plus',
    'community/mtpfs',
    'tree'
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

PYTHON = [
    'extra/python',
    'extra/python-pip',
    'community/ipython'
]

DEFAULT = BASE + XORG + MATE + EXTRA + PYTHON

class CommandFail(Exception):
    pass

class ConfigError(Exception):
    pass


# TODO : add device param
class MountPoint():
    def __init__(self, dest, opts='defaults', fs_type=None, device=None):
        self.dest = dest
        self.opts = opts
        self.fs_type = fs_type
        self.device = device or fs_type

    def __str__(self):
        return self.dest

    def __hash__(self):
        return hash(self.dest)

    def is_mount(self):
        return os.path.ismount(self.dest)

    def get_cmd(self):
        cmd = ['mount']
        if self.fs_type:
            cmd += ['-t', self.fs_type]
        if self.opts:
            cmd += ['-o', self.opts]
        return cmd + [self.device, self.dest]

    def mount(self):
        def mktree(fullpath):
            dirs = fullpath.split('/')
            path = '/'
            for d in dirs:
                path = os.path.join(path, d)
                if not os.path.exists(path):
                    os.mkdir(path)
        print('mounting', self.dest)
        if not os.path.isdir(self.dest):
            mktree(self.dest)
        ret = subprocess.run(self.get_cmd())
        assert ret.returncode == 0, ret.returncode

    def unmount(self):
        if not self.is_mount:
            return
        ret = subprocess.run(['umount', self.dest])
        assert ret.returncode == 0, ret

class Chroot():
    def __init__(self, path, unbind=False):
        self.real_root = os.open('/', os.O_RDONLY)
        self.path = path
        self.unbind = unbind
        self.mounts = [
            MountPoint(f'{path}/proc', opts='nosuid,noexec,nodev', fs_type='proc'),
            MountPoint(f'{path}/dev', opts='mode=0755,nosuid', fs_type='devtmpfs'),
            MountPoint(f'{path}/dev/pts', opts='mode=1777,nosuid,nodev', fs_type='devpts'),
            MountPoint(f'{path}/dev/shm', opts='nodev,nosuid', fs_type='tmpfs'),
            MountPoint(f'{path}/run', opts='nosuid,nodev,mode=0775', fs_type='tmpfs'),
            MountPoint(f'{path}/tmp', opts='mode=1777,strictatime,nodev,nosuid', fs_type='tmpfs'),
            MountPoint(f'{path}/sys', opts='nosuid,noexec,nodev,ro', fs_type='sysfs')
        ]
        if os.path.exists('/sys/firmware/efi'):
            self.mounts.append(
                MountPoint(f'{path}/sys/firmware/efi/efivars', opts='nosuid,noexec,nodev', fs_type='efivarfs')
            )

    def start(self):
        for bind in self.mounts:
            if bind.is_mount() == False:
                bind.mount()
        os.chroot(self.path)
        os.chdir('/')

    def stop(self):
        os.chdir(self.real_root)
        os.chroot('.')
        os.close(self.real_root)
        if self.unbind:
            for bind in self.mounts:
                bind.unmount()

    def __enter__(self):
        self.start()

    def __exit__(self, a, b, c):
        self.stop()

    @staticmethod
    def decorator(path):
        def real_decorator(func):
            def wrapper(*args, **kwargs):
                with Chroot(path):
                    func(*args, **kwargs)
            return wrapper
        return real_decorator


class Service():
    packages = []
    groups = []
    service = None
    ai = None
    users = []
    enable = True
    desc = 'This service needs a description'

    def __init__(self, users=[], enable=None):
        self.users = users
        if enable != None:
            self.enable = enable

    def __hash__(self):
        return hash(self.service)

    def check(self):
        """
        """
        if not self.ai:
            raise ConfigError('you must set self.ai before using this service')

    def install(self):
        if not self.packages:
            return
        self.ai.pkg_install(self.packages)

    def add_users(self):
        """
        user must be a list of ArchUser
        """
        if not self.groups or not self.users:
            return
        for user in self.users:
            user.add_groups(self.groups)

    def set_enabled(self, state=True):
        if not self.service:
            return
        self.ai.run_in(['systemctl', ('disable', 'enable')[state], self.service])

    def start(self):
        raise ValueError('You are trying to run a service in a chroot... morron !')


class Mlocate(Service):
    packages = ['mlocate']
    desc = 'files indexer'


class Cups(Service):
    packages = [
        'extra/cups',
        'extra/cups-pdf',
        'extra/gutenprint',
        'extra/foomatic-db-gutenprint-ppds'
    ]
    service = 'org.cups.cupsd.service'
    groups = ['lp']
    desc = 'Printer server'


class NetworkManager(Service):
    packages = ['extra/networkmanager']
    service = 'NetworkManager'
    dest = 'Network interface manager / dhcp client'


class LightDm(Service):
    packages = ['extra/lightdm', 'extra/lightdm-gtk-greeter']
    service = 'lightdm.service'
    enabled = False
    desc = 'A lightweight display manager'


class Gpm(Service):
    packages = ['gpm']
    service = 'gpm.service'
    desc = 'a mouse in the the terminal mode'


class Fail2Ban(Service):
    packages = ['fail2ban']
    service = 'fail2ban.service'
    desc = 'bruteforcers nightmare'


class Smartd(Service):
    packages = ['smartmontools']
    service = 'smartd.service'
    desc = 'disks errors reporter'


class Sshd(Service):
    packages = ['openssh']
    service = 'sshd.service'
    desc = 'remote controll service'


class Docker(Service):
    packages = ['docker']
    service = 'docker.service'
    desc = 'docker containers support'


class Udisks2(Service):
    packages = ['extra/udisks2']
    service = 'udisks2.service'
    desc = 'drive managements'


class Nginx(Service):
    packages = ['nginx']
    service = ['nginx.service']
    groups = ['www-data']
    desc = 'web server'


class Acpid(Service):
    packages = ['community/acpid']
    service = 'acpid.service'
    desc = 'power management'


class Iptables(Service):
    packages = ['core/iptables']
    service = 'iptables.service'
    desc = 'firewall'


class Cd():
    """
    context manager to change dir and then goes back into the original dir.
    """
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.origin = os.getcwd()
        os.chdir(self.path)
        return (self.origin, self.path)

    def __exit__(self, a, b, c):
        os.chdir(self.origin)


class ArchUser():
    def __init__(self, ai, username):
        if not isinstance(ai, ArchInstall):
            raise ValueError(ai)
        self.username = username
        self.home = os.path.join('/home', username)
        self.ai = ai
        self.uid = None
        self.gid = None
        # this a restricted env to lie to childs process.
        self.env = {
            'HOME': self.home,
            'PWD': self.home,
            'USER': self.username,
            'LOGNAME': self.username,
            'SHELL': '/bin/zsh',
            'EDITOR': 'vim',
            'OLDPWD': '/',
            'TERM': 'linux'
        }

    def __str__(self):
        return f'ArchUser {self.username}'

    def __hash__(self):
        return hash(str(self))

    def run(self, command, **kwargs):
        assert self.exists() == True, (self.uid, self.gid)
        if not kwargs.get('cwd'):
            kwargs['cwd'] = self.home
        if not kwargs.get('env'):
            kwargs['env'] = self.env
        with Chroot(self.ai.mnt):
            with Cd(self.home):
                self.ai.run(command, capture=False, preexec_fn=self.demote, **kwargs)

    def get_defaults_groups(self):
        return ['audio', 'video', 'render', 'input', 'scanner', 'games']

    def add_groups(self, groups):
        for group in groups:
            self.ai.run_in(['gpasswd', '-a', self.username, group])

    def create(self, shell='/bin/zsh'):
        with Chroot(self.ai.mnt):
            self.ai.run(['useradd', '-m', '-s', shell, self.username])
            self.ai.run(['chown', f'{self.username}:{self.username}', self.home])
            self.ai.run(['chmod', '700', self.home])
            users = ArchUser.list()
            for u in users:
                if u['user'] == self.username:
                    me = u
                    self.gid = me['gid']
                    self.uid = me['uid']

    def delete(self, delete_home=False):
        with Chroot(self.ai.mnt):
            if delete_home:
                self.ai.run(['userdel', '-f', self.username])
            else:
                self.ai.run(['userdel', self.username])
        self.uid, self.gid = (None, None)

    def set_password(self):
        while True:
            try:
                with Chroot(self.ai.mnt):
                    self.ai.run(['passwd', self.username])
                return
            except KeyboardInterrupt:
                print(f'setup of user {self.username} skipped: no password set')
                return
            except CommandFail:
                pass

    def install_trizen(self):
        trizen_path = os.path.join(self.home, 'trizen')
        real_path = f'{self.ai.mnt}{trizen_path}'
        self.run(['id'], cwd=self.home, env=self.env)
        # remove any previous get.
        if os.path.exists(real_path):
            self.ai.run(['rm', '-rf', real_path])

        self.run(['git', 'clone', 'https://aur.archlinux.org/trizen.git', trizen_path],
            cwd=self.home)
        self.run(['pwd'], cwd=trizen_path)
        self.run(['makepkg', '-si', '--noconfirm'], cwd=trizen_path)
        self.run(['trizen', '-Sy'])
        self.run(['rm', '-rf', trizen_path])

    def install(self, packages):
        self.run(['trizen', '-S', '--noedit', '--noconfirm'] + packages)

    def install_oh_myzsh(self):
        self.run(['wget',
                 'https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh',
                 '-O', '/tmp/ohmyzsh.sh'])
        self.run(['sh', '/tmp/ohmyzsh.sh'])
        self.run(['rm', '/tmp/ohmyzsh.sh'])

    def exists(self):
        return self.uid != None and self.gid != None

    def demote(self):
        assert self.exists() == True
        print('demoting privileges to ', self.username)
        os.setgid(self.gid)
        os.setuid(self.uid)

    @staticmethod
    def list():
        users = []
        with open('/etc/passwd', 'r') as fd:
            for line in fd.readlines():
                try:
                    data = line[0:-1].split(':')
                    print(data)
                    user,_,uid,gid,desc,home, shell = data
                    users.append({
                        'user': user,
                        'uid': int(uid),
                        'gid': int(gid),
                        'desc': desc,
                        'home': home,
                        'shell': shell
                    })
                except ValueError:
                    continue
        return users

class ArchInstall():
    def __init__(self, hostname, mnt='/mnt', lang='fr_FR.UTF-8'):
        """
        hostname: the machine hostname
        mnt: on wich mount point will you install arch ? this mountpoint must exists
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
        with Chroot(self.mnt):
            if not user:
                return self.run(command, **kwargs)
            assert isinstance(user, ArchUser) == True
            return self.run(command, preexec_fn=user.demote(), **kwargs)

    def pkg_install(self, packages):
        self.run_in(['pacman', '-S', '--noconfirm'] + packages)

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

    def install(self, packages):
        if packages:
            self.run(['pacstrap', self.mnt] + packages)
        fstab = self.run(['genfstab', self.mnt], True)
        with Chroot(self.mnt):
            self.file_put('/etc/hostname', self.hostname + '\n')
            self.file_put('/etc/fstab', fstab)
            self.file_put('/etc/locale.conf', f'LC_CTYPE={self.lang}\nLANG={self.lang}')
            self.file_put('/etc/locale.gen', self.locale_genfile())
            self.file_put('/etc/resolv.conf', 'nameserver 1.1.1.1\nnameserver 1.0.0.1\n')
            self.file_put('/etc/sudoers.d/wheel', '%wheel ALL=(ALL) ALL')
            self.file_put('/etc/sudoers.d/targetpw', 'Defaults targetpw')
            commands = (
                # System has not been booted with systemd as init (PID 1). Can't operate.
                # ['timedatectl', 'set-ntp', 'true'],
                ['locale-gen'],
                ['chmod', '751', '/home'],
                ['ln', '-sf', f'/usr/share/zoneinfo/{self.timezone}', '/etc/localtime'],
                ['mkdir', '-pv', '/etc/polkit-1/rules.d/'],
                ['passwd'],
                ['mkinitcpio', '-p', 'linux'],
            )
            for cmd in commands:
                self.run(cmd)

    def install_bootloader(self, name, device, **kwargs):
        if name == 'refind':
            self.install_refind(device)
        elif name == 'grub':
            self.install_grub(device, **kwargs)
        else:
            raise ValueError(name)

    def install_grub(self, device, target='i386-pc'):
        self.pkg_install(['grub'])
        with Chroot(self.mnt):
            if not os.path.exists('/boot/grub'):
                os.mkdir('/boot/grub')
            self.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
            self.run(['grub-install', '--target', target, device])

    def install_refind(self, device):
        if not os.path.ismount(os.path.join(self.mnt, '/boot/efi')):
            raise(ConfigError('please create and mount /boot/efi (vfat)'))
        # TODO : detect informations about device and mount point of /boot/efi
        partition = 1
        efi_path = '/EFI/refind/refind_x64.efi'
        with Chroot(self.mnt):
            self.pkg_install(['extra/refind-efi'])
            self.run(['refind-install', '--alldrivers', device])
        if not os.path.exists(os.path.join('/boot/efi', efi_path)):
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

    def install_services(self, services):
        for service in services:
            if not isinstance(service, Service):
                raise ValueError(service)
            service.ai = self
            service.install()
            if service.enable:
                service.set_enabled(True)
            service.add_users()

    @staticmethod
    def get_mounts():
        lst = []
        with open('/proc/mounts','r') as fd:
            for line in fd.readlines():
                try:
                    device, mount_point, fs, opts, dump, pas = line.split()
                    lst.append({
                        'device': device,
                        'mnt': mount_point,
                        'fs': fs,
                        'opts': opts,
                        'dump': dump,
                        'pass': pas
                    })
                except ValueError:
                    pass
        return lst


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', help='the new machine hostname', default='localhost')
    parser.add_argument('--root', help='the mount point to use (/mnt)', default='/mnt')
    parser.add_argument('--device', help='wich device to use (for bootloaders)', default='/dev/sda')
    parser.add_argument('--user', help='create a default user ?', required=True)
    parser.add_argument('--loader', help='which bootloader to use ?', choices=('grub', 'refind'), required=True)
    args = parser.parse_args()

    arch = ArchInstall(hostname=args.hostname)
    user = ArchUser(arch, username=args.user)

    arch.install(DEFAULT)
    arch.install_bootloader(args.loader, args.device)

    user.create()
    user.set_password()
    user.add_groups(user.get_defaults_groups())
    user.add_groups(['wheel'])
    user.install_trizen()
    user.install(['aur/visual-studio-code-bin', 'spotify'])
    user.install_oh_myzsh()
    user.run(['/usr/bin/pip3', 'install', '--user', 'requests', 'virtualenv'])

    services = [
        NetworkManager(),
        Cups(users=[user]),
        LightDm(enable=True),
        Fail2Ban(),
        Sshd(),
        Smartd(),
        Gpm(),
        Udisks2(),
        Acpid(),
        Iptables(),
        Mlocate()
    ]
    arch.install_services(services)
