
#!./venv/bin/python
import re
from typing import Optional, List

from motorized import Q, mark_parents

from newtoon import Chapter, WebToonPacked, ToonManager
from bs4 import BeautifulSoup, ResultSet, element


class WebToonChapter(Chapter):
    episode: int
    key_name: Optional[str]
    _page: Optional[BeautifulSoup] = None

    @property
    def url(self) -> str:
        key_name = self.key_name if self.key_name else self.name
        return f'https://www.webtoons.com/{self._parent.lang}/' \
               f'{self._parent.gender}/{self._parent.name}/{key_name}' \
               f'/viewer?title_no={self._parent.titleno}' \
               f'&episode_no={self.episode}'

    async def get_pages_urls(self):
        page = await self.get_page()
        urls = [img['data-url'] for img in page.find_all('img', class_='_images')]

        def filter_urls(url: str) -> bool:
            return 'jpg' in url or 'JPG' in url or 'png' in url

        self._page = page
        return list(filter(filter_urls, urls))

    def reset(self) -> None:
        self._page = None

    @classmethod
    def from_url(cls, url: str, name: str = None) -> Optional["WebToonChapter"]:
        rule = re.compile(r'^https://www.webtoons.com/(\w+)/([\w-]+)/[\w-]+/([\w-]+)/viewer\?title_no=(\d+)&episode_no=(\d+)')
        match = rule.match(url)
        if not match:
            print(url)
            return None
        lang, gender, episode_name, _, episode_number = match.groups()
        chapter = cls(
            name=name or episode_name,
            key_name=episode_name,
            episode=episode_number
        )
        return chapter

    async def others(self) -> List["WebToonChapter"]:
        page = await self.get_page()
        chapters = page.find('div', class_='episode_cont').find('ul').find_all("li")

        def unwrap_ul(li: element.NavigableString) -> WebToonChapter:
            link = li.find('a')['href']
            pretty_name = li.find('img')['alt']
            chapter = WebToonChapter.from_url(link, pretty_name)
            return chapter

        return list(filter(None, [unwrap_ul(li) for li in chapters]))

    async def get_page(self) -> BeautifulSoup:
        if self._page:
            return self._page
        self._page = await self._parent.parse_url(self.url)
        return self._page

    async def nexts(self) -> List["WebToonChapter"]:
        return list(filter(lambda chapter: chapter > self, await self.others()))


class WebToon(WebToonPacked):
    titleno: int
    chapters: List[WebToonChapter]
    domain: str = 'webtoons.com'

    class Mongo:
        collection = 'webtoonpackeds'
        filters = Q(domain__in=['webtoons.com', 'webtoon.com'])
        manager_class = ToonManager

    @property
    def url(self) -> str:
        return f'https://www.webtoons.com/{self.lang}/{self.gender}/' \
               f'{self.name}/list?title_no={self.titleno}'

    def get_cookies(self):
        return {
            'atGDPR': 'AD_CONSENT',
            'countryCode': self.lang.upper(),
            'needGDPR': 'false',
            'needCCPA': 'false',
            'needCOPPA': 'false',
            'ageGatePass': 'true',
            'allowedCookie': 'ga',
            'pagGDPR': 'true',
            'contentLanguage': self.lang,
            'locale': self.lang,
            'countryCode': self.lang.upper() if self.lang != 'en' else 'US'
        }

    async def get_chapters_from_website(self, page_number: int = 1):
        url = self.url + f'&page={page_number}'
        print(f'Scanning for page {page_number} on {self.name}')
        page = await self.parse_url(url)
        chapters_lis = page.find('ul', id='_listUl').find_all('li')

        def get_chapter_instance_from_li(li: ResultSet) -> Optional[WebToonChapter]:
            url = li.find('a')['href']
            episode_pretty_name = li.find('img')['alt'].strip()
            return WebToonChapter.from_url(url, episode_pretty_name)

        chapters = list([get_chapter_instance_from_li(li) for li in chapters_lis])
        chapters = chapters[::-1]

        # now we need to find the next page
        pagination = page.find('div', class_='paginate').find_all('a')
        index_of_current = None
        for index, item in enumerate(pagination):
            if item['href'] == '#':
                index_of_current = index
                break

        # checking for the stop condition
        next_lefts = len(pagination[index_of_current:])
        if next_lefts == 1:
            return chapters

        next_page_chapters = await self.get_chapters_from_website(page_number + 1)
        return next_page_chapters + chapters

    @classmethod
    async def from_url(cls, url: str) -> Optional["WebToon"]:
        rule = re.compile(r'^https://www\.webtoons\.com/(\w+)/([\w-]+)/([\w-]+)/([\w-]+)/viewer\?title_no=(\d+)&episode_no=(\d+)')
        match = rule.match(url)
        if not match:
            return None
        lang, gender, name, chapter_name, titleno, episode_number = match.groups()
        try:
            return await cls.objects.get(name=name, lang=lang)
        except cls.DocumentNotFound:
            pass
        instance = cls(
            name=name,
            lang=lang,
            gender=gender,
            titleno=titleno,
            chapters=[WebToonChapter(name=chapter_name, episode=episode_number)]
        )
        mark_parents(instance)
        instance.chapters = await instance.chapters[0].others()
        return instance
