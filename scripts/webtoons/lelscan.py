from datetime import datetime
import bs4 as BeautifulSoup
from typing import List, Optional

from motorized import Document, QuerySet
from pydantic import Field
from toonbase import AsyncToon, ToonNotAvailableError
import aiohttp
import asyncio


class LelScanManager(QuerySet):
    def from_name(self, name: str, episode: int = 1) -> 'LelScan':
        instance = LelScan(
            lang='fr',
            name=name,
            episode=episode
        )
        return instance

    async def chapters(self, name: str) -> List[str]:
        url = f'https://lelscan-vf.co/manga/{name}'
        async with aiohttp.request('get', url, headers={'Referer': url}) as response:
            response.raise_for_status()
            page_content = await response.read()
        page = BeautifulSoup.BeautifulSoup(page_content, 'lxml')
        h5s = page.find_all('h5', {'class': 'chapter-title-rtl'})
        chapters = [h5.find('a')['href'].split('/')[-1] for h5 in h5s]
        return chapters


class LelScan(AsyncToon):
    name: str
    episode: str
    domain: str = 'https://lelscan-vf.co'
    created: datetime = Field(default_factory=datetime.now)

    class Mongo:
        manager_class = LelScanManager
        local_fields = ('page_content',)

    @property
    def url(self) -> str:
        return f'https://lelscan-vf.co/manga/{self.name}/{self.episode}'

    async def pages(self) -> List[str]:
        try:
            soup = BeautifulSoup.BeautifulSoup(await self.get_page_content(), 'lxml')
        except aiohttp.ClientResponseError as response_error:
            # with lelscan if the pages does not exists the server returns a 500 instead of a 404
            if response_error.status == 500:
                raise ToonNotAvailableError from response_error
            raise response_error
        parent = soup.find('div', id='all')
        try:
            urls = [img['data-src'] for img in parent.find_all('img')]
        except AttributeError as error:
            raise ToonNotAvailableError from error

        def fix_url(url: str) -> str:
            return ('https://lelscan-vf.co/' + '/'.join(url.split('/', 3)[3:])).strip()

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

    for chapter in chapters:
        instance = LelScan(
            domain='https://lelscan-vf.co',
            lang='fr',
            name=name,
            episode=chapter
        )
        if not instance.exists():
            try:
                await instance.pull(pool_size=8)
            except ToonNotAvailableError:
                await instance.log('Not available', end='\n')


async def main():
    subs = [
        'bijin-onna-joushi-takizawasan',
        'boku-no-kanojo-sensei',
        'bug-player',
        'dandadan',
        'dragon-ball-super',
        'i-picked-up-a-demon-lord-as-a-maid',
        'my-harem-grew-so-large-i-was-forced-to-ascend',
        'my-wife-is-a-man',
        'nana-to-kaoru-kokosei-no-sm-gokko',
        'nana-to-kaoru-last-year',
        'one-piece',
        'one-punch-man',
        'otherworldly-sword-kings-survival-records',
        'samayoeru-tenseishatachi-no-revival-game',
        'sentouin-haken-shimasu',
        'shinigami-bocchan-to-kuro-maid',
        'solo-leveling',
        'time-stop-brave',
        'touch-on',
    ]

    for scan_name in subs:
        await get_from_chapters(scan_name)


if __name__ == "__main__":
    asyncio.run(main())
