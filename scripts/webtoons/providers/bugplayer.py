from typing import List, Optional
from pydantic import Field
from motorized import Q, mark_parents
from newtoon import Chapter, WebToonPacked, ToonManager, SeleniumMixin
from undetected_chromedriver import Chrome


class BugPlayerChapter(Chapter):
    key_name: str = Field(min_length=1)

    @property
    def url(self) -> str:
        return f'https://bug-player.com/manga/{self.key_name}/'

    async def get_pages_urls(self) -> List[str]:
        page = await self._parent.parse_url(self.url)
        divs = page \
            .find('div', {'class': 'entry-content'}) \
            .find_all('div', {'class': 'separator'})

        def unwrap_link(link) -> Optional[str]:
            return link['href'] if link else None

        return list(filter(None, [unwrap_link(div.find('a')) for div in divs]))

    async def nexts(self) -> List["BugPlayerChapter"]:
        instance = await self._parent.from_scratch()
        return list(filter(lambda chapter: chapter > self, instance.chapters))


class BugPlayer(SeleniumMixin, WebToonPacked):
    name: str = 'bug-player'
    domain: str = 'bug-player.com'
    lang: str = 'en'

    class Mongo:
        filters = Q(domain='bug-player.com')
        collection = 'webtoonpackeds'
        manager_class = ToonManager

    @property
    def url(self):
        return 'https://bug-player.com/'

    async def get_chapters(self) -> List[BugPlayerChapter]:
        page = await self.parse_url(self.url)
        chapter_div = page.find('div', {'id': 'Chapters_List'})
        lis = chapter_div.find_all('li')

        def unwrap_li(index: int, li):
            link = li.find('a')
            return BugPlayerChapter(
                name=f'chapter-{index:03}',
                episode=index,
                key_name=link['href'].split('/')[-2].strip(),
            )

        return list([
            unwrap_li(index, li) for index, li in
            enumerate(lis[::-1], start=1)
        ])

    @classmethod
    async def from_scratch(cls, driver: Optional[Chrome] = None):
        instance = cls()
        instance._driver = driver
        instance.chapters = await instance.get_chapters()
        mark_parents(instance)
        return instance
