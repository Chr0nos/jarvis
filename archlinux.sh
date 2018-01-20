TARGET=/mnt
NAME=archlinux
VIDEO=extra/nvidia-dkms extra/nvidia-settings
#VIDEO=extra/xf86-video-intel
DEVELOPPER=python python-pip git clang make tig geany

pacstrap $TARGET base base-devel grub xorg-server $VIDEO $DEVELOPPER networkmanager htop vim net-tools pulseaudio lightdm lightdm-gtk-greeter libreoffice libreoffice-fr mpv vlc chromium gpm zsh terminator fish openssh openssl networkmanager-openvpn network-manager-applet mate mate-extra ttf-liberation ttf-ubuntu-font-family xorg-fonts-75dpi xorg-fonts-100dpi ttf-dejavu ttf-freefont otf-font-awesome gnome-keyring smartmontools hdparm idle3-tools iw
echo $NAME >> $TARGET/etc/hostname
arch-chroot $TARGET systemctl enable NetworkManager
arch-chroot $TARGET systemctl enable lightdm
arch-chroot $TARGET systemctl enable gpm
arch-chroot $TARGET locale-gen
arch-chroot $TARGET grub-mkconfig -o /boot/grub/grub.cfg
arch-chroot $TARGET mkinitcpio -p linux -g /boot/initramfs-linux.img
arch-chroot $TARGET passwd
