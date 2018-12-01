#!/bin/sh
TARGET="/mnt"
NAME="archlinux"
DEVICE=/dev/sda
USER=someone

#BOOT=grub
BOOT=refind-efi

#DESKTOP="extra/plasma-meta"
DESKTOP="mate mate-extra"
#DESKTOP="xfce4"
#DESKTOP="community/i3-wm"
#DESKTOP="community/i3-gaps community/i3status i3blocks i3lock"
#DESKTOP="community/cinnamon"
#DESKTOP="gnome"
#DESKTOP="weston"
#DESKTOP="openbox"

VIDEO="extra/nvidia-dkms extra/nvidia-settings"
#VIDEO="extra/xf86-video-intel"
#VIDEO="extra/xf86-video-vesa"
#VIDEO="extra/xf86-video-amdgpu"
#VIDEO="extra/xf86-video-ati"
#VIDEO="extra/xf86-video-vmware"
#VIDEO="virtualbox-guest-modules-arch virtualbox-guest-utils"

BROWSER="firefox extra/firefox-i18n-fr community/firefox-adblock-plus"
#BROWSER="chromium"

FIRMWARE="intel-ucode"
DEVELOPPER="python python-pip git clang make tig gdb peda"
EXTRA="extra/adwaita-icon-theme linux-headers"
XORG="xorg-server xorg-fonts-75dpi xorg-fonts-100dpi xorg-xrandr xorg-xinit"
WAYLAND="wayland"

echo "I will install arch linux on ${TARGET}"
echo "hostname: ${NAME}"
echo "desktop environement: ${DESKTOP}"
echo "browser: ${BROWSER}"
echo "extra: ${EXTRA}"
read -p "Press enter to continue or ctrl+c to abort."

pacstrap $TARGET base base-devel ${FIRMWARE} ${BOOT}  ${VIDEO} \
	${DEVELOPPER} networkmanager htop vim net-tools pulseaudio lightdm \
	lightdm-gtk-greeter mpv gpm zsh terminator fish openssh openssl \
	networkmanager-openvpn network-manager-applet ttf-liberation \
	ttf-ubuntu-font-family ttf-dejavu \
	ttf-freefont otf-font-awesome gnome-keyring smartmontools hdparm \
	idle3-tools iw fail2ban pavucontrol gparted ntfs-3g exfat-utils \
	sshfs ffmpegthumbnailer ${BROWSER} ${EXTRA} ${XORG}

# check for installation success
if [ $? == 0 ]; then
	echo $NAME >> $TARGET/etc/hostname
	sed -i "s\# Defaults targetpw\Defaults targetpw\g" $TARGET/etc/sudoers
	sed -i "s\# %wheel ALL=(ALL) ALL\%wheel ALL=(ALL) ALL" $TARGET/etc/sudoers
	arch-chroot $TARGET systemctl enable NetworkManager
	# arch-chroot $TARGET systemctl enable lightdm
	arch-chroot $TARGET systemctl enable gpm
	arch-chroot $TARGET systemctl enable fail2ban
	arch-chroot $TARGET systemctl enable smartd
	arch-chroot $TARGET locale-gen
	if [ $BOOT == "grub" ]; then
		arch-chroot ${TARGET} grub-mkconfig -o /boot/grub/grub.cfg
	else
		arch-chroot ${TARGET} refind-install --alldrivers ${DEVICE}
	fi
	arch-chroot $TARGET mkinitcpio -p linux -g /boot/initramfs-linux.img
	# note this needs base-devel and git
	arch-chroot $TARGET useradd -m -s /bin/zsh $USER
	chmod 751 $TARGET/home
	chmod 700 $TARGET/home/$USER
	arch-chroot $TARGET ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime
	arch-chroot $TARGET mkdir -pv /etc/polkit-1/rules.d/
	arch-chroot $TARGET passwd
	arch-chroot $TARGET su $USER -c "git clone https://aur.archlinux.org/trizen.git /home/$USER/trizen"
	arch-chroot $TARGET su $USER -c "cd /home/$USER/trizen && makepkg -si"
	arch-chroot $TARGET su $USER -c "trizen -Sy --noedit --noconfirm visual-studio-code-bin"

else
	echo "failed to install base packages."
fi

