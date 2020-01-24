#!/usr/bin/python3
# This is the tool i'm using to make my video re-encode
import sys
import os
import argparse
from subprocess import call

def run_or_except(cmd, file_to_remove=None):
    if call(cmd) != 0:
        if file_to_remove:
            print('removing', file_to_remove)
            os.unlink(file_to_remove)
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
    def __init__(self, vcodec='nvenc_h264', preset='fast', aspect='16:9'):
        self.cmd = [
            '-vcodec', vcodec,
            '-preset', preset,
            '-y',
            '-aspect', aspect,
            '-threads', str(12),
            # '-hwaccel', 'vaapi',
            # '-vaapi_device', '/dev/dri/renderD128'
        ]

    def getCmd(self):
        return self.cmd

    def __str__(self):
        return ' '.join(self.cmd)


class VideoH264(VideoPreset):
    def __init__(self, quality=25):
        super().__init__(vcodec='h264_nvenc')
        self.cmd.extend([
            '-vf', 'format=yuv444p',
            '-qp', str(quality),
            '-gpu', 'any',
        ])


class VideoHevc(VideoPreset):
    def __init__(self, quality=22, vcodec='hevc_nvenc', preset='fast', aspect='16:9'):
        super().__init__(vcodec, preset, aspect)
        self.cmd.extend([
            "-rc", "vbr_hq",
            "-rc-lookahead", "32",
            '-qp', str(quality),
            '-gpu', 'any',
        ])


class VideoXvid(VideoPreset):
    def __init__(self):
        super().__init__(vcodec='libxvid')


def encode_file(vp, ap, source, dest: str):
    if dest.endswith('.webm'):
        dest = dest[0:-4] + '.mkv'
    cmd = [
        '/usr/bin/ffmpeg',
        '-i', source
    ] + ap.getCmd() + vp.getCmd() + [
        # '-map', '0',
        # '-loglevel', 'debug',
        dest
    ]
    run_or_except(cmd, dest)


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

    def mirror(self, callback, target, subdir, userdata):
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
                self.mirror(callback, target, relative_path, userdata)
            else:
                callback(False, relative_path, fullpath, fulldst, userdata)


def encode_dir(isDir, relative, fullSrc, fullDst, userdata):
    # print(f'{isDir} : {fullSrc} -> {fullDst}')
    if isDir and not os.path.exists(fullDst):
        print(f'Making dir {fullDst}')
        os.mkdir(fullDst)
        return
    else:
        if os.path.exists(fullDst) and not userdata.get('overwrite'):
            print(f'destination {relative} already exists')
            return
        print(f'Encoding {relative}')
        encode_file(
            vp=userdata['video'],
            ap=userdata['audio'],
            source=fullSrc,
            dest=fullDst)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', '-s', help='source dir')
    parser.add_argument('--dest', '-d', help='destination dir')
    parser.add_argument('--overwrite', '-y', help='overwrite existing files.', action='store_true', default=False)
    parser.add_argument('--preset', '-p', help='video preset to use', choices=('freebox', 'hevc', 'xvid', 'x264'), default='hevc')
    args = parser.parse_args()
    if not args.source or not args.dest:
        parser.print_help()
        sys.exit(1)

    presets = {
        'freebox': VideoH264,
        'h264': VideoH264,
        'hevc': VideoHevc,
        'xvid': VideoXvid
    }
    config = {
        'video': presets[args.preset](),
        'audio': AudioPreset(),
        'overwrite': args.overwrite
    }
    print(config)
    try:
        if not os.path.exists(args.dest):
            os.mkdir(args.dest)
        walker = PathIterator(args.source)
        walker.mirror(encode_dir, args.dest, '', config)

    except ValueError:
        print("wrong dir as target specified.")
    except FileNotFoundError as e:
        print("No such file or directory.", e.filename)
    except PermissionError:
        print("You don't have permissions for this.")
