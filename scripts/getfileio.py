#!/usr/bin/python3
import asyncio
import aiohttp
import aiofile
import os
from hsize import hsize


async def getfile(url: str, filepath, chunk_size=150000, bytes_range=None,
                  retries=5, nocheck=False, **kwargs) -> None:
    """
    in case of a non file you wan to use nocheck=True (like /dev/null)
    valid kwargs:
    callback : called on each chunk received after it was wrote to disk
    userdata : sent to callback on each call, ignored if no callback.
    """
    callback = kwargs.pop('callback', None)
    userdata = kwargs.pop('userdata', None)
    kwargs.setdefault('raise_for_status', True)

    def get_headers(file_size=None) -> dict:
        start, end = 0, ''
        if bytes_range is not None:
            start, end = bytes_range
        if file_size is not None:
            start = file_size
        else:
            return {}
        return {'Bytes-Range': f'{start}-{end}'}

    async def fetch(afp: aiofile.AIOFile) -> None:
        current_size = 0
        if os.path.exists(filepath):
            current_size = os.stat(filepath).st_size
        headers = kwargs.pop('headers', {})
        headers.update(get_headers())
        kwargs['headers'] = headers
        async with aiohttp.ClientSession(**kwargs) as session:
            async with session.get(url) as response:
                total_size = response.headers.get('Content-Length', None)
                if total_size is not None:
                    total_size = int(total_size) + current_size
                async for chunk in response.content.iter_chunked(chunk_size):
                    current_size += len(await afp.write(chunk))
                    if callback:
                        await callback(filepath, current_size, total_size,
                                       userdata)
                    # yield filepath, current_size, total_size
        if nocheck:
            return
        if total_size is not None and current_size != total_size:
            raise ValueError(current_size)

    async with aiofile.AIOFile(filepath, 'ab+') as afp:
        for current_retry in range(retries):
            try:
                if current_retry != 0:
                    print('retrying download of', url)
                await fetch(afp)
                return
            except ValueError as error:
                if current_retry == retries:
                    raise error(f'{filepath}')


def clean(*files):
    for f in files:
        try:
            os.unlink(f)
        except FileNotFoundError:
            pass


async def print_progression(filepath, current, total, _):
    print(f'{filepath} -> {hsize(current)} of {hsize(total)}')


async def many_query(urls, method='get', asjson=True, verbose=False, **kwargs):
    async def process_link(url, func):
        if verbose:
            print('getting', url)
        content = await func(url, **kwargs)
        return await getattr(content, 'json' if asjson else 'read')()

    async with aiohttp.ClientSession() as session:
        jobs = [process_link(url, getattr(session, method.lower()))
                for url in urls]
        return await asyncio.gather(*jobs)


if __name__ == "__main__":
    clean('/tmp/test', '/dev/shm/cv.pdf')

    async def test():
        alpha = getfile('http://freebox/gen/1M', '/tmp/test',
                        callback=print_progression)
        bravo = getfile('https://thorin.me/static/cv.pdf', '/dev/shm/cv.pdf',
                        callback=print_progression)
        tasks = asyncio.gather(alpha, bravo)
        return await tasks

    asyncio.run(test())
    print('done')
