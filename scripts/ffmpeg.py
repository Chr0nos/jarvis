#!/usr/bin/python3
# This is the tool i'm using to make my video re-encode
import os
from subprocess import run


class FFmpeg:
    encoder = '/usr/bin/ffmpeg'
    HDR = 'YUV444p10le'
    STD = 'yuv444p'

    @classmethod
    def run(cls, *args):
        command = (cls.encoder, *args)
        print('running', *command)
        return run(command, check=True)

    @classmethod
    def to_x264(cls, source, output, *args, quality=25, format='yuv444p'):
        # 'YUV444p10le'
        cmd = (
            '-i', source,
            '-vcodec', 'h264_nvenc',
            '-vf', f'format={format}',
            '-qp', str(quality),
            '-gpu', 'any',
            '-preset', 'fast',
            '-y',
            '-threads', '12',
            '-acodec', 'copy'
        )
        return cls.run(*cmd, *args, output)

    @classmethod
    def to_hevc(cls, source, output, *args, quality=25):
        cmd = (
            '-i', source,
            '-vcodec', 'libx265',
            '-rc', 'vbr_hq',
            '-rc-lookahead', '32',
            '-qp', str(quality),
            '-gpu', 'any',
            '-acodec', 'copy'
        )
        return cls.run(*cmd, *args, output)

    @classmethod
    def to_webm(cls, source, output, *args, quality=25):
        output = '.'.join(output.split('.')[0:-1]) + '.webm'
        cmd = (
            '-i', source,
            '-threads', '12',
            '-vcodec', 'libvpx-vp9',
            '-b:v', '1M',
            '-q:v', str(quality),
            '-f', 'webm'
        )
        return cls.run(*cmd, *args, output)

    @classmethod
    def convert(cls, source_dir, dest_dir, cvt_func=None, *args, **kwargs):
        if not os.path.isdir(source_dir):
            raise FileNotFoundError(source_dir)
        if cvt_func is None:
            cvt_func = cls.to_x264
        len_src = len(source_dir)
        for pwd, _, files in os.walk(source_dir):
            for file in sorted(files):
                relative = pwd[len_src:]
                source = os.path.join(pwd, file)
                dest = os.path.join(dest_dir, relative, file)
                os.makedirs(os.path.join(dest_dir, relative), exist_ok=True)
                cvt_func(source, dest, *args, **kwargs)
