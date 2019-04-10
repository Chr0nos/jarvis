import os

from .tools import ArchChroot
from .mount import MountPoint
from .exceptions import ConfigError

class BootLoader():
	device = None
	name = None
	runner = None

	def __init__(self, runner, device=None):
		self.device = device
		self.runner = runner

	def install(self, **kwargs):
		raise NotImplementedError

	@staticmethod
	def get_partition_id(path):
		"""
		returns the partition id of a mount point.
		if the path is not a mount point a ValueError will be raised.
		"""
		for mount in MountPoint.list():
			if mount['mnt'] == path:
				partition = int(mount['device'][-1])
				return partition
		raise ValueError(path)


class BootLoaderEfi(BootLoader):
	efi = None
	boot = '/boot/efi'

	def mkentry(self, label, partition):
		"""
		create a new uefi entry into the bios
		also checks thats the provided informations are correct.
		"""
		assert self.efi
		efi_mnt = self.runner.mnt + self.boot
		assert os.path.exists(efi_mnt + self.efi), '.efi file not found'
		assert os.path.exists(self.device), 'device not found'
		assert isinstance(partition, int)
		assert os.path.exists(self.device + partition), 'partition not found'
		self.runner.run([
			'efibootmgr', '-c',
			'-L', label,
			'-l', self.efi,
			'-d', self.device,
			'-p', str(partition),
		])


class BootLoaderRefind(BootLoaderEfi):
	name = 'refind'
	efi = '/EFI/refind/refind_x64.efi'
	boot = '/boot/efi'

	def install_alldrivers(self):
		# refind show error on --alldrivers ? okay :)
		self.runner.run(['cp', '-vr',
			'/usr/share/refind/drivers_x64',
			self.boot + '/EFI/refind/drivers_x64'])

	def install(self, alldrivers=True, **kwargs):
		assert self.runner.efi_capable, 'This system was not booted in uefi mode.'
		mnt = self.runner.mnt
		if not os.path.ismount(mnt + self.boot):
			raise(ConfigError('please create and mount /boot/efi (vfat)'))

		with ArchChroot(mnt):
			self.runner.run(['mkdir', '-vp', self.boot + '/EFI/refind'])
			self.runner.pkg_install(['extra/refind-efi'])
			if alldrivers:
				self.install_alldrivers()

		# launching the install from outside of the chroot (host system)
		self.runner.run(['refind-install', '--root', mnt + self.boot])

	def add_entry(self):
		# TODO: check if this call is needed in a further test with vmware
		partition = self.get_partition_id(self.runner.mnt + self.boot)
		self.mkentry('rEFInd', partition)


class BootLoaderGrub(BootLoader):
	name = 'grub'

	def install(self, **kwargs):
		target = kwargs.get('target', 'i386-pc')
		assert target != 'x86_64-efi' or self.runner.efi_capable, 'This system was not booted in uefi mode.'
		with ArchChroot(self.runner.mnt):
			self.runner.pkg_install(['grub'] + ['community/os-prober'] if kwargs.get('os-prober') else [])
			if not os.path.exists('/boot/grub'):
				os.mkdir('/boot/grub')
			self.runner.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
			self.runner.run(['grub-install', '--target', target, self.device])
