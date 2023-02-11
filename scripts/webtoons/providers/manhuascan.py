from typing import List, Optional
from newtoon import Chapter, WebToonPacked,  SeleniumMixin

# INFO POUR MOI, tu peux supprimer ca, le site est relou
# et a une protection cloudflare qui te renvois de la 404 meme si la page
# existe bel et bien, une sombre histoire de headers...

class ManHuaScanChapter(Chapter):
    key: str

    @property
    def url(self) -> str:
        return self._parent.base_url + '/' + self.key


class ManHuaScan(SeleniumMixin, WebToonPacked):
    lang: str = 'en'
    domain: str = 'manhuascan.me'
    chapters: List[ManHuaScanChapter] = []
    corporate: bool = True

    @property
    def base_url(self) -> str:
        return f'https://{self.domain}/{self.name}'

    @property
    def url(self) -> str:
        return f'{self.base_url}.html'

    async def get_chapters_from_website(self) -> List[ManHuaScanChapter]:
        page = await self.parse_cloudflare_url(self.url)
        chapters_div = page.find('div', {'id': 'list-chapters'})
        links_a = chapters_div.find_all('a', {'class': 'chapter'})

        chapters = [
            ManHuaScanChapter(
                name=a.find('b').text,
                episode=index,
                key=a['href']
            )
            for index, a in enumerate(links_a)
        ]
        return chapters
