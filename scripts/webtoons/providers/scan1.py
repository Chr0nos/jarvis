import re
from typing import List, Optional
from motorized import mark_parents, Q
from newtoon import Chapter, WebToonPacked, ToonManager
import ssl


class ScanOneChapter(Chapter):
    episode: float
    key_name: str

    @property
    def url(self):
        return f'{self._parent.url}/{self.key_name}'

    async def get_pages_urls(self) -> List[str]:
        page = await self._parent.parse_url(self.url)
        try:
            imgs = page \
                .find('div', class_='viewer-cnt') \
                .find('div', {'id': 'all'}) \
                .find_all('img')

            return list([img['data-src'].strip() for img in imgs])
        # Some chapters have no urls at all and are just broken on the website side
        except AttributeError:
            return []

    async def nexts(self) -> List["ScanOneChapter"]:
        instance = await self._parent.from_url(self._parent.url)
        return list(filter(lambda chapter: chapter > self, instance.chapters))


class ScanOne(WebToonPacked):
    domain: str = 'scan-1.com'
    lang: str = 'fr'
    chapters: List[ScanOneChapter] = []

    class Mongo:
        collection = 'webtoonpackeds'
        filters = Q(domain='scan-1.com')
        manager_class = ToonManager

    @property
    def url(self) -> str:
        return f'https://wwv.scan-1.com/{self.name}'

    @classmethod
    async def from_url(cls, url: str) -> Optional["ScanOne"]:
        rule = re.compile('https://wwv.scan-1.com/([\w-]+)')
        match = rule.match(url)
        if not match:
            return None
        instance = cls(name=match.groups()[0])
        page = await instance.parse_url(url)
        chapters_lis = page.find('ul', class_='chapters').find_all('li')

        def unpack_li(index: int, li) -> ScanOneChapter:
            link = li.find('a')
            return ScanOneChapter(
                name=link.text.replace(instance.name, '').strip(),
                episode=index,
                key_name=link['href'].split('/')[-1]
            )

        instance.chapters = list([
            unpack_li(index, li)
            for index, li in enumerate(chapters_lis[::-1], start=1)
        ])
        mark_parents(instance)
        return instance

    @classmethod
    async def from_name(cls, name: str) -> Optional["ScanOne"]:
        return await cls.from_url(f'https://wwv.scan-1.com/{name}')
