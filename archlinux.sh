TARGET=/mnt
NAME=archlinux
VIDEO=extra/nvidia-dkms extra/nvidia-settings
#VIDEO=extra/xf86-video-intel
DEVELOPPER=python python-pip git clang make tig geany
PASSWD=

pacstrap $TARGET base base-devel xorg-server $VIDEO $DEVELOPPER networkmanager htop vim net-tools pulseaudio lightdm lightdm-gtk-greeter libreoffice libreoffice-fr mpv vlc chromium gpm zsh terminator fish openssh openssl networkmanager-openvpn network-manager-applet mate mate-extra
echo $NAME >> $TARGET/etc/hostname
arch-chroot $TARGET systemctl enable NetworkManager
arch-chroot $TARGET systemctl enable lightdm
arch-chroot $TARGET systemctl enable gpm
arch-chroot $TARGET passwd $PASSWD
arch-chroot $TARGET locale-gen
