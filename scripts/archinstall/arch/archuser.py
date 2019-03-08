import os

from .archinstall import ArchInstall
from .tools import Cd, ArchChroot
from .mount import MountPoint


class ArchUser():
    def __init__(self, ai, username, home=None, uid=None, gid=None):
        if not isinstance(ai, ArchInstall):
            raise ValueError(ai)
        self.username = username
        self.home = home or os.path.join('/home', username)
        self.ai = ai
        self.uid = uid
        self.gid = gid
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
        assert self.exists(), (self.uid, self.gid)
        if not kwargs.get('cwd'):
            kwargs['cwd'] = self.home
        if not kwargs.get('env'):
            kwargs['env'] = self.env
        with ArchChroot(self.ai.mnt):
            with Cd(self.home):
                self.ai.run(command, capture=False, preexec_fn=self.demote, **kwargs)

    def get_defaults_groups(self):
        return ['audio', 'video', 'render', 'input', 'scanner', 'games']

    def add_groups(self, groups):
        for group in groups:
            self.ai.run_in(['gpasswd', '-a', self.username, group])

    def create(self, shell='/bin/zsh'):
        with ArchChroot(self.ai.mnt):
            self.ai.run(['useradd', '-d', self.home, '-m', '-s', shell, self.username])
            self.ai.run(['chown', f'{self.username}:{self.username}', self.home])
            self.ai.run(['chmod', '700', self.home])
            users = ArchUser.list()
            for u in users:
                if u['user'] == self.username:
                    me = u
                    self.gid = me['gid']
                    self.uid = me['uid']

    def delete(self, delete_home=False):
        with ArchChroot(self.ai.mnt):
            if delete_home:
                self.ai.run(['userdel', '-f', self.username])
            else:
                self.ai.run(['userdel', self.username])
        self.uid, self.gid = (None, None)

    def passwd(self):
        while True:
            try:
                print('password for', self.username)
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

        self.run(
            [
                'git', 'clone', 'https://aur.archlinux.org/trizen.git', trizen_path
            ],
            cwd=self.home)
        self.run(['pwd'], cwd=trizen_path)
        self.run(['makepkg', '-si', '--noconfirm'], cwd=trizen_path)
        self.run(['trizen', '-Sy'])
        self.run(['rm', '-rf', trizen_path])

    def install(self, packages):
        self.run(['trizen', '-S', '--noedit', '--noconfirm'] + packages)

    def install_oh_myzsh(self):
        self.run(
            ['wget',
            'https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh',
            '-O', '/tmp/ohmyzsh.sh'])
        self.run(['sh', '/tmp/ohmyzsh.sh'])
        self.run(['rm', '/tmp/ohmyzsh.sh'])

    def exists(self):
        return self.uid is not None and self.gid is not None

    def demote(self):
        assert self.exists()
        os.setgid(self.gid)
        os.setuid(self.uid)

    @staticmethod
    def list():
        users = []
        with open('/etc/passwd', 'r') as fd:
            for line in fd.readlines():
                try:
                    data = line[0:-1].split(':')
                    user, _, uid, gid, desc, home, shell = data
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

    @staticmethod
    def from_disk(login, ai):
        assert isinstance(login, str)
        assert isinstance(ai, ArchInstall)
        for account in ArchUser.list():
            if account['user'] == login:
                user = ArchUser(login, ai)
                user.gid = account['gid']
                user.uid = account['uid']
                user.home = account['home']
                return user
        raise ValueError(login)
