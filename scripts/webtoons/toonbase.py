import asyncio
from datetime import datetime
import os
import sys

from typing import Optional, Any, Generator
from attr import astuple
from bson.objectid import ObjectId
from motorized.types import PydanticObjectId
from pydantic.types import PositiveInt
from requests.cookies import cookiejar_from_dict
from tempfile import TemporaryDirectory
import zipfile
from asyncio_pool import AioPool
import aiohttp
import aiofile
from typing import Tuple, List

from motorized import Document, QuerySet
from pydantic import Field


class ToonBaseUrlInvalidError(Exception):
    pass


class ToonNotAvailableError(Exception):
    pass


class Chdir:
    def __init__(self, path):
        self.dir = path
        self.previous_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.dir)

    def __exit__(self, *_):
        os.chdir(self.previous_dir)


class ToonManager(QuerySet):
    lasts_ordering_selector = ['-created', '-chapter']

    async def lasts(self) -> Generator[None, None, "AsyncToon"]:
        names: List[str] = await self.distinct('name')
        for toon_name in names:
            toon = await self.filter(name=toon_name).sort(self.lasts_ordering_selector).first()
            yield toon


class AsyncToon(Document):
    name: str
    episode: int
    domain: str
    created: datetime = Field(default_factory=datetime.now)
    next: Optional[PydanticObjectId]

    _page_content: Optional[str] = None

    class Mongo:
        manager_class = ToonManager

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f'{self.name} {self.episode}'

    @property
    def path(self) -> str:
        return f'/mnt/aiur/Users/snicolet/Scans/Toons/{self.name}'

    @property
    def cbz_path(self) -> str:
        return f'{self.path}/{self.episode}.cbz'

    async def get_next(self) -> Optional["AsyncToon"]:
        raise NotImplementedError

    def exists(self) -> bool:
        return os.path.exists(self.cbz_path)

    def get_cookies(self):
        return {}

    def get_headers(self):
        return {
            'Referer': self.domain,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/61.0.3112.113 Safari/537.36',
        }

    async def log(self, message: str, flush=True, **kwargs) -> None:
        kwargs.setdefault('end', '')
        print(message, **kwargs)
        if flush:
            sys.stdout.flush()

    async def get_page_and_destination_pairs(self, folder: str) -> List[Tuple[str, str]]:
        pages = await self.pages()

        def get_output_filename(index: int, page: str) -> str:
            return os.path.join(folder, f'{index:03}.jpg')

        return list([
            (get_output_filename(i, page), page)
            for i, page in enumerate(pages)
        ])

    async def create_folder(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    async def pull(self, pool_size=3) -> None:
        assert self.name
        await self.create_folder()
        await self.log(f'{self}: ')
        cbz = None

        async def download_coroutine(pair) -> None:
            output_filepath, url = pair
            request = aiohttp.request(
                url=url,
                method='get',
                headers=self.get_headers(),
                cookies=cookiejar_from_dict(self.get_cookies())
            )
            async with request as response:
                response.raise_for_status()
                page_data = await response.read()
                self.check_page_content(page_data)
                async with aiofile.async_open(output_filepath, 'wb') as fp:
                    await fp.write(page_data)
                    cbz.write(output_filepath, os.path.basename(output_filepath))
                    await self._progress()

        pool = AioPool(size=pool_size)
        with TemporaryDirectory() as tmpd:
            with Chdir(tmpd):
                pair_list = (await self.get_page_and_destination_pairs(tmpd))
                cbz = zipfile.ZipFile(self.cbz_path, 'w', zipfile.ZIP_DEFLATED)
                try:
                    await pool.map(download_coroutine, pair_list)
                    cbz.close()
                except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
                    cbz.close()
                    os.unlink(cbz.filename)
                    self.log('removed incomplete cbz', end='\n')
            await self.log('\n')

    async def _progress(self):
        """Called each time a page has been downloaded successfully
        """
        print('.', end='')
        sys.stdout.flush()

    async def get_page_content(self) -> str:
        """return the source code of the main page and cache it into the `cache_content` attribute
        of this instance.

        raises:
        - asyncio.exceptions.ClientResponseError
        """
        if self._page_content:
            return self._page_content
        request = aiohttp.request(
            url=self.url,
            method='get',
            headers=self.get_headers(),
            cookies=self.get_cookies()
        )
        async with request as response:
            response.raise_for_status()
            page_content = await response.read()
        self._page_content = page_content
        return page_content

    def check_page_content(self, page_data: bytes) -> None:
        """Receive the actual data from the page after the fetch
        this function is here to be overided by custom checks
        """
        pass

    async def leech(self, pool_size: PositiveInt = 3) -> None:
        await self.log(f' --- {self.name} ---', end='\n')
        toon = self
        while toon:
            # if the toon does not exists on disk we pull it and save it in db
            if not toon.exists():
                await self.log(f"{toon}: ")
                await toon.pull(pool_size=pool_size)
                if not await toon.objects.filter(name=toon.name, episode=toon.episode).exists():
                    await toon.save()

            next_toon: Optional[AsyncToon] = await toon.get_next()
            if next_toon:
                # look in the db if we already know the next toon, if so we use it directly
                next_toon_in_db = await self.objects.filter(name=next_toon.name, episode=next_toon.episode).first()
                if next_toon_in_db:
                    next_toon = next_toon_in_db
                # otherwise save the new one
                else:
                    await next_toon.save()
                toon.next = next_toon.id
                await toon.save()

            # ready for next iteration on the loop
            toon = next_toon

    async def rename(self, newname) -> None:
        if newname == self.name:
            return
        folder = os.path.join('/', *self.path.split('/')[0:-1])
        new_folder = os.path.join(folder, newname)
        os.rename(self.path, new_folder)
        # rename other chapters
        await self.objects.collection.update_many({'name': self.name}, {'$set': {'name': newname}})
        await self.reload()


AsyncToon.update_forward_refs()
