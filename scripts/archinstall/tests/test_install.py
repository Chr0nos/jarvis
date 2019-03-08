import sys, os;
sys.path.insert(0, os.getcwd())

from arch import ArchInstall

import pytest
from mock import patch

from fakeai import fakearch
from test_user import fake_chroot


@pytest.fixture
def arch():
    return ArchInstall(hostname='localhost')


def test_install_missing_hostname():
    with pytest.raises(TypeError):
        arch = ArchInstall()


def test_install_put(arch):
    filepath = '/tmp/test'
    if os.path.exists(filepath):
        os.unlink(filepath)
    test_content = 'test\ndata\nfor\fun\n\n'
    arch.file_put(filepath, test_content)
    with open(filepath, 'r') as fd:
        assert fd.read() == test_content
    os.unlink(filepath)


@patch('os.chroot', side_effect=fake_chroot)
def test_install_bootloader_grub(fc, fakearch):
    fakearch.install_bootloader('grub', device='/dev/sda')
    fakearch.install_bootloader('grub-efi', device='/dev/sda')
    with pytest.raises(ValueError):
        fakearch.install_bootloader('grub-test', device='/dev/sda')
    old_mnt = fakearch.mnt


def test_install_attributes(fakearch):
    assert fakearch.mnt is not None
    assert fakearch.hostname is not None
    assert fakearch.lang is not None
    assert fakearch.timezone is not None
    assert fakearch.locales
    assert fakearch.efi_capable is not None


def test_install_hash(fakearch):
    hash(fakearch)


def test_arch_instance():
    """
    test about kwargs.
    """
    arch = ArchInstall(hostname='louis', mnt='/', lang='en_EN.UTF-8')
    assert arch.hostname == 'louis'
    assert arch.mnt == '/'
    assert arch.lang == 'en_EN.UTF-8'
