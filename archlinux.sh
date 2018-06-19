TARGET="/mnt"
NAME="archlinux"

#DESKTOP="extra/plasma-meta"
DESKTOP="mate mate-extra"
#DESKTOP="xfce4"
#DESKTOP="community/i3-wm"
#DESTKOP="community/i3-gaps"
#DESTKOP="plasma-meta"
#DESKTOP="gnome"

VIDEO="extra/nvidia-dkms extra/nvidia-settings"
#VIDEO="extra/xf86-video-intel"
#VIDEO="extra/xf86-video-vesa"
#VIDEO="extra/xf86-video-amdgpu"
#VIDEO="extra/xf86-video-ati"
#VIDEO="extra/xf86-video-vmware"

BROWSER="firefox extra/firefox-i18n-fr community/firefox-adblock-plus"
#BROWSER="chromium"

FIRMWARE="intel-ucode"
DEVELOPPER="python python-pip git clang make tig geany rustup"
EXTRA="libreoffice libreoffice-fr vlc extra/adwaita-icon-theme"

echo "I will install arch linux on ${TARGET}"
echo "hostname: ${NAME}"
echo "desktop environement: ${DESKTOP}"
echo "browser: ${BROWSER}"
echo "extra: ${EXTRA}"
read -p "Press enter to continue or ctrl+c to abort."

pacstrap $TARGET base base-devel $FIRMWARE grub xorg-server $VIDEO $DEVELOPPER networkmanager htop vim net-tools pulseaudio lightdm lightdm-gtk-greeter mpv gpm zsh terminator fish openssh openssl networkmanager-openvpn network-manager-applet ttf-liberation ttf-ubuntu-font-family xorg-fonts-75dpi xorg-fonts-100dpi ttf-dejavu ttf-freefont otf-font-awesome gnome-keyring smartmontools hdparm idle3-tools iw fail2ban pavucontrol gparted ntfs-3g exfat-utils xorg-xrandr xorg-xinit sshfs ffmpegthumbnailer $BROWSER $EXTRA
# check for installation success
if [ $? == 0 ]; then
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
else
	echo "failed to install base packages."
fi

