#!./venv/bin/python
import os

import re
from typing import Generator, Optional, Any
import bs4 as BeautifulSoup

from toonbase import ToonBaseUrlInvalidError, AsyncToon, ToonManager
from motorized import Document, QuerySet


class ToonManager(ToonManager):
    lasts_ordering_selector = ['-episode', '-chapter']

    def from_url(self, url: str):
        # print('parsing ', url)
        r = re.compile(r'^https:\/\/([\w\.]+)\/(en|fr)\/([\w-]+)\/([\w-]+)\/([\w-]+)\/viewer\?title_no=(\d+)&episode_no=(\d+)')
        m = r.match(url)
        if not m:
            raise ToonBaseUrlInvalidError(url)
        site, lang, gender_name, name, episode, title_no, episode_no = m.groups()
        toon = self.model(
            name=name,
            episode=int(episode_no),
            chapter=episode,
            titleno=int(title_no),
            gender=gender_name,
            lang=lang,
            domain='webtoon.com'
        )
        return toon

    async def last(self, name: str) -> Optional['Document']:
        return await self.filter(name=name).sort(["name", '-created', '-chapter']).first()



class WebToon(AsyncToon):
    titleno: int
    gender: str
    chapter: str
    lang: str

    _soup: Optional[BeautifulSoup.BeautifulSoup] = None

    class Mongo:
        manager_class = ToonManager
        collection = 'mongotoon'

    def get_cookies(self):
        return {
            'needGDPR': 'false',
            'ageGatePass': 'true',
            'allowedCookie': 'ga',
            'contentLanguage': 'en',
            'locale': 'en',
            'countryCode': 'US'
        }

    def get_headers(self):
        return {
            'Referer': 'www.webtoons.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/61.0.3112.113 Safari/537.36',
        }

    @property
    def cbz_path(self):
        if not self.chapter or not self.path:
            return None
        return os.path.join(self.path, f'{self.chapter}.cbz')

    @property
    def url(self):
        return ''.join(
            f'https://webtoons.com/en/{self.gender}/{self.name}/'
            f'{self.chapter}/viewer?title_no={self.titleno}'
            f'&episode_no={self.episode}'
        )

    async def index(self):
        if not self._soup:
            await self.get_soup()
        for img in self._soup.find_all('img', class_="_images"):
            url = img['data-url']
            if 'jpg' not in url and 'JPG' not in url and 'png' not in url:
                # print('i', url)
                continue
            yield url

    async def pages(self):
        return list([url async for url in self.index()])

    async def get_soup(self):
        page = await self.get_page_content()
        self._soup = BeautifulSoup.BeautifulSoup(page.decode(), 'lxml')
        return self._soup

    async def get_next(self) -> Optional["WebToon"]:
        if not self._soup:
            await self.get_soup()
        try:
            next_page = self._soup.find_all("a", class_='pg_next')[0].get('href')
            return WebToon.objects.from_url(next_page)
        except (AttributeError, ToonBaseUrlInvalidError):
            return None


async def pullall():
    async for toon in WebToon.objects.filter(finished=False).lasts():
        await toon.leech()
