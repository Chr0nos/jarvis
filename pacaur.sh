#!/bin/sh

if [ "$(whoami)" == 'root' ]; then
	echo do not run this script as root !
	exit 1
fi

if [ ! -x /usr/bin/sudo ]; then
	echo Error: unable to find sudo !
	exit 2
fi

# catch any signal for quit (exemple: missing sudo password...)
trap "exit" SIGINT SIGTERM

# directories structure
mkdir -p /tmp/pacaur
cd /tmp/pacaur
mkdir cower
mkdir pacaur

# dedependecies install part
sudo pacman -Sy
sudo pacman -S curl binutils make gcc fakeroot expac yajl git --noconfirm

# cower install part
cd /tmp/pacaur/cower
curl -o PKGBUILD 'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=cower'
makepkg PKGBUILD --skippgpcheck
sudo pacman -U cower*.tar.xz --noconfirm

# pacaur install part
cd /tmp/pacaur/pacaur
curl -o PKGBUILD 'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=pacaur'
makepkg PKGBUILD
sudo pacman -U pacaur*.tar.xz --noconfirm

# cleans
cd ~
rm -rf /tmp/pacaur
