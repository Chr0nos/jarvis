TARGET="/mnt"
NAME="archlinux"
DEVICE=/dev/sda
USER=someone

#DESKTOP="extra/plasma-meta"
DESKTOP="mate mate-extra"
#DESKTOP="xfce4"
#DESKTOP="community/i3-wm"
#DESTKOP="community/i3-gaps"
#DESTKOP="community/cinnamon"
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
DEVELOPPER="python python-pip git clang make tig geany gdp peda"
EXTRA="libreoffice libreoffice-fr vlc extra/adwaita-icon-theme linux-headers"

echo "I will install arch linux on ${TARGET}"
echo "hostname: ${NAME}"
echo "desktop environement: ${DESKTOP}"
echo "browser: ${BROWSER}"
echo "extra: ${EXTRA}"
read -p "Press enter to continue or ctrl+c to abort."

# this function does the folowing partitions sheme:
# mount point	size		flags
# /boot			100M		boot
# /				30Gb
# swap			4Gb
# /home			all remaining space of the drive
function create_partitions() {
	parted --script ${DEVICE} \
		mklabel dos \
		mkpart primary 1MiB 100MiB \
		mkpart primary 100MiB 4100Mib \
		mkpart primary 4100MiB 34GiB \
		mkpart primary 34GiB \
		set 1 boot on
	mkfs.ext4 -L Boot ${DEVICE}1
	mkfs.ext4 -L Arch ${DEVICE}2
	mkswap ${DEVICE}3
	mkfs.ext4 -L Home ${DEVICE}4
}

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
	# note this needs base-devel and git
	arch-chroot $TARGET useradd -m -s /bin/zsh $USER
	chmod 700 $TARGET/home/$USER
	arch-chroot $TARGET su $USER -c git clone https://aur.archlinux.org/trizen.git /home/$USER/trizen
	arch-chroot $TARGET su $USER -c "cd /home/$USER/trizen && makepkg -si"
	arch-chroot $TARGET su $USER -c trizen -Sy --noedit --noconfirm visual-studio-code-bin
	arch-chroot $TARGET ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime
	arch-chroot $TARGET passwd

else
	echo "failed to install base packages."
fi

