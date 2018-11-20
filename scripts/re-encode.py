#!/usr/bin/python3
# This is the tool i'm using to make my video re-encode
import sys
import os
from subprocess import run

def encode_file(source, dest, threads=12):
    cmd = [
        "/usr/bin/ffmpeg",
        "-i", '"{}"'.format(str(source)),
        "-scodec", "copy",
        "-map", "0:0",
        "-map", "0:2",
        "-map", "0:3",
        "-threads", str(threads),
        "-aspect", "16:9",
        "-y",
        "-f", "matroska",
        "-ab", "128k",
        "-ar", "48000",
        "-ac", "2",
        "-vcodec", "hevc_nvenc",
        '"{}"'.format(str(dest))
    ]
    command_line = " ".join(cmd)
    # run(cmd, capture_output=True);
    print(command_line)
    os.system(command_line)

def encode_dir(source, dest):
    if not os.path.isdir(dest):
        raise(ValueError(dest))
    if not os.path.exists(source):
        raise(FileNotFoundError(source))
    if not os.path.exists(dest):
        os.mkdir(dest)
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
