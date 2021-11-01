import re
from typing import Optional
from toonbase import AsyncToon, ToonManager, SoupMixin
from motorized import Q


class MangaOriginmManager(ToonManager):
    def from_url(self, url: str) -> "MangaOriginToon":
        m = re.compile(r"^https://mangas-origines.fr/manga/([\w-]+)/([\w-]+)/")
        name, chapter = m.match(url).groups()
        return self.model(name=name, episode=chapter)

    async def leech(self):
        async for toon in self.filter(next=None):
            await toon.leech()


class MangaOriginToon(SoupMixin, AsyncToon):
    domain: str = 'mangas-origines.fr'
    lang: str = 'fr'
    episode: str

    class Mongo:
        manager_class = MangaOriginmManager
        collection = 'toons'
        filters = Q(domain='mangas-origines.fr')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def url(self) -> str:
        return f'https://{self.domain}/manga/{self.name}/{self.chapter}/'

    @property
    def chapter(self) -> str:
        return self.episode

    def get_cookies(self):
        return {
            'wpmanga-reading-history': 'W3siaWQiOjI2MTAsImMiOiIyNDMwOCIsInAiOjEsImkiOiIiLCJ0IjoxNjM0ODU5MTE0fV0=',
            'pum-23148': 'true',
            '_gid': 'GA1.2.299007645.1634834303',
            '_ga_DPGCMVGV83': 'GS1.1.1634899075.3.1.1634899909.0',
            '__gads': 'ID=1d4022007433f892-2274218888cc00e4:T=1634899351:RT=1634899351:S=ALNI_MYQvGe04Kpz4ROOb0FZg0R16ybm_w',
            '__cf_bm': 'WiZRKsB9uV.DmO.WX5RLYExCeGEdRC_km1_47ckErQk-1634899351-0-AVEmc2nWOOxgRNfJVpaBvyiMDy2ql6ZfPV7Slj3hhSLfFUdzdLGZaFKhx/6DEzdt0Htb+9eGYWKdKPnEv1yS8Mm6+Ckzj6OpRCZrdDyioUhlhvqGdh4RVLUKaGH8INVROQ==',
            '_gat': 1,
            '_gat_gtag_UA_177067753_1': 1,
        }

    def get_headers(self):
        headers = super().get_headers()
        headers.update({
            'Connection': 'keep-alive',
            'Host': 'mangas-origines.fr',
            'Accept': '*/*',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'X-Moz': 'prefetch',
        })
        return headers

    async def get_pages(self):
        soup = await self.get_soup()
        reading_content = soup.find('div', 'reading-content')
        images = reading_content.find_all('img')
        return list([img['data-src'].strip() for img in images])

    async def get_next(self) -> Optional["MangaOriginToon"]:
        soup = await self.get_soup()
        try:
            next_url = soup.find('div', {'class': 'nav-next'}).find('a')['href']
            return MangaOriginToon.objects.from_url(next_url)
        except AttributeError:
            return None
