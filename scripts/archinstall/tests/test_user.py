import pytest

from mock import patch
import sys, os;
sys.path.insert(0, os.getcwd())

from fakeai import *
from arch import ArchUser, ArchInstall
from arch.mount import MountPoint

REAL_USER = os.getenv('USER')


@pytest.fixture
def user():
    return ArchUser(FakeAi(hostname='Nope', mnt='/'), username=REAL_USER, uid=1000, gid=1000)


@patch('os.chroot', side_effect=fake_chroot)
@patch('os.mkdir', side_effect=fake_mkdir)
def test_user_trizen(fmk, fc, fakearch):
    user = ArchUser(fakearch, username=REAL_USER, gid=1000, uid=1000)
    user.install_trizen()


@patch('os.chroot', side_effect=fake_chroot)
@patch('arch.mount.MountPoint', callable=FakeMount)
def test_user_install(fm, fc, fakearch):
    user = ArchUser(fakearch, username=REAL_USER, gid=1000, uid=1000)
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


def test_user_list():
    for user in ArchUser.list():
        assert user.get('user')
        assert user.get('uid') is not None
        assert user.get('gid') is not None
        assert user.get('shell')
        assert user.get('home')


def test_user_attributes(user):
    assert user.username == REAL_USER
    assert user.uid == 1000
    assert user.gid == 1000
    assert user.home == '/home/' + REAL_USER
