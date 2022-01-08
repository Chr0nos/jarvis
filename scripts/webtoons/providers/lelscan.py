from datetime import datetime
import bs4 as BeautifulSoup
from typing import List, Optional

from motorized import Document, QuerySet, Q
from pydantic import Field
from toonbase import AsyncToon, ToonNotAvailableError, SoupMixin, provide_soup, UserAgent
import aiohttp
import asyncio


class LelScanManager(QuerySet):
    def from_name(self, name: str, episode: int = 1) -> 'LelScan':
        instance = LelScan(name=name, episode=episode)
        return instance

    async def chapters(self, name: str) -> List[str]:
        url = f'https://www.frscan.cc/manga/{name}'
        headers = {
            "Referer": url,
            "User-Agent": UserAgent.FIREFOX.value
        }
        async with aiohttp.request('get', url, headers=headers) as response:
            response.raise_for_status()
            page_content = await response.read()
        page = BeautifulSoup.BeautifulSoup(page_content, 'lxml')
        h5s = page.find_all('h5', {'class': 'chapter-title-rtl'})
        chapters = [h5.find('a')['href'].split('/')[-1] for h5 in h5s]
        return chapters


class LelScan(SoupMixin, AsyncToon):
    name: str
    episode: str
    domain: str = 'lelscan-vf.co'
    created: datetime = Field(default_factory=datetime.now)
    lang: str = "fr"

    class Mongo:
        manager_class = LelScanManager
        collection = 'toons'
        filters = Q(domain='lelscan-vf.co')

    @property
    def url(self) -> str:
        return f'https://www.frscan.cc/manga/{self.name}/{self.episode}'

    @provide_soup
    async def get_pages(self, soup: BeautifulSoup.BeautifulSoup) -> List[str]:
        parent = soup.find('div', id='all')
        try:
            urls = [img['data-src'] for img in parent.find_all('img')]
        except AttributeError as error:
            raise ToonNotAvailableError from error

        def fix_url(url: str) -> str:
            return ('https://www.frscan.cc/' + '/'.join(url.split('/', 3)[3:])).strip()

        return list(fix_url(url) for url in urls)

    def inc(self):
        self.episode += 1
        self.page_content = None
        return self


def sorter(x):
    try:
        return float(x)
    except ValueError:
        return x


async def get_from_chapters(name: str, chapters: Optional[List[str]] = None) -> None:
    chapters: List[str] = await LelScan.objects.chapters(name) if not chapters else chapters
    chapters.sort(key=sorter)

    #print(name, 'chapters', chapters)
    for chapter in chapters:
        instance = LelScan(name=name, episode=chapter)
        if not instance.exists():
            try:
                await instance.pull(pool_size=1)
            except ToonNotAvailableError:
                await instance.log('Not available', end='\n')


async def main():
    subs = [
        #'bijin-onna-joushi-takizawasan',
        #'boku-no-kanojo-sensei',
        # 'bug-player',
        #'dandadan',
        'cross-days',
        'dragon-ball-super',
        #'i-picked-up-a-demon-lord-as-a-maid',
        #'my-harem-grew-so-large-i-was-forced-to-ascend',
        #'my-wife-is-a-man',
        #'nana-to-kaoru-kokosei-no-sm-gokko',
        #'nana-to-kaoru-last-year',
        'girl-and-science',
        # 'one-piece',
        #'one-punch-man',
        #'otherworldly-sword-kings-survival-records',
        #'samayoeru-tenseishatachi-no-revival-game',
        #'sentouin-haken-shimasu',
        #'shinigami-bocchan-to-kuro-maid',
        'solo-leveling',
        'please-put-these-on-takaminesan',
        #'time-stop-brave',
        #'touch-on',
    ]
    for scan_name in subs:
        await get_from_chapters(scan_name)

if __name__ == "__main__":
    asyncio.run(main())
