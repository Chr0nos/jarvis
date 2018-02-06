TARGET="/home/adamaru/jours/jarvis/test/"
#TARGET="/mnt"
NAME="archlinux"
#DESKTOP="extra/plasma-meta"
DESKTOP="mate mate-extra"
#DESKTOP="xfce4"
VIDEO="extra/nvidia-dkms extra/nvidia-settings"
#VIDEO="extra/xf86-video-intel"
DEVELOPPER="python python-pip git clang make tig geany"
EXTRA=

echo "I will install arch linux on ${TARGET}"
echo "hostname: ${NAME}"
echo "desktop environement: ${DESKTOP}"
echo "extra: ${EXTRA}"
read -p "Press enter to continue or ctrl+c to abort."
pacstrap $TARGET base base-devel intel-ucode grub xorg-server $VIDEO $DEVELOPPER networkmanager htop vim net-tools pulseaudio lightdm lightdm-gtk-greeter libreoffice libreoffice-fr mpv vlc chromium gpm zsh terminator fish openssh openssl networkmanager-openvpn network-manager-applet ttf-liberation ttf-ubuntu-font-family xorg-fonts-75dpi xorg-fonts-100dpi ttf-dejavu ttf-freefont otf-font-awesome gnome-keyring smartmontools hdparm idle3-tools iw fail2ban pavucontrol gparted ntfs-3g exfat-utils xorg-xrandr xorg-xinit sshfs ffmpegthumbnailer $EXTRA
echo $NAME >> $TARGET/etc/hostname
sed -i "s\# Defaults targetpw\Defaults targetpw\g" $TARGET/etc/sudoers
sed -i "s\# %wheel ALL=(ALL) ALL\%wheel ALL=(ALL) ALL" $TARGET/etc/sudoers
arch-chroot $TARGET systemctl enable NetworkManager
arch-chroot $TARGET systemctl enable lightdm
arch-chroot $TARGET systemctl enable gpm
arch-chroot $TARGET systemctl enable fail2ban
arch-chroot $TARGET systemctl enable smartd
arch-chroot $TARGET locale-gen
arch-chroot $TARGET grub-mkconfig -o /boot/grub/grub.cfg
arch-chroot $TARGET mkinitcpio -p linux -g /boot/initramfs-linux.img
arch-chroot $TARGET passwd
