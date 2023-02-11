from typing import List, Optional
from newtoon import Chapter, WebToonPacked,  ToonManager
from motorized import Q
import re


class ManhwaChapter(Chapter):
    @property
    def url(self) -> str:
        return f'{self._parent.url}{self.name}/'

    @classmethod
    def from_url(cls, url: str, index: int) -> Optional["ManhwaChapter"]:
        rule = re.compile(r'^https://www.69manhwa.com/manga/.+/([\w-]+)/$')
        match = rule.match(url)
        if not match:
            return None
        name = match.groups(0)[0]
        return cls(name=name, episode=index)

    async def get_pages_urls(self) -> List[str]:
        page = await self._parent.parse_url(self.url)
        reader = page.find('div', {'class': 'reading-content'})
        return [img['data-src'].strip() for img in reader.find_all('img')]


class Manhwa(WebToonPacked):
    domain: str = '69manhwa.com'
    lang: str = 'en'
    chapters: List[ManhwaChapter] = []
    reversed: bool = False
    corporate: bool = False

    class Mongo:
        collection = 'webtoonpackeds'
        filters = Q(domain='69manhwa.com')
        manager_class = ToonManager

    @property
    def url(self) -> str:
        return f'https://www.69manhwa.com/manga/{self.name}/'

    async def get_chapters_from_website(self) -> List[ManhwaChapter]:
        chapters_url = f'https://www.69manhwa.com/manga/{self.name}/ajax/chapters/'
        page = await self.parse_url(chapters_url, 'post')
        links = page.find_all('a')
        chapters_urls = list([link['href'] for link in links])
        if self.reversed:
            chapters_urls = chapters_urls[::-1]
        return list(filter(None, [
            ManhwaChapter.from_url(url, index) for index, url
            in enumerate(chapters_urls, start=1)
        ]))
