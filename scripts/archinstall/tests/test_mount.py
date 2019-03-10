import sys, os;
sys.path.insert(0, os.getcwd())

from arch.mount import MountPoint

def test_mount_proc():
    m = MountPoint(dest='/proc', fs_type='proc', device='/proc')
    assert m.is_mount()

def test_mount_list():
    MountPoint.list()

def test_mount_str():
    m = MountPoint(dest='/proc', fs_type='proc', device='/proc')
    print(m)
    assert str(m) is not None

# def test_mount_already_mount():
#     m = MountPoint(dest='/proc', fs_type='proc', device='/proc')
#     assert m.is_mount()
