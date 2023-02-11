from motorized import Q, mark_parents
from newtoon import Chapter, WebToonPacked, Chapter, ToonManager, SeleniumMixin
from typing import List, Optional

import asyncio
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
import re

class XunScanChapter(Chapter):
    key: str

    @classmethod
    def from_url(cls, url: str, index: int) -> Optional["XunScanChapter"]:
        rule = re.compile(r'^https://xunscans.xyz/manga/.+/([\w-]+)/$')
        match = rule.match(url)
        if not match:
            print('no match for', url)
            return None
        name = match.groups(0)[0]
        name = name.replace('?', '')
        return cls(name=name, episode=index)

    @property
    def url(self) -> str:
        return f'{self._parent.url}/{self.key}/'

    async def get_pages_urls(self) -> List[str]:
        self._parent.driver.get(self.url)
        self._parent.driver.implicitly_wait(5)

        reading_div: WebElement = self._parent.driver.find_element(By.XPATH, '//div[@class="reading-content"]')
        imgs: List[WebElement] = reading_div.find_elements(By.XPATH, '//div[@class="page-break "]/img')
        srcs: List[str] = list([elem.get_attribute('data-src').strip() for elem in imgs])
        srcs = list(filter(None, srcs))
        return srcs

    @classmethod
    def from_element(cls, element: WebElement, index: int) -> Optional["XunScanChapter"]:
            rule = 'https://xunscans.xyz/manga/.+/(.+)/'
            match = re.compile(rule)
            url: str = element.get_attribute('href')
            match = match.search(url)
            if not match:
                return None
            key: str = match.groups()[0]
            name: str = element.text.strip().replace('?', '')
            if not name:
                print('no name for ', element.text, element.tag_name)
                return None
            chapter = cls(
                name=name,
                key=key,
                episode=index
            )
            return chapter


class XunScan(SeleniumMixin, WebToonPacked):
    chapters: List[XunScanChapter] = []
    lang: str = 'en'
    domain: str = 'xunscans.xyz'
    reversed: bool = True

    class Mongo:
        collection = 'webtoonpackeds'
        filters = Q(domain='xunscans.xyz')
        manager_class = ToonManager

    @property
    def url(self) -> str:
        return f'https://xunscans.xyz/manga/{self.name}'

    async def get_chapters_from_website(self) -> List[XunScanChapter]:
        self.driver.get(self.url)
        await asyncio.sleep(3)

        # click on the "read more" button to get all the chapters list
        # read_more = self.driver.find_element(By.XPATH, '//*[@id="manga-chapters-holder"]/div[2]/div/div/span')
        read_more = self.driver.find_element(By.CSS_SELECTOR, 'span.chapter-readmore')
        try:
            read_more.click()
            # print('waiting for chapters to load...')
            await asyncio.sleep(10)
        except ElementNotInteractableException:
            print('cannot expand chapters')

        links = self.driver.find_element(By.ID, 'manga-chapters-holder').find_elements(By.XPATH, '//div/div/ul/li/a')

        if self.reversed:
            links = links[::-1]
        chapters = list(
            filter(
                None,
                [
                    XunScanChapter.from_element(elem, index)
                    for index, elem in enumerate(links)
                ]
            )
        )
        return chapters
