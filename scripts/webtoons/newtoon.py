import os
import re
import sys
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

import aiohttp
from asyncio_pool import AioPool
from bs4 import BeautifulSoup
from motorized import (Document, EmbeddedDocument, Field, PrivatesAttrsMixin,
                       QuerySet)
from pydantic import HttpUrl, validator
from selenium import webdriver


FIREFOX = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'
CHROME_LINUX = 'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
CHROME = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'


def raise_on_any_error_from_pool(pool_result: List[Optional[Exception]]):
    errors = list(filter(None, pool_result))
    for error in errors:
        raise error


class InMemoryZipFile:
    def __init__(self, filename: str):
        self.io = BytesIO()
        self.cbz = zipfile.ZipFile(self.io, 'w', zipfile.ZIP_DEFLATED)
        self.filename = filename

    def __str__(self) -> str:
        return self.filename

    def exists(self) -> bool:
        return os.path.exists(self.filename)

    def write(self, filename: str, data: bytes) -> None:
        self.cbz.writestr(filename, data)

    def close(self):
        self.cbz.close()

    def save(self) -> None:
        self.close()
        self.io.seek(0)
        with open(self.filename, 'wb') as fp:
            fp.write(self.io.read())


class SeleniumMixin:
    _driver: Optional[webdriver.Firefox] = None

    @property
    def driver(self) -> webdriver.Firefox:
        if not self._driver:
            self._driver = webdriver.Firefox()
        return self._driver

    async def parse_url(self, url: str) -> BeautifulSoup:
        self.driver.get(url)
        return BeautifulSoup(self.driver.page_source, 'lxml')


class Chapter(PrivatesAttrsMixin, EmbeddedDocument):
    """
    Describe ONE chapter of a webtoon.
    Things to override:
    properties:
    - url
    functions:
    - get_pages_urls (return the list of urls)
    - nexts (return the list of next chapters after the curent instance)
    """
    name: str
    episode: Optional[int]
    _parent: Optional["WebToonPacked"]

    @validator('episode', pre=True)
    def validate_episode(cls, value: Optional[Union[int, str]]) -> Optional[int]:
        if isinstance(value, str):
            rule = re.compile(r'^[a-z\-]+(\d+)')
            match = rule.match(value)
            if match:
                chapter = match.groups()[0]
                return int(chapter)
        return value

    def __str__(self) -> str:
        return self.name

    @property
    def cbz_path(self) -> str:
        return os.path.join(self._parent.path, self.name + '.cbz')

    def exists(self) -> bool:
        return os.path.exists(self.cbz_path)

    async def pull(self, pool_size: int = 3) -> None:
        if self.exists():
            return
        self._start_pull()
        pair_list = list([(filename, str(url)) async for filename, url in self])
        if not pair_list:
            self._no_content()
            return

        pool = AioPool(pool_size)
        cbz = InMemoryZipFile(self.cbz_path)

        async with self._parent.get_client() as client:
            async def download_coroutine(pair: Tuple[str, str]):
                filename, url = pair
                # Download the page
                response = await client.get(url)
                response.raise_for_status()

                # Save the page content to the cbz file
                page_content: bytes = await response.read()
                cbz.write(filename, page_content)
                self._progress()

            result = await pool.map(download_coroutine, pair_list)
            raise_on_any_error_from_pool(result)
        cbz.save()
        self.log('\n', end='')

    async def get_pages_urls(self) -> List[HttpUrl]:
        raise NotImplementedError

    async def nexts(self) -> List["Chapter"]:
        # override this to implement the next pull feature
        return []

    async def __aiter__(self) -> AsyncGenerator[Tuple[str, HttpUrl], None]:
        pages = await self.get_pages_urls()
        for index, url in enumerate(pages):
            filename = f'{index:03}.jpg'
            yield filename, url

    def _progress(self) -> None:
        self.log('.', end='')

    def _start_pull(self) -> None:
        self.log(f'{self.name}: ', end='')

    def _no_content(self) -> None:
        self.log('No content')

    def log(self, *args, **kwargs) -> None:
        print(*args, **kwargs)
        sys.stdout.flush()

    def __gt__(self, other: "Chapter") -> bool:
        return self.episode > other.episode

    def __lt__(self, other: "Chapter") -> bool:
        return self.episode < other.episode

    def __eq__(self, other: "Chapter") -> bool:
        return self.episode == other.episode


class ToonManager(QuerySet):
    async def leech(self, pool_size: int = 3) -> None:
        async for toon in self:
            await toon.leech(pool_size)


class WebToonPacked(Document):
    """
    Things to override:
    properties:
    - url
    """
    name: str
    titleno: Optional[int]
    lang: str = Field(max_length=2)
    finsihed: bool = False
    domain: str
    created: datetime = Field(default_factory=datetime.utcnow)
    updated: Optional[datetime] = None
    gender: Optional[str]
    corporate: bool = True
    chapters: List[Chapter] = []
    # inner use, for futures developement.
    version: int = 2

    _quote_cookies: bool = False
    _lowerize_headers: bool = False

    class Mongo:
        manager_class = ToonManager

    def __str__(self):
        return self.name

    @property
    def url(self) -> str:
        raise NotImplementedError

    @property
    def path(self) -> str:
        if not self.corporate:
            return f'/mnt/aiur/Users/snicolet/Scans/Toons/Ero/{self.name}'
        return f'/mnt/aiur/Users/snicolet/Scans/Toons/{self.name}'

    def update_chapters_parent(self) -> None:
        for chapter in self.chapters:
            chapter._parent = self

    async def create_folder(self) -> None:
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    async def save(self, *args, **kwargs):
        self.updated = datetime.utcnow()
        return await super().save(*args, **kwargs)

    async def leech(self, pool_size: int = 3):
        await self.create_folder()
        print(f'--- {self.name} ---')
        # check for missing chapters on local
        for chapter in self.chapters:
            chapter._parent = self
            await chapter.pull(pool_size)

        nexts = await self.chapters[-1].nexts()
        if not nexts:
            return

        self.chapters.extend(nexts)
        for chapter in nexts:
            chapter._parent = self
            await chapter.pull(pool_size)
        await self.save()

    def get_headers(self) -> Dict[str, str]:
        headers = {
            'Referer': self.url,
            'User-Agent': FIREFOX,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'max-age=0'
        }
        if getattr(self, '_lowerize_headers', False):
            headers = dict({k.lower(): v for k, v in headers.items()})
        return headers

    def get_cookies(self) -> Dict[str, str]:
        return {}

    @asynccontextmanager
    async def get_client(self):
        session = aiohttp.ClientSession(
            headers=self.get_headers(),
            cookie_jar=self.get_cookie_jar(),
        )
        async with session as client:
            yield client

    async def parse_url(self, url: str) -> BeautifulSoup:
        async with self.get_client() as client:
            request = client.get(url)
            async with request as response:
                response.raise_for_status()
                page_content = await response.read()
        page = BeautifulSoup(page_content, 'lxml')
        return page

    def get_cookie_jar(self) -> aiohttp.CookieJar:
        loop = aiohttp.helpers.get_running_loop()
        jar = aiohttp.CookieJar(loop=loop, unsafe=True, quote_cookie=self._quote_cookies)
        cookies: Optional[Dict] = self.get_cookies()
        if cookies is not None:
            jar.update_cookies(cookies)
        return jar
