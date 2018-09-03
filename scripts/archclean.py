#!/usr/bin/python3
import os
import stat
import re
import sys

CACHE_DIR = "/var/cache/pacman/pkg/"


def hsize(size):
	units = ('b', 'K', 'M', 'G', 'T', 'P', 'E')
	i = 0
	m = len(units)
	while size >= 1024 and i < m:
		size /= 1024
		i += 1
	return ("{}{}".format(round(size, 2), units[i]))


def package_clean(lst, real=False):
	l = len(lst)
	if (l == 1):
		return(0)
	gained_space = 0
	lst = sorted(lst, key=lambda x: x[0], reverse=True)
	keep_file = True
	for ctime, filepath, filesize in lst:
		if keep_file:
			print("[KEEP] {:50} [{:4}]".format(filepath, hsize(filesize)))
			keep_file = False
			continue
		print("[RM  ] {:50} [{:4}]".format(filepath, hsize(filesize)))
		if real == True:
			os.unlink(CACHE_DIR + filepath)
		gained_space += filesize
	return(gained_space)


def packages_list(real=False):
	dico = {}
	base_name = re.compile(r'^([a-z-\d]+)')
	for file in os.listdir(CACHE_DIR):
		base = base_name.match(file).group()
		st = os.stat(CACHE_DIR + file)
		if not dico.get(base):
			dico[base] = []
		dico[base].append((st.st_ctime, file, st.st_size))

	gained_space = 0
	keys = list(dico.keys())
	keys.sort()
	for key in keys:
		gained_space += package_clean(dico[key], real)
	print("----\nGained space: {}".format(hsize(gained_space)))


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("usage: {} [-r/-p]".format(sys.argv[0]))
		print("if '-r' is not present, then the script will run in pretend mode")
		sys.exit(0)
	real = sys.argv[1] == "-r"
	try:
		packages_list(real)
	except PermissionError:
		print("Cannot delete files in {}, please run me as root.".format(
			CACHE_DIR))
	if not real:
		print("This script has run in pretend mode")
