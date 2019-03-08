import pytest

from mock import patch
import sys, os;
sys.path.insert(0, os.getcwd())

from arch import ArchUser, ArchInstall

REAL_USER = os.getenv('USER')

@pytest.fixture
def user():
    return ArchUser(FakeAi(hostname='Nope'), username=REAL_USER, uid=1000, gid=1000)


class FakeAi(ArchInstall):
    def run(self, command, **kwargs):
        print('[out]', command)

    def run_in(self, command, user=None, **kwargs):
        print('[in]', command)

    def file_put(self, filepath, content):
        print(filepath, '->', content)

    def passwd(self):
        print('setting password for root')


def fake_chroot(path):
    print('chroot', path)


@patch('os.chroot', side_effect=fake_chroot)
def test_user_trizen(fc):
    arch = FakeAi(hostname='localhost')
    user = ArchUser(arch, username=REAL_USER, gid=1000, uid=1000)
    user.install_trizen()


@patch('os.chroot', side_effect=fake_chroot)
def test_user_install(fc):
    arch = FakeAi(hostname='localhost')
    user = ArchUser(arch, username=REAL_USER, gid=1000, uid=1000)
    user.run(['ls'])


def test_user_groups(user):
    user.get_defaults_groups()


def test_user_exists(user):
    assert user.exists()


@patch('os.chroot', side_effect=fake_chroot)
def test_user_delete(fh, user):
    user.delete(delete_home=False)
    user.delete(delete_home=True)


def test_user_demote(user):
    user.demote()


@patch('os.chroot', side_effect=fake_chroot)
def test_create(_, user):
    user.create()


def test_add_groups(user):
    user.add_groups([])
    user.add_groups(['lp', 'docker', 'audio', 'video', 'render'])


@patch('os.chroot', side_effect=fake_chroot)
def test_user_run(_, user):
    user.run(['ls'])
    user.run(['ls', '-la'])
    user.run(['id'])
    user.run(['ls'], env={}, cwd='/tmp')


def test_user_list():
    for user in ArchUser.list():
        assert user.get('user')
        assert user.get('uid') is not None
        assert user.get('gid') is not None
        assert user.get('shell')
        assert user.get('home')
