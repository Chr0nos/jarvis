import subprocess

class ServicesManager(list):
    def __init__(self, ai, *args):
        super().__init__(args)
        self.ai = ai

    def collect_packages(self):
        pkgs = []
        for service in self:
            if not service.packages:
                continue
            pkgs += service.packages
        # remove any duplicate entries
        return list(set(pkgs))

    def install(self):
        for service in self:
            service.ai = self.ai
            if service.enable:
                service.set_enabled(True)

    def add_users(self):
        for service in self:
            service.add_users()


class Service():
    name = None
    packages = []
    groups = []
    service = None
    ai = None
    users = []
    enable = True
    desc = 'This service needs a description'

    def __init__(self, users=[], enable=None):
        self.users = users
        if enable is not None:
            self.enable = enable

    def __hash__(self):
        return hash(self.name)

    def check(self):
        """
        """
        if not self.ai:
            raise ConfigError('you must set self.ai before using this service')

    def install(self):
        if not self.packages:
            return
        self.check()
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
        if not state or not self.service:
            return
        self.check()
        self.ai.run_in(['systemctl', ('disable', 'enable')[state], self.service])

    def start(self):
        raise ValueError('You are trying to run a service in a chroot... morron !')


class Xorg(Service):
    name = 'xorg'
    packages = [
        'xorg-server',
        'xorg-fonts-75dpi',
        'xorg-fonts-100dpi',
        'xorg-xrandr',
        'xorg-xinit',
    ]
    groups = ['video']
    desc = 'Graphic interface server (Xorg)'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.packages.extend(Xorg.get_driver_packages())

    @staticmethod
    def get_driver_packages():
        # 'xf86-video-nouveau',
        # 'extra/nvidia-dkms', 'extra/nvidia-settings',
        # 'extra/xf86-video-vesa',
        # 'extra/xf86-video-intel',
        # 'extra/xf86-video-ati',
        # 'extra/xf86-video-amdgpu',
        # 'extra/xf86-video-vmware',

        raw = subprocess.run(['lspci'], stdout=subprocess.PIPE)
        out = raw.stdout.decode('utf-8')
        for line in out.split('\n'):
            if 'VGA' not in line:
                continue
            if 'NVIDIA' in line:
                return ['nvidia-dkms', 'extra/nvidia-settings']
            if 'INTEL' in line:
                return ['extra/xf86-video-intel']
            if 'VMware' in line:
                return ['extra/xf86-video-vmware', 'xf86-input-vmmouse']
            return ['extra/xf86-video-vesa']


class Mlocate(Service):
    name = 'mlocate'
    packages = ['mlocate']
    desc = 'files indexer'


class Cups(Service):
    name = 'cups'
    packages = [
        'extra/cups',
        'extra/cups-pdf',
        'extra/gutenprint',
        'extra/foomatic-db-gutenprint-ppds',
        'system-config-printer'
    ]
    service = 'org.cups.cupsd.service'
    groups = ['lp']
    desc = 'Printer server'


class NetworkManager(Service):
    name = 'networkmanager'
    packages = [
        'extra/networkmanager',
        'networkmanager-openvpn',
        'network-manager-applet',
        'extra/nm-connection-editor'
    ]
    service = 'NetworkManager'
    dest = 'Network interface manager / dhcp client'


class LightDm(Service):
    name = 'lightdm'
    packages = ['extra/lightdm', 'extra/lightdm-gtk-greeter']
    service = 'lightdm.service'
    enabled = False
    desc = 'A lightweight display manager'


class Gpm(Service):
    name = 'gpm'
    packages = ['gpm']
    service = 'gpm.service'
    desc = 'a mouse in the the terminal mode'


class Fail2Ban(Service):
    name = 'fail2ban'
    packages = ['fail2ban']
    service = 'fail2ban.service'
    desc = 'bruteforcers nightmare'


class Smartd(Service):
    name = 'smartd'
    packages = ['smartmontools']
    service = 'smartd.service'
    desc = 'disks errors reporter'


class Sshd(Service):
    name = 'sshd'
    packages = ['openssh']
    service = 'sshd.service'
    desc = 'remote controll service'


class Docker(Service):
    name = 'docker'
    packages = ['docker']
    service = 'docker.service'
    desc = 'docker containers support'


class Udisks2(Service):
    name = 'udisks2'
    packages = ['extra/udisks2']
    service = 'udisks2.service'
    desc = 'drive managements'


class Nginx(Service):
    name = 'nginx'
    packages = ['nginx']
    service = 'nginx.service'
    groups = ['www-data']
    desc = 'web server'


class Acpid(Service):
    name = 'acpid'
    packages = ['community/acpid']
    service = 'acpid.service'
    desc = 'power management'


class Iptables(Service):
    name = 'iptables'
    packages = ['core/iptables']
    service = 'iptables.service'
    desc = 'firewall'


class BlueTooth(Service):
    name = 'bluetooth'
    packages = [
        'extra/bluez',
        'extra/bluez-utils',
        'extra/pulseaudio-bluetooth'
    ]
    service = 'bluetooth.service'
    desc = 'bluetooth support'

class MariaDB(Service):
    name = 'mariadb'
    packages = ['extra/mariadb']
    service = 'mariadb.service'
    # Need to be initialised with :
    # mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
    # before been launched, could be done with args for the service
    enable = False
    desc = 'mysql database'

class Redis(Service):
    name = 'redis'
    packages = ['community/redis']
    service = 'redis.service'
    desc = 'cache/key-value database'
