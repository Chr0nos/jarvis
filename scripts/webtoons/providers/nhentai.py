from typing import List, Optional
import bs4 as BeautifulSoup
import asyncio
from toonbase import AsyncToon, SoupMixin, provide_soup
from motorized import Q
import sys
from glob import glob


class NHentaiToon(SoupMixin, AsyncToon):
    name: Optional[str]
    episode: str
    domain: str = 'nhentai.xxx'
    page_content: Optional[str] = None
    _cdn = 'https://cdn.nhentai.xxx'

    class Mongo:
        collection = 'toons'
        filters = Q(domain='nhentai.xxx')

    @property
    def url(self) -> str:
        return f'https://nhentai.net/g/{self.episode}'

    @provide_soup
    async def resolve_name(self, soup: BeautifulSoup.BeautifulSoup) -> str:
        title = soup.find('meta', {'itemprop': 'name'})['content']
        for replacement in (' | ', '~', '|', ':', '?'):
            title = title.replace(replacement, '')
        return title

    @provide_soup
    async def get_pages(self, soup: BeautifulSoup.BeautifulSoup) -> List[str]:
        thumbs_div = soup.find('div', 'thumbs')
        img_find = thumbs_div.find_all('img', {'class': 'lazyload'})

        def thumb_to_img(thumb_url: str) -> str:
            parts = thumb_url.split('/')
            sauce_code = parts[4]
            filename = parts[-1].replace('t', '')
            return f'{self._cdn}/g/{sauce_code}/{filename}'

        imgs = [thumb_to_img(img['data-src']) for img in img_find]
        return imgs

    @property
    def path(self):
        return f'/mnt/aiur/Users/snicolet/Scans/Toons/nhentai'

    @property
    def cbz_path(self):
        if not self.episode:
            return ''
        return f'{self.path}/[{self.episode:6}] {self.name}.cbz'

    async def pull(self, *args, **kwargs):
        if self.exists():
            return
        await super().pull(*args, **kwargs)

    def exists(self):
        return bool(glob(f'{self.path}/?{self.episode:6}]*.cbz'))



async def get_scan(sauce_code: int, name: str = None) -> bool:
    """Perform the download of sauce_code if not present,
    return True is a request has been performed, Flase otherwise
    """
    instance = NHentaiToon(name=name, episode=sauce_code)
    if instance.exists():
        return False
    if not name:
        instance.name = await instance.resolve_name()
    await instance.pull(pool_size=5)
    return True


async def get_scan_list(sauce_list: List[int]) -> None:
    for sauce in sauce_list:
        if await get_scan(sauce):
            await asyncio.sleep(0.2)


if __name__ == "__main__":
    try:
        sauce_list = [int(sauce) for sauce in sys.argv[1:]]
    except (IndexError, ValueError):
        print(f'usage: ./{sys.argv[0]} [sauce_code]')
        sys.exit(1)
    asyncio.run(get_scan_list(sauce_list))
