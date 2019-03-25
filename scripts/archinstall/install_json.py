#!/usr/bin/python3
from arch import ArchInstall, ArchUser
from arch.tools import Chroot
from arch.services import *
from arch.metapkg import *

import json
import sys
import os


def copy_form_host(arch, copy):
	assert isinstance(copy, dict)
	assert copy.get('src') is not None
	assert copy.get('dst') is not None
	assert os.path.exists(copy['src'])
	real_dst = arch.mnt + copy['dst']
	arch.run(['cp', '-vr', copy['src'], real_dst])

	with Chroot(arch.mnt):
		if copy.get('perms'):
			arch.run_in(['chmod', copy['perms'], copy['dst']])
		if copy.get('user'):
			arch.run_in(['chown', '-R', f'{user.username}:{user.username}', copy['dst']])


def handle_users(arch, users):
    # creating and configuring users
    for cfg_user in users:
        user = ArchUser(arch,
                        username=cfg_user['login'],
                        home=cfg_user.get('home'))
        if user.username != 'adamaru':
            user.create(shell=cfg_user['shell'])
            user.add_groups(cfg_user['groups'])
        else:
            user.uid, user.gid = (1000, 1000)
        if cfg_user.get('trizen'):
            user.install_trizen()
        if cfg_user.get('ohmyzsh'):
            user.install_oh_myzsh()
        if cfg_user.get('aur'):
            user.install(cfg_user['aur'])
        for command in cfg_user.get('commands', []):
            if isinstance(command, list):
                user.run(command)
            elif isinstance(command, dict):
                env = command.get('env')
                cwd = command.get('cwd')
                command = command['cmd']
                user.run(command, env=env, cwd=cwd)
            else:
                raise TypeError(command)
        user.passwd()


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
        'KDE': KDE,
        'AUDIO': AUDIO,
        'FONTS': FONTS,
        'DEV': DEV
    }
    packages = []
    for meta in config.get('meta', []):
        packages.extend(metas[meta])
    servers = config.get('pacman', {}).get('servers')

    arch = ArchInstall(hostname=config['hostname'], mnt=config.get('mnt', '/mnt'))
    if config.get('dns'):
        arch.dns = config['dns']
    services = ServicesManager(arch, *[srv() for srv in services_to_install])
    #arch.install(
    #    packages + services.collect_packages() + config.get('packages', []),
    #    custom_servers=servers)
    #services.install()

    handle_users(arch, config.get('users', []))

    # configuring sudo
    sudo = config.get('sudo', {'present': True, 'targetpw': True, 'nopasswd': False})
    if not sudo['present']:
        arch.run(['pacman', '-Rns', '--noconfirm', 'core/sudo'])
    if not sudo['targetpw']:
        arch.run(['rm', '-f', '/etc/sudoers.d/targetpw'])
    arch.set_sudo_free(sudo['nopasswd'])

	# bootloader installation, it is perfectly okay to don't install one with the script.
    if config.get('loader'):
        efi = config['loader'].get('efi')
        device = config['loader'].get('device')
        arch.install_bootloader(config['loader']['name'],
                                efi_path=efi,
                                device=device)

	# copy ressources from host guest system
    for copy in config.get('config', []):
        copy_form_host(arch, copy)
    arch.passwd()


if __name__ == "__main__":
    assert os.getuid() == 0 and os.getgid() == 0, "You need to run this script as root"
    install_from_json(sys.argv[1])
