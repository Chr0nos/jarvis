import bs4 as BeautifulSoup
import mongomodel
import requests
from typing import List

from toonbase import ToonBase, AsyncToonMixin
import asyncio


class LelScan(AsyncToonMixin, ToonBase):
    @property
    def url(self) -> str:
        return f'https://lelscan-vf.co/manga/{self.name}/{self.episode}'

    async def pages(self) -> List[str]:
        soup = BeautifulSoup.BeautifulSoup(await self.get_page_content(), 'lxml')
        parent = soup.find('div', id='all')
        urls = [img['data-src'] for img in parent.find_all('img')]

        def fix_url(url: str) -> str:
            return ('https://lelscan-vf.co/' + '/'.join(url.split('/', 3)[3:])).strip()

        return list(fix_url(url) for url in urls)

    def inc(self):
        self.episode += 1
        self.page_content = None
        return self

    def save(self) -> None:
        # don't save it for now...
        pass


async def get_scan(name: str, episode: int = 1) -> None:
    instance = LelScan(
        domain='https://lelscan-vf.co',
        lang='fr',
        name=name,
        episode=episode
    )
    try:
        await instance.leech(pool_size=8)
    except AttributeError:
        print('Unavailable')


async def main():
    subs = [
        'shinigami-bocchan-to-kuro-maid',
        'my-wife-is-a-man',
        'nana-to-kaoru-kokosei-no-sm-gokko',
        'nana-to-kaoru-last-year',
        'touch-on',
        'boku-no-kanojo-sensei',
        'bijin-onna-joushi-takizawasan',
        'otherworldly-sword-kings-survival-records',
        {'name': 'one-punch-man', 'episode': 4},
        {'name': 'one-piece', 'episode': 389},
        {'name': 'samayoeru-tenseishatachi-no-revival-game', 'episode': 2}
    ]

    for scan_name in subs:
        if isinstance(scan_name, dict):
            await get_scan(**scan_name)
        else:
            await get_scan(scan_name)


if __name__ == "__main__":
    asyncio.run(main())
