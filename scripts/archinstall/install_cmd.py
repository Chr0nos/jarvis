#!/usr/bin/python3
from arch import ArchInstall, ArchUser
from arch.services import *

import argparse

# Note to Chr0nos on futur improvement: the arch package could use some asyncio feature 
# to be easier to read and use.

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', help='the new machine hostname', default='localhost')
    parser.add_argument('--root', help='the mount point to use (/mnt)', default='/mnt')
    parser.add_argument('--device', help='wich device to use (for bootloaders)', default='/dev/sda')
    parser.add_argument('--user', help='create a default user ?', required=True)
    parser.add_argument('--loader', help='which bootloader to use ?', choices=('grub', 'grub-efi', 'refind'), required=True)
    args = parser.parse_args()

    arch = ArchInstall(hostname=args.hostname)
    user = ArchUser(arch, username=args.user)
    services = ServicesManager(arch,
        Xorg(),
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
        Mlocate(),
        Docker(users=[user]),
        BlueTooth(),
    )

    arch.install(DEFAULT + services.collect_packages())
    arch.install_bootloader(args.loader, args.device)
    services.install()

    user.create()
    user.add_groups(user.get_defaults_groups())
    user.add_groups(['wheel'])
    user.install_trizen()
    user.install(['aur/visual-studio-code-bin', 'spotify'])
    user.install_oh_myzsh()
    user.run(['/usr/bin/pip3', 'install', '--user', 'requests', 'virtualenv'])

    services.add_users()

    arch.passwd()
    user.passwd()
    arch.set_sudo_free(False)
