#!/usr/bin/python3
from arch import ArchInstall, ArchUser
from arch.services import *
from arch.metapkg import *

import json
import sys


def install_from_json(json_path):
    with open(json_path, 'r') as json_fd:
        config = json.load(json_fd)

    services = [
        Xorg, NetworkManager, Cups, LightDm, Fail2Ban, Sshd, Smartd, Udisks2,
        Gpm, Udisks2, Acpid, Iptables, Mlocate, Docker, BlueTooth, Nginx
    ]
    services_to_install = []
    for service in services:
        if service.name in config['services']:
            services_to_install.append(service)

    metas = {
        'MATE': MATE,
        'PYTHON': PYTHON,
        'EXTRA': EXTRA,
        'BASE': BASE,
        'GNOME': GNOME,
        'XFCE': XFCE,
        'I3': I3,
        'CINNAMON': CINNAMON,
        'KDE': KDE
    }
    packages = []
    for meta in config['meta']:
        packages.extend(metas[meta])

    arch = ArchInstall(hostname=config['hostname'])
    services = ServicesManager(arch, *[srv() for srv in services_to_install])
    arch.install(
        packages + services.collect_packages() + config.get('packages', []))
    services.install()

    # creating and configuring users
    for cfg_user in config['users']:
        user = ArchUser(arch,
                        username=cfg_user['login'],
                        home=cfg_user.get('home'))
        user.create(shell=cfg_user['shell'])
        user.add_groups(cfg_user['groups'])
        if cfg_user['trizen']:
            user.install_trizen()
        if cfg_user['ohmyzsh']:
            user.install_oh_myzsh()
        if cfg_user['aur']:
            user.install(cfg_user['aur'])
        user.passwd()

    # configuring sudo
    if not config['sudo']['present']:
        arch.run(['pacman', '-Rns', '--noconfirm', 'core/sudo'])
    if not config['sudo']['targetpw']:
        arch.run(['rm', '-f', '/etc/sudoers.d/targetpw'])
    arch.set_sudo_free(config['sudo']['nopasswd'])

    efi = config['loader'].get('efi')
    device = config['loader'].get('device')
    arch.install_bootloader(cfg_user['loader']['name'],
                            efi_path=efi,
                            device=device)
    arch.passwd()


if __name__ == "__main__":
    install_from_json(sys.argv[1])
