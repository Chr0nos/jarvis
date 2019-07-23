import os, sys
sys.path.insert(0, os.getcwd())

from mock import patch

from arch import ArchInstall, CommandRunner
from arch.mount import MountPoint
from pytest import fixture


class FakeAi(ArchInstall):
    def run(self, command, **kwargs):
        print('[out]', command)

    def run_in(self, command, user=None, **kwargs):
        print('[in]', command)

    def file_put(self, filepath, content):
        print(filepath, '->', content)

    def passwd(self):
        print('setting password for root')


class FakeMount(MountPoint):
    def mount(self):
        print('mount', self.dest)

    def unmount(self):
        print('unmount')


class FakeRunner(CommandRunner):
    def run(self, command, return_value=None, **kwargs):
        print('running ' + ' '.join(command) + '(' + kwargs + ')')
        return force_return


@fixture
@patch('arch.mount.MountPoint', callable=FakeMount)
def fakearch(_):
    return FakeAi(hostname='fakeai', mnt='/')

@fixture
def fakerunner():
    return FakeRunner('/')

def fake_chroot(path):
    print('chroot', path)


def fake_mkdir(path):
    print('mkdir', path)
