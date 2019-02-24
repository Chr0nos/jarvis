#!/usr/bin/python3
# This is the tool i'm using to make my video re-encode
import sys
import os
import argparse
from subprocess import call

def run_or_except(cmd):
    if call(cmd) != 0:
        raise Exception(cmd)


class AudioPreset():
    def __init__(self):
        self.cmd = [
            '-ab', '128k',
            '-ar', '48000'
        ]

    def getCmd(self):
        return self.cmd


class VideoPreset():
    def __init__(self, crf=14, vcodec='h264_nvenc', preset='fast', aspect='16:9'):
        self.cmd = [
            '-vcodec', vcodec,
            '-crf', str(crf),
            '-preset', preset,
            '-y',
            '-aspect', aspect,
            '-threads', str(12)
        ]

    def getCmd(self):
        return self.cmd


class VideoHevc(VideoPreset):
    def __init__(self, crf=14, vcodec='hevc_nvenc', preset='fast', aspect='16:9'):
        super().__init__(crf, vcodec, preset, aspect)
        self.cmd.extend([
            "-rc", "vbr_hq",
            "-rc-lookahead", "32",
        ])

def encode_file(vp, ap, source, dest):
    cmd = [
        '/usr/bin/ffmpeg',
        '-i', source
    ] + ap.getCmd() + vp.getCmd() + [
        '-map', '0',
        dest
    ]
    run_or_except(cmd)


class PathIterator():
    def __init__(self, root):
        self.root = root

    @staticmethod
    def join(root, subdir=None):
        if not subdir:
            return root
        return os.path.join(root, subdir)

    def walk(self, callback=print, subdir=None):
        path = self.join(self.root, subdir)
        for item in os.listdir(path):
            fullpath = os.path.join(path, item)
            if os.path.isdir(fullpath):
                callback(fullpath)
                self.walk(callback, fullpath)
            else:
                callback(fullpath)

    def mirror(self, callback, target, subdir='', userdata=None):
        """
        callback prototype must be:
        def callback(isDir, relativePath, fullSource, fullDest, userdata)
        """
        path = self.join(self.root, subdir)
        path_dest = self.join(target, subdir)
        for item in os.listdir(path):
            fullpath = os.path.join(path, item)
            fulldst = os.path.join(path_dest, item)
            relative_path = self.join(subdir, item)
            if os.path.isdir(fullpath):
                callback(True, relative_path, fullpath, fulldst, userdata)
                self.mirror(callback, target, relative_path)
            else:
                callback(False, relative_path, fullpath, fulldst, userdata)


def encode_dir(isDir, relative_path, fullSrc, fullDst, userdata):
    print(f'{isDir} : {fullSrc} -> {fullDst}')
    if isDir and not os.path.exists(fullDst):
        print(f'Making dir {fullDst}')
        os.mkdir(fullDst)
        return
    else:
        print(f'Encoding {relative_path}')
        encode_file(
            vp=userdata['video'],
            ap=userdata['audio'],
            source=fullSrc,
            dest=fullDst)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', '-s', help='source dir')
    parser.add_argument('--dest', '-d', help='destination dir')
    args = parser.parse_args()
    if not args.source or not args.dest:
        parser.print_help()
        sys.exit(1)

    config = {
        'video': VideoPreset(),
        'audio': AudioPreset()
    }
    try:
        if not os.path.exists(args.dest):
            os.mkdir(args.dest)
        walker = PathIterator(args.source)
        walker.mirror(encode_dir, args.dest, userdata=config)

    except ValueError:
        print("wrong dir as target specified.")
    except FileNotFoundError as e:
        print("No such file or directory.", e.filename)
    except PermissionError:
        print("You don't have permissions for this.")
