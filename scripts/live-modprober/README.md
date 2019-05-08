# What is this ?
this this is a little python script who parses kernel arguments for `live-usb` linux installation and who load/unload the correct kernel modules with modprobe.
if you use `nvidia` module at boot, a proper `Xorg` configuration file will be generated.

# Why ?
i installed an `ArchLinux` distribution on an usb-ssd drive, and i need to be able to boot litteraly on any `modern` (64 bits) machine without knowing the video card configuration or kernel modules to load in avance, so i pass them with `rEFInd` boot loader to the kernel.

# Installation
```
make install
```

# Uninstall
```
make uninstall
```

# Parameters format:
```
modprobe.blacklist=module1,module2,... modprobe.load=module4,module5,...
```

examples:
```
modprobe.blacklist=nouveau modprobe.load=nvidia
modprobe.blacklist=nvidia modprobe.load=nouveau
```

# Do you accept pull requests ?
Yes, with pleasure, if the code is not stupid

# Licence
honestly, i don't care, do whatever you want with this, no guaranties
