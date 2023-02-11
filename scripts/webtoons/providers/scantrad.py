import aiohttp
import bs4
from toonbase import AsyncToon, ToonManager, SoupMixin, UserAgent
from typing import List


class ScanTradManager(ToonManager):
    async def chapters(self, name: str, **kwargs) -> List["ScanTrad"]:
        url = f'https://manga-scantrad.net/manga/{name}/'
        headers = {
            'Referer': 'https://manga-scantrad.net/manga/',
            'UserAgent': UserAgent.FIREFOX.value,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate'
        }
        async with aiohttp.request('get', url, headers=headers) as response:
            response.raise_for_status()
            page_content = await response.read()

        page = bs4.BeautifulSoup(page_content, 'lxml')
        h5s = page.find_all('h5', {'class': 'chapter-title-rtl'})
        chapters = [h5.find('a')['href'].split('/')[-1] for h5 in h5s]

        return chapters


class ScanTrad(SoupMixin, AsyncToon):
    class Mongo:
        manager_class = ScanTradManager
