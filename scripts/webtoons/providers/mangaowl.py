import re
import os
from typing import Optional, List, Literal
from typing_extensions import Literal
from motorized import mark_parents, Q
from newtoon import Chapter, WebToonPacked, SeleniumMixin, ToonManager


class MangaOwlChapter(Chapter):
    id: int

    @property
    def url(self) -> str:
        tr = self._parent.driver.execute_script('return tr;')
        s = self._parent.driver.execute_script('return encodeURIComponent(btoa(document.location.origin));')
        user = 0
        return f'https://r.mangaowls.com/reader/{self._parent.code}/{self.id}/{user}?tr={tr}&s={s}'

    async def get_pages_urls(self) -> List[str]:
        await self._parent.parse_url(self._parent.url)
        page = await self._parent.parse_cloudflare_url(self.url, delay=3)
        # print(page)
        reader = page.find('div', {'id': 'reader'})
        return list([img['data-src'] for img in reader.find_all('img', {'class': 'owl-lazy'})])

    @property
    def cbz_path(self) -> str:
        name = getattr(self, self._parent.chapters_naming)
        return os.path.join(self._parent.path, f'{name}.cbz')


class MangaOwl(SeleniumMixin, WebToonPacked):
    domain: str = 'mangaowl.net'
    lang: str = 'en'
    code: int
    corporate: bool = False
    chapters: List[MangaOwlChapter] = []
    chapters_naming: Literal["name", "episode"] = "name"

    class Mongo:
        collection = 'webtoonpackeds'
        filters = Q(domain='mangaowl.net')
        manager_class = ToonManager

    @property
    def url(self) -> str:
        return f'https://mangaowl.net/single/{self.code}/{self.name}'

    @classmethod
    async def from_url(cls, url: str) -> Optional["MangaOwl"]:
        rule = re.compile(r'https://mangaowl.net/single/(\d+)/([\w-]+)')
        match = rule.match(url)
        if not match:
            return None
        code, name = match.groups()
        instance = cls(name=name, code=code)
        instance.chapters = await instance.get_chapters_from_website()
        return instance

    async def get_chapters_from_website(self) -> List[MangaOwlChapter]:
        # print(self.url)
        page = await self.parse_cloudflare_url(self.url)
        chapters_div = page.find('div', {'class': 'table table-chapter-list'})

        def unwrap_li(index:int, li) -> MangaOwlChapter:
            chapter = MangaOwlChapter(
                id=li.find('input')['chapter-id'],
                name=li.find('label').text.strip(),
                episode=index,
            )
            chapter._parent = self
            return chapter

        return list([
            unwrap_li(index, li)
            for index, li in enumerate(chapters_div.find_all('li')[::-1])
        ])

    def rename_chapters(self) -> None:
        root_path = self.path
        for chapter in self.chapters:
            chapter._parent = self
            name_path = root_path + f'/{chapter.name}.cbz'
            new_name = chapter.cbz_path
            if os.path.exists(name_path) and name_path != new_name:
                print(f'Renaming {name_path} to {new_name}')
                os.rename(name_path, new_name)
