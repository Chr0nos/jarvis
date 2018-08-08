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


def package_clean(name, lst, pretend=True):
    l = len(lst)
    if (l == 1):
        return(0)
    gained_space = 0
    # print("checking {} : {} versions present.".format(name, len(lst)))
    lst = sorted(lst, key=lambda x: x[0], reverse=True)
    keep_file = True
    for ctime, filepath, filesize in lst:
        if keep_file:
            print("[KEEP] {:50} [{:4}]".format(filepath, hsize(filesize)))
            keep_file = False
            continue
        print("[RM  ] {:50} [{:4}]".format(filepath, hsize(filesize)))
        if pretend == False:
            os.unlink(CACHE_DIR + filepath)
        gained_space += filesize
    return(gained_space)


def packages_list(pretend=True):
    dico = {}
    base_name = re.compile(r'^([a-z-\d]+)')
    for file in os.listdir(CACHE_DIR):
        base = base_name.match(file).group()
        st = os.stat(CACHE_DIR + file)
        if not dico.get(base):
            dico[base] = []
        dico[base].append((st.st_ctime, file, st.st_size))

    gained_space = 0
    for key, pkg in dico.items():
        gained_space += package_clean(key, pkg, pretend)
    print("----\ngained space: {}".format(hsize(gained_space)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: {} [-r/-p]".format(sys.argv[0]))
        print("if '-r' is not present, then the script will run in pretend mode");
        sys.exit(0)
    pretend = sys.argv[1] == "-r"
    packages_list(True);
    if not pretend:
        print("This script has run in pretend mode")
