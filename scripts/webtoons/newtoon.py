import os
import re
import sys
from textwrap import wrap
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union, Type

import asyncio
import aiohttp
from asyncio_pool import AioPool
from bs4 import BeautifulSoup
from motorized import (Document, EmbeddedDocument, Field, PrivatesAttrsMixin,
                       QuerySet, Q)
from pydantic import HttpUrl, validator
from selenium import webdriver
import undetected_chromedriver as uc
from functools import wraps


FIREFOX = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'
CHROME_LINUX = 'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
CHROME = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'


def raise_on_any_error_from_pool(pool_result: List[Optional[Exception]]):
    errors = list(filter(None, pool_result))
    for error in errors:
        raise error


def retry(count: int, *exceptions: List[Type[Exception]], delay: int = 0):
    def wrapper(func):
        @wraps(func)
        async def decorator(*args, **kwargs):
            for retry_index in range(count + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as error:
                    if type(error) in exceptions:
                        if delay:
                            await asyncio.sleep(delay)
                        continue
        return decorator
    return wrapper


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
    _driver: Optional[Union[webdriver.Firefox, webdriver.Chrome]] = None
    _headless: bool = True

    @classmethod
    def get_new_marionette(cls, headless: bool = False) -> uc.Chrome:
        print('Requesting a new marionette')
        options = uc.ChromeOptions()
        if headless:
            options.headless = True
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
        driver = uc.Chrome(options=options)
        print('Got new marionette.')
        return driver

    @property
    def driver(self) -> Union[webdriver.Firefox, webdriver.Chrome]:
        if not self._driver:
            # self._driver = webdriver.Firefox()
            # self._driver = webdriver.Chrome()
            self._driver = self.get_new_marionette(self._headless)
        return self._driver

    async def parse_url(self, url: str, delay: int = 0) -> BeautifulSoup:
        """The `delay` parameter wait for the page to load/execute the scripts
        in the marionette, some websites require that otherwise the JS don't
        have the time to populate divs/lists.
        """
        if self.url != self.driver.current_url:
            self.driver.get(url)
        if delay:
            await asyncio.sleep(delay)
        return BeautifulSoup(self.driver.page_source, 'lxml')

    async def parse_cloudflare_url(self, url: str, delay: int = 0) -> BeautifulSoup:
        self.driver.get(url)
        for index in range(20):
            await asyncio.sleep(delay)
            page = BeautifulSoup(self.driver.page_source, 'lxml')
            # print(f'{index:02}: {self.driver.current_url}', x)
            challenge_form = page.find('form', {'class': 'challenge-form'})
            if not challenge_form:
                return page
            await asyncio.sleep(8)

    async def post_cloudflare_challenge(self, page: BeautifulSoup) -> None:
        challenge_form = page.find('form', {'class': 'challenge-form'})
        challenge_link = challenge_form['action']
        challenge_inputs = challenge_form.find_all('input')
        payload = dict({
            field['name']: field['value'] for field in challenge_inputs if field.get('value', None)
        })
        cookies = self.driver.get_cookies()
        print('POST', challenge_link, payload, cookies)


class LocalStorage:
    """Allow to access to the local storage of the marionette from python.
    """
    def __init__(self, driver: uc.Chrome) :
        self.driver = driver

    def __len__(self):
        return self.driver.execute_script("return window.localStorage.length;")

    def items(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, items = {}; " \
            "for (var i = 0, k; i < ls.length; ++i) " \
            "  items[k = ls.key(i)] = ls.getItem(k); " \
            "return items; ")

    def keys(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, keys = []; " \
            "for (var i = 0; i < ls.length; ++i) " \
            "  keys[i] = ls.key(i); " \
            "return keys; ")

    def get(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)

    def set(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def has(self, key):
        return key in self.keys()

    def remove(self, key):
        self.driver.execute_script("window.localStorage.removeItem(arguments[0]);", key)


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

    @validator('name', pre=True)
    def validate_name(cls, value: str) -> str:
        try:
            return value \
                .replace('"', "") \
                .replace('/', '') \
                .replace('*','') \
                .replace('&amp;', '&') \
                .replace('&#39;', '\'')
        except Exception:
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
        get_chapters_func = getattr(self._parent, 'get_chapters_from_website')
        if not get_chapters_func:
            return []
        chapters = await get_chapters_func()
        return list(filter(lambda chapter: chapter > self, chapters))

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
    async def leech(self, pool_size: int = 3, driver: Optional[uc.Chrome] = None) -> None:
        # we want to iterate over all toons that are not explictly finished.
        async for toon in self.filter(Q(finished=False) | Q(finished__exists=False)):
            # if this can have a driver
            if isinstance(toon, SeleniumMixin):
                # and the driver in toon is set but not in global, we set it
                if toon._driver and not driver:
                    driver = toon._driver
                # otherwise if we have a driver but not the toon, set set it
                elif driver:
                    toon._driver = driver
            await toon.leech(pool_size)

    async def drop(self):
        # prevent droping the whole table, just drop the current filtering
        await self.delete()


class WebToonPacked(Document):
    """
    Things to override:
    properties:
    - url
    """
    name: str
    lang: str = Field(max_length=2)
    finished: bool = False
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

        if not self.chapters:
            return
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
