import requests
import os
from datetime import datetime, timedelta


class SpeedOMetter:
    """Provides a easy way to monitor speed of a download
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_size = 0
        self.last_date = datetime.now().timestamp()

    def update(self, new_size) -> int:
        """return the bytes per seconds since last upadte.
        """
        now = datetime.now().timestamp()
        delta_time = now - self.last_date
        delta_size = new_size - self.last_size

        self.last_date = now
        self.last_size = new_size
        try:
            return int(delta_size / delta_time)
        except ZeroDivisionError:
            return 0


def hsize(size, factor=1024, precision=2) -> str:
    """Convert a size in bytes to a human readable one
    """
    units = ('b', 'kb', 'Mb', 'Gb', 'Tb', 'Eb', 'Pb', 'Yb')
    p = 0
    mp = len(units) - 1
    while p < mp and size >= factor:
        size /= factor
        p += 1
    return f'{round(size, precision)}{units[p]}'


def eta(size, speed) -> timedelta:
    """size in bytes,
    speed in bytes per second
    """
    try:
        return timedelta(seconds=size / speed)
    except ZeroDivisionError:
        return timedelta(seconds=0)


def getfile(url, filepath, chunksize=15000, retries=5, bytes_range=None,
            **kwargs):
    """Download the given url into filepath,
    if the filepath currently exists the function will atemp a resume

    Usage:
    for current, total in getfile(url, '/tmp/file.txt'):
        print(current, total)
    """
    def get_range_header() -> dict:
        start, end = 0, ''
        if bytes_range is not None:
            start, end = bytes_range
        if os.path.exists(filepath):
            start = os.stat(filepath).st_size
        else:
            return {}
        return {'Range': f'bytes={start}-{end}'}

    headers = kwargs.pop('headers', {})
    headers.update(get_range_header())
    kwargs['headers'] = headers

    with requests.get(url, stream=True, **kwargs) as response:
        response.raise_for_status()
        current_size = 0
        if os.path.exists(filepath):
            current_size = os.stat(filepath).st_size
        total_size = int(response.headers.get('Content-Length', -1)) + current_size
        with open(filepath, 'ab+') as file:
            for chunk in response.iter_content(chunk_size=chunksize):
                current_size += file.write(chunk)
                yield (current_size, total_size)
    if current_size != total_size:
        if retries > 0:
            return getfile(url, filepath, chunksize, retries - 1,
                           (current_size, total_size), **kwargs)
        raise ValueError(current_size)
