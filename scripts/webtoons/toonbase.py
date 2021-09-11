import os
import sys

import mongomodel
import requests
from datetime import datetime
from requests.cookies import cookiejar_from_dict
from tempfile import TemporaryDirectory
import zipfile
from asyncio_pool import AioPool
import aiohttp
import aiofile
from typing import Tuple, List


mongomodel.database.connect(host='10.8.1.1')


class ToonBaseUrlInvalidError(Exception):
    pass


class Chdir:
    def __init__(self, path):
        self.dir = path
        self.previous_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.dir)

    def __exit__(self, *_):
        os.chdir(self.previous_dir)


class ToonBase(mongomodel.Document):
    name = mongomodel.StringField()
    created = mongomodel.DateTimeField(default=lambda: datetime.now())
    fetched = mongomodel.BoolField(False)
    last_fetch = mongomodel.DateTimeField(required=False)
    lang = mongomodel.StringField(maxlen=2)
    domain = mongomodel.StringField(maxlen=255)
    episode = mongomodel.IntegerField()
    finished = mongomodel.BoolField(default=lambda: False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.headers = self.get_headers()
        self.session.cookies = cookiejar_from_dict(self.get_cookies())

    def pre_save(self, data, is_new=False):
        self.created = data.get('created')

    def get_cookies(self):
        return {}

    def get_headers(self):
        return {
            'Referer': self.domain,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/61.0.3112.113 Safari/537.36',
        }

    def __repr__(self):
        return f'<Toon {self.name}>'

    @property
    def path(self):
        return f'/mnt/aiur/Users/snicolet/Scans/Toons/{self.name}'

    @property
    def cbz_path(self):
        return f'{self.path}/{self.episode}.cbz'

    def state(self) -> str:
        if self.finished:
            return 'finished'
        if os.path.exists(self.cbz_path):
            return 'fetched'
        return 'ready-for-next-chapter'

    def pages(self):
        return []

    def pull(self):
        if not self.name:
            print('setup a name first !')
            return
        pages = self.pages()
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        print(self.name, self.episode, end=': ')
        if not pages:
            print('no pages')
            return

        with TemporaryDirectory() as tmpd:
            with Chdir(tmpd):
                cbz = zipfile.ZipFile(self.cbz_path, 'w', zipfile.ZIP_DEFLATED)
                for i, url in enumerate(pages):
                    filepath = os.path.join(tmpd, f'{i:03}.jpg')
                    page_response = self.session.get(
                        url, headers={'Referer': self.url})
                    assert page_response.status_code == 200, \
                        page_response.status_code
                    page_data = page_response.content
                    self.check_page_content(page_data)
                    with open(filepath, 'wb') as fp:
                        fp.write(page_data)
                    print('.', end='')
                    sys.stdout.flush()
                    cbz.write(filepath, os.path.basename(filepath))
            cbz.close()
            print('\n', end='')
        self.last_fetch = datetime.now()
        self.fetched = True

    def check_page_content(self, page_data: bytes) -> None:
        """Receive the actual data from the page after the fetch
        this function is here to be overided by custom checks
        """
        pass

    def exists(self):
        return os.path.exists(self.cbz_path)

    def inc(self):
        raise NotImplementedError

    def auth(self, username, password) -> 'ToonBase':
        """Override this method to perform authentication on the scrapped site
        return None if the autentication failed.
        """
        return self

    def leech(self, **kwargs) -> 'ToonBase':
        try:
            while True:
                if not self.exists():
                    self.pull()
                    self.save()
                self.inc(**kwargs)
        except (StopIteration, ToonBaseUrlInvalidError):
            return self

    def rename(self, newname):
        if newname == self.name:
            return
        folder = os.path.join('/', *self.path.split('/')[0:-1])
        new_folder = os.path.join(folder, newname)
        os.rename(self.path, new_folder)
        self.name = newname
        return self.save()


class AsyncToonMixin:
    """Transform the pull & leech methods to be asyncio capables
    """
    async def leech(self, pool_size=3, **kwargs):
        try:
            while True:
                if not self.exists():
                    await self.pull(pool_size=pool_size)
                    self.save()
                # else:
                #     print(f'{self.cbz_path} already exists, skipping')
                self.inc(**kwargs)
        except (StopIteration, ToonBaseUrlInvalidError):
            self.save()
            return self

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
        print(self.name, self.episode, end=': ')
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
                    print('.', end='')
                    sys.stdout.flush()

        pool = AioPool(size=pool_size)
        with TemporaryDirectory() as tmpd:
            with Chdir(tmpd):
                pair_list = (await self.get_page_and_destination_pairs(tmpd))
                cbz = zipfile.ZipFile(self.cbz_path, 'w', zipfile.ZIP_DEFLATED)
                await pool.map(download_coroutine, pair_list)
            print('\n', end='')
        self.last_fetch = datetime.now()
        self.fetched = True

    async def get_page_content(self) -> str:
        """return the source code of the main page and cache it into the `cache_content` attribute
        of this instance.

        raises:
        - asyncio.exceptions.ClientResponseError
        """
        if getattr(self, 'page_content', None):
            return self.page_content
        request = aiohttp.request(
            url=self.url,
            method='get',
            headers=self.get_headers()
        )
        async with request as response:
            response.raise_for_status()
            page_content = await response.read()
        self.page_content = page_content
        return page_content
