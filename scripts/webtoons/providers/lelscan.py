from typing import List, Optional

from motorized import Document, QuerySet, Q, mark_parents
from newtoon import Chapter, WebToonPacked, ToonManager


class LelScanChapter(Chapter):
    episode: float

    @property
    def url(self):
        try:
            episode = int(self.episode)
        except ValueError:
            episode = self.episode
        return f'{self._parent.url}/{episode}'

    async def get_pages_urls(self) -> List[str]:
        page = await self._parent.parse_url(self.url)

        def fix_url(url: str) -> str:
            return ('https://www.lelscan-vf.cc/' + '/'.join(url.split('/', 3)[3:])).strip()

        return list([
            fix_url(img['data-src']) for img
            in page.find('div', {'id': 'all'}).find_all('img')
        ])

    async def nexts(self) -> List["LelScanChapter"]:
        instance = await self._parent.from_name(self._parent.name)
        chapters = list(filter(lambda chapter: chapter > self, instance.chapters))
        mark_parents(instance, self)
        return chapters


class LelScan(WebToonPacked):
    domain: str = 'lelscan-vf.co'
    lang: str = 'fr'
    chapters: List[LelScanChapter] = []

    class Mongo:
        manager_class = ToonManager
        collection = 'webtoonpackeds'
        filters = Q(domain='lelscan-vf.co')

    @property
    def url(self) -> str:
        return f'https://www.lelscan-vf.cc/manga/{self.name}'

    async def discover_chapters(self) -> List[LelScanChapter]:
        page = await self.parse_url(self.url)
        h5s = page.find_all('h5', {'class': 'chapter-title-rtl'})

        def unwrap_h5(h5) -> Optional[LelScanChapter]:
            link = h5.find('a')['href']
            title = h5.find('em').text.strip()
            episode = link.split('/')[-1]
            try:
                episode = int(episode)
            except ValueError:
                episode = float(episode)

            return LelScanChapter(
                name=f'{episode} - {title}' if title else f'{episode}',
                episode=episode,
            )

        return list(filter(None, [unwrap_h5(h5) for h5 in h5s[::-1]]))

    @classmethod
    async def from_name(cls, name: str):
        instance = cls(name=name)
        instance.chapters = await instance.discover_chapters()
        mark_parents(instance)
        return instance
