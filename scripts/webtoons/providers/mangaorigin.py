import re
from toonbase import AsyncToon, ToonManager, UserAgent


class MangaOriginmManager(ToonManager):
    def from_url(self, url: str):
        m = re.compile(r"^https://mangas-origines.fr/manga/([\w-]+)/([\w-]+)/")
        name, chapter = m.match(url).groups()
        return self.model(name=name, episode=chapter)


class MangaOriginToon(AsyncToon):
    domain: str = 'mangas-origines.fr'
    lang: str = 'fr'
    episode: str

    class Mongo:
        manager_class = MangaOriginmManager

    @property
    def url(self) -> str:
        # return 'https://mangas-origines.fr/manga/martial-peak/'
        return f'https://{self.domain}/manga/{self.name}/{self.chapter}/'

    @property
    def chapter(self) -> str:
        return self.episode

    def get_cookies(self):
        return {
            'wpmanga-reading-history': 'W3siaWQiOjI2MTAsImMiOiIyNDMwOCIsInAiOjEsImkiOiIiLCJ0IjoxNjM0ODQxNTEwfV0%3D; _ga=GA1.1.739239683.1634834303; _gid=GA1.2.299007645.1634834303; _ga_DPGCMVGV83=GS1.1.1634834303.1.1.1634834309.0; __cf_bm=VigKFFe.ibJTl2LJG90Im1PPjHc5Mgq0VEuNLwsrKKE-1634834304-0-AcpWsVVTkZQRvHCBMZhGq0G4vFTcz854FvsVRB5WFtAc0D18VKmsMwKRz5ewNysP8cYkes0wBcq5+67tImZzW5bsqI5gBcpWPRhdBBAAowrqfYvzfjrumuXMK2oHiTCJyw==',
            'pum-23148': 'true'
        }

    def get_headers(self):
        headers = super().get_headers()
        headers.update({
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })
        return headers
