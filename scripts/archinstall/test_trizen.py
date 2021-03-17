from arch import ArchInstall, ArchUser
from mock import patch

def donothink(path):
    pass

@patch("os.chroot", side_effect=donothink)
def run(_):
    arch = ArchInstall(mnt="/", hostname="StarK")
    user = ArchUser(arch, username="adamaru", uid=1000, gid=1000)
    user.install_trizen()

if __name__ == "__main__":
    run()
