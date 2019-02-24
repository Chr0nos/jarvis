#!/usr/bin/python3
# This is the tool i'm using to make my video re-encode
import sys
import os
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


# TODO: refaire cette fonction pour qu elle gere les sous dossiers

def encode_dir(vp, ap, source, dest):
    if not os.path.exists(dest):
        os.mkdir(dest)
    if not os.path.isdir(dest):
        raise ValueError(dest)
    if not os.path.exists(source):
        raise FileNotFoundError(source)
    # if the source is the same as the destination there is a problem.
    if source == dest:
            raise ValueError(dest)
    # is the source a file ? if so we just encode it an return
    if os.path.isfile(source):
        filename = source.split('/')[-1]
        return encode_file(vp, ap, source, os.path.join(dest, filename))
    for file in os.listdir(source):
        full_source_path = os.path.join(source, file)
        full_dest_path = os.path.join(dest, file)
        if os.path.isfile(full_source_path):
            encode_file(vp, ap, full_source_path, full_dest_path)
        else:
            encode_dir(vp, ap, full_source_path, dest)


if __name__ == "__main__":
    vp = VideoPreset()
    ap = AudioPreset()

    try:
        encode_dir(vp, ap, os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
    except IndexError:
        print("usage: {} <source dir> <destination dir>".format(sys.argv[0]))
    except ValueError:
        print("wrong dir as target specified.")
    except FileNotFoundError as e:
        print("No such file or directory.", e.filename)
    except PermissionError:
        print("You don't have permissions for this.")
