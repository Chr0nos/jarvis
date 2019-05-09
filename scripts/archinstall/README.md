# What is this ?
A fully automatic way to install ArchLinux

# How does it works ?
The best way is to write a simple .json file (examples are available in ./json/
then just run `./install_json.py json/file.json`
the script will only asks for root and user(s) password(s) at the end of the installation

# The case of the live iso
the live iso does not have `git` intalled but you can do:
```shell
pacman -S unzip
wget https://github.com/Chr0nos/jarvis/archive/master.zip -O jarvis.zip
unzip jarvis
cd jarvis/scripts/archinstall/
```

or

```shell
pacman -S git
git clone https://github.com/Chr0nos/jarvis.git
cd jarvis/scripts/archinstall/
```

# Example
for this example, i will assume that you use `/dev/sdx` device.


```shell
cfdisk /dev/sdx

# create /boot partition
mkfs.vfat -F32 -n EFI /dev/sdx1

# create system partition (root)
mkfs.ext4 -L Arch /dev/sdx2

# create home partition
mkfs.ext4 -L Home /dev/sdx3

# create swap
mkswap /dev/sdx4

# prepair the installation
mount /dev/sdx2 /mnt
mkdir -pv /mnt/boot/efi
mount /dev/sdx1 /mnt/boot/efi
mount /dev/sdx3 /mnt/home
swapon /dev/sdx4


./install_json.py ./json/deepin.json
```

That's all, you can now reboot

# Dependencies
None, just for the unit tests, for python i just use builtin modules
