import asyncio
from datetime import datetime, timedelta
from functools import wraps
import os
import sys

from typing import Dict, Optional, Any, Generator, Union
from aiohttp.helpers import get_running_loop
import httpx
from bson.objectid import ObjectId
from motorized.types import PydanticObjectId
from pydantic.main import BaseModel
from pydantic.types import PositiveInt
from tempfile import TemporaryDirectory
import zipfile
from asyncio_pool import AioPool
import aiohttp
import aiofile
from typing import Tuple, List
from enum import Enum
from contextlib import asynccontextmanager
import traceback
import bs4 as BeautifulSoup

from motorized import Document, QuerySet
from pydantic import Field


class ToonBaseUrlInvalidError(Exception):
    pass


class ToonNotAvailableError(Exception):
    pass


def raise_on_any_error_from_pool(pool_result: List[Optional[Exception]]):
    errors = list(filter(None, pool_result))
    for error in errors:
        if isinstance(error, asyncio.exceptions.CancelledError):
            raise error
        if isinstance(error, KeyboardInterrupt):
            raise error
        print(traceback.format_exc(error))
    assert not errors, errors


class UserAgent(Enum):
    FIREFOX = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'
    CHROME_LINUX = 'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    CHROME = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'


class Chdir:
    def __init__(self, path):
        self.dir = path
        self.previous_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.dir)

    def __exit__(self, *_):
        os.chdir(self.previous_dir)


class Http2Mixin:
    """Only use if you have no choices, httpx is realy slower than aiohttp
    """
    _page_content: str
    _no_session: False

    async def get_page_content(self) -> str:
        if self._page_content:
            return self._page_content
        async with httpx.AsyncClient(http2=True, timeout=10) as client:
            response = await client.get(self.url, headers=self.get_headers(), cookies=self._cookies)
            response.raise_for_status()
            self._page_content = response.read()
        return self._page_content

    async def download_links(self, client: httpx.AsyncClient, cbz: zipfile.ZipFile, pair: Tuple[str, str]):
        output_filepath, url = pair
        if self._no_session:
            response = await httpx.get(url, headers=self.get_headers(), cookies=self._cookies)
        else:
            response = await client.get(url)
        response.raise_for_status()
        page_data = response.read()
        self.check_page_content(page_data)
        await self._save_page_data_to_disk(output_filepath, page_data)
        cbz.write(output_filepath, os.path.basename(output_filepath))
        await self._progress()

    @asynccontextmanager
    async def get_client(self):
        session  = httpx.AsyncClient(
            http2=True,
            headers=self.get_headers(),
            cookies=self.get_cookies(),
            follow_redirects=False
        )
        async with session as client:
            yield client


class SoupMixin:
    _soup: Optional[BeautifulSoup.BeautifulSoup] = None

    async def get_soup(self):
        if self._soup:
            return self._soup
        page_content = await self.get_page_content()
        self._soup = BeautifulSoup.BeautifulSoup(page_content, 'lxml')
        return self._soup


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
    lang: str
    corporate: bool = True

    _page_content: Optional[str] = None
    _cookies: aiohttp.CookieJar
    _quote_cookies: bool = True

    class Mongo:
        manager_class = ToonManager
        collection = 'toons'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cookies = self.get_cookie_jar()

    def __str__(self):
        return f'{self.name} {self.episode}'

    def get_cookie_jar(self) -> aiohttp.CookieJar:
        loop = get_running_loop()
        jar = aiohttp.CookieJar(loop=loop, unsafe=True, quote_cookie=self._quote_cookies)
        cookies: Optional[Dict] = self.get_cookies()
        if cookies is not None:
            jar.update_cookies(cookies)
        return jar

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

    def get_cookies(self) -> Optional[Dict]:
        return None

    def get_headers(self):
        headers = {
            'Referer': getattr(self, 'url', None) or self.domain,
            'User-Agent': UserAgent.CHROME.value,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'max-age=0'
        }
        if getattr(self, '_lowerize_headers', False):
            headers = dict({k.lower(): v for k, v in headers.items()})
        return headers

    async def log(self, message: str, flush=True, **kwargs) -> None:
        kwargs.setdefault('end', '')
        print(message, **kwargs)
        if flush:
            sys.stdout.flush()

    async def get_page_and_destination_pairs(self, folder: str) -> List[Tuple[str, str]]:
        pages = await self.get_pages()

        def get_output_filename(index: int, page: str) -> str:
            return os.path.join(folder, f'{index:03}.jpg')

        return list([
            (get_output_filename(i, page), page)
            for i, page in enumerate(pages)
        ])

    async def create_folder(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    async def _save_page_data_to_disk(self, filepath: str, data: bytes) -> None:
        async with aiofile.async_open(filepath, 'wb') as fp:
            await fp.write(data)

    async def download_links(self, client: aiohttp.ClientSession, cbz: zipfile.ZipFile, pair: Tuple[str, str]) -> None:
        output_filepath, url = pair
        request = client.get(url)
        async with request as response:
            response.raise_for_status()
            page_data = await response.read()
            self.check_page_content(page_data)
            await self._save_page_data_to_disk(output_filepath, page_data)
            cbz.write(output_filepath, os.path.basename(output_filepath))
            await self._progress()

    async def pull(self, pool_size=3) -> None:
        assert self.name
        await self.create_folder()
        await self.log(f'{self}: ')

        pool = AioPool(size=pool_size)
        with TemporaryDirectory() as tmpd:
            with Chdir(tmpd):
                pair_list = (await self.get_page_and_destination_pairs(tmpd))
                cbz = zipfile.ZipFile(self.cbz_path, 'w', zipfile.ZIP_DEFLATED)
                try:
                    async with self.get_client() as client:
                        download_coroutine = lambda pair: self.download_links(client, cbz, pair)
                        raise_on_any_error_from_pool(await pool.map(download_coroutine, pair_list))
                    cbz.close()
                except (KeyboardInterrupt, asyncio.exceptions.CancelledError) as error:
                    cbz.close()
                    os.unlink(cbz.filename)
                    await self.log('removed incomplete cbz', end='\n')
                    raise error
            await self.log('\n')

    @asynccontextmanager
    async def get_client(self):
        session = aiohttp.ClientSession(
            headers=self.get_headers(),
            cookie_jar=self._cookies,
        )
        async with session as client:
            yield client

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
        async with self.get_client() as client:
            request = client.get(url=self.url)
            async with request as response:
                if response.status == 403:
                    print(await response.read())
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
                await toon.pull(pool_size=pool_size)
                if not await toon.objects.filter(name=toon.name, episode=toon.episode).exists():
                    await toon.save()

            next_toon: Optional[AsyncToon] = await toon.get_next()
            if next_toon:
                # look in the db if we already know the next toon, if so we use it directly
                next_toon_in_db: Optional[AsyncToon] = await self.objects.filter(name=next_toon.name, episode=next_toon.episode).first()
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

    async def get_pages(self):
        raise NotImplementedError


AsyncToon.update_forward_refs()


def provide_soup(func):
    @wraps(func)
    async def wrapper(instance: SoupMixin, *args, **kwargs):
        try:
            soup = await instance.get_soup()
        except aiohttp.ClientResponseError as response_error:
            if response_error.status == 500:
                raise ToonNotAvailableError
            raise response_error
        return await func(instance, *args, soup=soup, **kwargs)
    return wrapper
