import os

from .runner import CommandRunner, CommandFail
from .tools import Cd, ArchChroot, Chroot, Groups


class ArchUser():
    def __init__(self, runner: CommandRunner, username, home=None, uid=None, gid=None):
        if not isinstance(runner, CommandRunner):
            raise ValueError(runner)
        self.username = username
        self.home = home or os.path.join('/home', username)
        self.runner = runner
        self.uid = uid
        self.gid = gid

        with Chroot(self.runner.mnt):
            self.groups = Groups().parse().user_groups(username)
            print(self.groups)
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
        with ArchChroot(self.runner.mnt):
            with Cd(self.home):
                self.runner.run(command, capture=False, preexec_fn=self.demote, **kwargs)

    def run_many(self, commands, **kwargs):
        assert self.exists(), (self.uid, self.gid)
        if not kwargs.get('cwd'):
            kwargs['cwd'] = self.home
        if not kwargs.get('env'):
            kwargs['env'] = self.env
        with ArchChroot(self.runner.mnt):
            with Cd(self.home):
                for cmd in commands:
                    self.runner.run(cmd, preexec_fn=self.demote, **kwargs)

    @staticmethod
    def get_defaults_groups():
        return ['audio', 'video', 'render', 'input', 'scanner', 'games']

    def add_groups(self, groups):
        for group in groups:
            self.runner.run_in(['gpasswd', '-a', self.username, group])
        self.groups = Groups().parse().user_groups(self.username)

    def create(self, shell='/bin/zsh'):
        with ArchChroot(self.runner.mnt):
            self.runner.run(['useradd', '-d', self.home, '-m', '-s', shell, self.username])
            self.runner.run(['chown', f'{self.username}:{self.username}', self.home])
            self.runner.run(['chmod', '700', self.home])
            users = ArchUser.list()
            for u in users:
                if u['user'] == self.username:
                    me = u
                    self.gid = me['gid']
                    self.uid = me['uid']

    def delete(self, delete_home=False):
        with ArchChroot(self.runner.mnt):
            if delete_home:
                self.runner.run(['userdel', '-f', self.username])
            else:
                self.runner.run(['userdel', self.username])
        self.uid, self.gid = (None, None)

    def passwd(self):
        while True:
            try:
                print('password for', self.username)
                with Chroot(self.runner.mnt):
                    self.runner.run(['passwd', self.username])
                return
            except KeyboardInterrupt:
                print(f'setup of user {self.username} skipped: no password set')
                return
            except CommandFail:
                pass

    def install_trizen(self):
        trizen_path = os.path.join(self.home, 'trizen')
        real_path = f'{self.runner.mnt}{trizen_path}'
        self.run(['id'], cwd=self.home, env=self.env)
        # remove any previous get.
        if os.path.exists(real_path):
            self.runner.run(['rm', '-rf', real_path])

        self.run(['git', 'clone', 'https://aur.archlinux.org/trizen.git'], cwd=self.home)
        self.run(['makepkg', '-sic', '--noconfirm'], cwd=trizen_path)
        self.run(['ls', '-la', trizen_path])
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
        if self.groups:
            os.setgroups(self.groups)
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
    def from_disk(login, runner: CommandRunner):
        assert isinstance(login, str)
        assert isinstance(runner, CommandRunner)
        for account in ArchUser.list():
            if account['user'] == login:
                user = ArchUser(login, runner)
                user.gid = account['gid']
                user.uid = account['uid']
                user.home = account['home']
                return user
        raise ValueError(login)
