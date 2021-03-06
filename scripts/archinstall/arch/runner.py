import os
import subprocess

from .tools import ArchChroot
from .exceptions import CommandFail


class CommandRunner():
    def __init__(self, mnt):
        if not os.path.exists(mnt):
            raise ValueError('invalid mount point you morron: ' + mnt)
        self.mnt = mnt
        self.efi_capable = os.path.exists('/sys/firmware/efi')

    def run(self, command, capture=False, critical=True, **kwargs):
        if kwargs.get('debug_run'):
            del(kwargs['debug_run'])
            print('running', ' '.join(command), kwargs)
        if capture:
            return subprocess.check_output(command, **kwargs).decode('utf-8')
        return subprocess.run(command, **kwargs, check=critical)

    def run_in(self, command, user=None, **kwargs):
        with ArchChroot(self.mnt):
            if not user:
                return self.run(command, **kwargs)
            return self.run(command, preexec_fn=user.demote(), **kwargs)

    def edit(self, filepath):
        self.run_in(['vim', filepath])
