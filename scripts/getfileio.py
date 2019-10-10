import asyncio
import aiohttp
import aiofile
import os


async def getfile(url: str, filepath, chunk_size=150000,
                  bytes_range=None, retries=5, **kwargs):

    def get_headers(file_size=None) -> dict:
        start, end = 0, ''
        if bytes_range is not None:
            start, end = bytes_range
        if file_size is not None:
            start = file_size
        else:
            return {}
        return {'Bytes-Range': f'{start}-{end}'}

    async def fetch(afp) -> None:
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
                    print(current_size, total_size)
        if total_size is not None and current_size != total_size:
            raise ValueError(current_size)

    kwargs.setdefault('raise_for_status', True)
    async with aiofile.AIOFile(filepath, 'ab+') as afp:
        for current_retry in range(retries):
            try:
                if current_retry != 0:
                    print('retrying download of', url)
                return await fetch(afp)
            except ValueError as error:
                if current_retry == retries:
                    raise error
        await afp.fsync()


if __name__ == "__main__":
    filepath = '/dev/shm/test.pdf'
    try:
        os.unlink(filepath)
    except FileNotFoundError:
        pass
    asyncio.run(getfile('http://freebox/gen/100M', filepath))
    # asyncio.run(getfile('https://thorin.me/static/cv.pdf', filepath))
    print('done')
