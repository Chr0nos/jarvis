import os, sys
sys.path.insert(0, os.getcwd())

from arch import ArchInstall
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


@fixture
def fakearch():
    return FakeAi(hostname='fakeai')
