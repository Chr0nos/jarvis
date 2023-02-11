import re
import os
from typing import Optional, List, Literal
from typing_extensions import Literal
from motorized import mark_parents, Q
from newtoon import Chapter, WebToonPacked, SeleniumMixin, ToonManager, LocalStorage, error_handler
from selenium.common import exceptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from undetected_chromedriver import Chrome
from time import sleep
from aiohttp.client_exceptions import ClientResponseError


class MangaOwlChapter(Chapter):
    id: int

    @property
    def url(self) -> str:
        # tr = self._parent.driver.execute_script('return tr;')
        # s = self._parent.driver.execute_script('return encodeURIComponent(btoa(document.location.origin));')
        # user = 0
        # return f'https://r.mangaowls.com/reader/{self._parent.code}/{self.id}/{user}?tr={tr}&s={s}'
        self.click()
        url: str = self._parent.driver.current_url
        return url

    async def get_page_content(self, retries=10):
        for _ in range(0, retries):
            page = await self._parent.parse_cloudflare_url(self.url, delay=3)
            if 'mangaowl' in self._parent.driver.current_url:
                return page
        raise Exception('cannot enforce self url' + self._parent.driver.current_url)

    async def get_pages_urls(self) -> List[str]:
        await self._parent.parse_url(self._parent.url)

        page = await self.get_page_content()
        reader = page.find('div', {'id': 'reader'})
        return list([img['data-src'] for img in reader.find_all('img', {'class': 'owl-lazy'})])

    @property
    def cbz_path(self) -> str:
        name = getattr(self, self._parent.chapters_naming)
        return os.path.join(self._parent.path, f'{name}.cbz')

    def click(self) -> None:
        driver: Chrome = self._parent.driver

        # avoid the "adult content" warning
        storage = LocalStorage(driver)
        storage.set('mgo_warning', 'true')

        # go back to the chapters's list
        driver.get(self._parent.url)
        sleep(3)

        # getting the <ul id='simpleList'>
        chapters_list: WebElement = driver.find_element_by_id('simpleList')

        # move the cursor over the chapter's list.
        ActionChains(driver).move_to_element(chapters_list).perform()
        link = chapters_list.find_element(By.XPATH, f"//a[@chapter-id='{self.id}']")

        # prevent thoses morrons to open the link in a new tab...
        driver.execute_script("arguments[0].target='_self';", link)

        # actually click on the link
        actions = ActionChains(driver)
        actions.move_to_element(link).click().perform()

        # let the time to update the page.
        sleep(1)


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

    @error_handler(ClientResponseError, 'Miserable failure')
    async def leech(self, *args, **kwargs):
        return await super().leech(*args, **kwargs)

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
        """Rename local files from the current cbz name
        (based on self.name) to new naming convention
        (based on self._parent.chapers_naming)
        """
        root_path = self.path
        for chapter in self.chapters:
            chapter._parent = self
            name_path = root_path + f'/{chapter.name}.cbz'
            new_name = chapter.cbz_path
            if os.path.exists(name_path) and name_path != new_name:
                print(f'Renaming {name_path} to {new_name}')
                os.rename(name_path, new_name)
