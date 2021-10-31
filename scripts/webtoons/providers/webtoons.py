#!./venv/bin/python
import os

import re
from typing import Generator, Optional, Any
import aiohttp
import bs4 as BeautifulSoup

from toonbase import ToonBaseUrlInvalidError, AsyncToon, ToonManager, SoupMixin, provide_soup
from motorized import Document, QuerySet, Q


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

    async def leech(self) -> None:
        async for toon in self.filter(finished=False).lasts():
            await toon.leech()


class WebToon(SoupMixin, AsyncToon):
    titleno: int
    gender: str
    chapter: str
    lang: str
    domain:str = 'webtoons.com'

    class Mongo:
        manager_class = ToonManager
        collection = 'toons'
        filters = Q(domain__in=['webtoons.com', 'webtoon.com'])

    def get_cookies(self):
        return {
            'needGDPR': 'false',
            'needCCPA': 'false',
            'needCOPPA': 'false',
            'ageGatePass': 'true',
            'allowedCookie': 'ga',
            'contentLanguage': self.lang,
            'locale': self.lang,
            'countryCode': self.lang.upper() if self.lang != 'en' else 'US'
        }

    @property
    def cbz_path(self):
        if not self.chapter or not self.path:
            return None
        return os.path.join(self.path, f'{self.chapter}.cbz')

    @property
    def url(self):
        return ''.join(
            f'https://www.webtoons.com/{self.lang}/{self.gender}/{self.name}/'
            f'{self.chapter}/viewer?title_no={self.titleno}'
            f'&episode_no={self.episode}'
        )

    async def index(self, soup: BeautifulSoup.BeautifulSoup):
        for img in self._soup.find_all('img', class_="_images"):
            url = img['data-url']
            if 'jpg' not in url and 'JPG' not in url and 'png' not in url:
                # print('i', url)
                continue
            yield url

    @provide_soup
    async def get_pages(self, soup: BeautifulSoup.BeautifulSoup):
        return list([url async for url in self.index(soup)])

    @provide_soup
    async def get_next(self, soup: BeautifulSoup.BeautifulSoup) -> Optional["WebToon"]:
        try:
            next_page = self._soup.find_all("a", class_='pg_next')[0].get('href')
            return WebToon.objects.from_url(next_page)
        except (AttributeError, ToonBaseUrlInvalidError):
            return None


async def pullall():
    async for toon in WebToon.objects.filter(finished=False).lasts():
        await toon.leech()
