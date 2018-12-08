#!/usr/bin/python3
# This is the tool i'm using to make my video re-encode
import sys
import os
from subprocess import run

def encode_file(source, dest, threads=12, mapping=['-map', "0"]):
    cmd = [
        "/usr/bin/ffmpeg",
        "-i", str(source),
        "-scodec", "copy"
    ] + mapping + [
        "-threads", str(threads),
        "-aspect", "16:9",
        "-y",
        "-f", "matroska",
        "-ab", "128k",
        "-ar", "48000",
        "-ac", "2",
        "-preset", "slow",
        "-crf", "14",
        "-rc", "vbr_hq",
        "-rc-lookahead", "32",
        "-vcodec", "hevc_nvenc",
        str(dest)
    ]
    command_line = " ".join(cmd)
    print(command_line)
    run(cmd);

def encode_dir(source, dest):
    if not os.path.exists(dest):
        os.mkdir(dest)
    if not os.path.isdir(dest):
        raise(ValueError(dest))
    if not os.path.exists(source):
        raise(FileNotFoundError(source))
    # if the source is the same as the destination there is a problem.
    if source == dest:
            raise(ValueError)
    # is the source a file ? if so we just encode it an return
    if os.path.isfile(source):
        filename = source.split('/')[-1]
        return encode_file(source, os.path.join(dest, filename))
    for file in os.listdir(source):
        full_source_path = os.path.join(source, file)
        if os.path.isfile(full_source_path):
            encode_file(full_source_path, "{}/{}".format(dest, file))
        else:
            encode_dir(full_source_path)

if __name__ == "__main__":
    try:
        encode_dir(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
    except IndexError:
        print("usage: {} <source dir> <destination dir>".format(sys.argv[0]))
    except ValueError:
        print("wrong dir as target specified.")
    except FileNotFoundError as e:
        print("No such file or directory.", e.filename)
    except PermissionError:
        print("You don't have permissions for this.")
