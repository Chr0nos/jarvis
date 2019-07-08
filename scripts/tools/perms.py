import os


def perm_fix(path, perm_dirs=None, perm_files=None):
	if not perm_dirs:
		perm_dirs = int('0755', 8)
		perms_files = int('0644', 8)
	for root, _, files in os.walk(path):
		for file in files:
			fullpath = os.path.join(root, file)
			os.chmod(fullpath, perms_dir if os.path.isdir(fullpath) else perms_files)
			print(fullpath)


if __name__ == '__main__':
	if len(os.sys.argv) < 2:
		print('Usage:', os.sys.argv[0], '<path>')
		os.sys.exit(1)
	perm_fix(os.sys.argv[1])
