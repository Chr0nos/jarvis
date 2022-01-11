from newtoon import Chapter, WebToonPacked, SeleniumMixin
from motorized import Q
from typing import Optional, List
import re


class TbateChapter(Chapter):
    episode: float

    @property
    def url(self) -> str:
        return f'{self._parent.url}/{self.name}/'

    @classmethod
    def from_url(cls, url: str) -> Optional["TbateChapter"]:
        rule = re.compile(r'^https://www.thebeginningaftertheend.fr/manga/the-beginning-after-the-end-vf/([\w-]+)/')
        match = rule.match(url)
        if not match:
            return None
        name = match.groups()[0]
        episode = re.compile(r'[a-z\-]+[a-z]+([\d-]+)').match(name).groups()[0]
        if episode.startswith('-'):
            episode = episode[1:]
        episode = episode.replace('-', '.').strip()
        return cls(name=name, episode=float(episode))

    async def get_pages_urls(self):
        page = await self._parent.parse_url(self.url)
        divs = page.find_all('div', class_='page-break no-gaps')
        return list([div.find('img')['data-src'].strip() for div in divs])

    async def nexts(self) -> List["TbateChapter"]:
        return list(filter(lambda chapter: chapter > self, await self._parent.get_chapters_from_website()))


class Tbate(SeleniumMixin, WebToonPacked):
    name: str = 'the-beginning-after-the-end-vf'
    domain: str = 'thebeginningaftertheend.fr'
    lang: str = 'fr'
    chapters: List[TbateChapter] = []

    class Mongo:
        collection = 'webtoonpackeds'
        filters = Q(domain='thebeginningaftertheend.fr')

    @property
    def url(self) -> str:
        return f'https://www.thebeginningaftertheend.fr/manga/{self.name}/'

    async def get_chapters_from_website(self) -> List[TbateChapter]:
        page = await self.parse_url(self.url)
        chapters_ul = page.find('ul', class_='version-chap')
        chapters_lis = chapters_ul.find_all('li')

        links = [li.find('a')['href'] for li in chapters_lis]
        chapters = [TbateChapter.from_url(url) for url in links]
        return list(chapters)[::-1]
