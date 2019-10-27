import requests
import os


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
        total_size = int(response.headers.get('Content-Length', -1)) + \
            current_size
        with open(filepath, 'ab+') as file:
            for chunk in response.iter_content(chunk_size=chunksize):
                current_size += file.write(chunk)
                yield (current_size, total_size)
    if current_size != total_size:
        if retries > 0:
            return getfile(url, filepath, chunksize, retries - 1,
                           (current_size, total_size), **kwargs)
        raise ValueError(current_size)
