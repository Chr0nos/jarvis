import re
from typing import Optional, List
from motorized import Q
from newtoon import Chapter, WebToonPacked, ToonManager


class MangaScanChapter(Chapter):
    episode: int

    @classmethod
    def from_url(cls, url: str) -> Optional["MangaScanChapter"]:
        rule = re.compile(r'^https://mangascan.cc/manga/([\w-]+)/(\d+)$')
        match = rule.match(url)
        if not match:
            return None
        _, episode = match.groups()
        chapter = cls(name=f'chapitre-{episode}', episode=episode)
        return chapter

    @property
    def url(self) -> str:
        return f'{self._parent.url}/{self.episode}'

    async def get_pages_urls(self) ->  List[str]:
        page = await self._parent.parse_url(self.url)
        all = page.find('div', {'id': 'all'})
        return list([img['data-src'] for img in all.find_all('img')])


class MangaScan(WebToonPacked):
    lang: str = 'fr'
    domain: str = 'mangascan.cc'
    chapters: List[MangaScanChapter] = []

    class Mongo:
        collection = 'webtoonpackeds'
        filters = Q(domain='mangascan.cc')
        manager_class = ToonManager

    @property
    def url(self) -> str:
        return f'http://{self.domain}/manga/{self.name}'

    async def get_chapters_from_website(self) -> List[MangaScanChapter]:
        page = await self.parse_url(self.url)
        chapters_ul = page.find('ul', class_='chapters')
        chapters_lis = chapters_ul.find_all('li')
        links = [li.find('a')['href'] for li in chapters_lis]
        chapters = [MangaScanChapter.from_url(url) for url in links]
        return list(filter(None, chapters))[::-1]
