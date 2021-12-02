from typing import Optional
import bs4 as BeautifulSoup

import re

from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
from motorized import Q
from toonbase import AsyncToon, ToonManager


class ToomicManager(ToonManager):
    domain = 'toomics.com'
    lang = 'fr'
    _driver: Optional[webdriver.Firefox] = None

    def from_url(self, url, name=None) -> Optional["Toomic"]:
        m = re.compile(r'^https://([\w.]+)/(\w+)/webtoon/detail/code/(\d+)/'
                       r'ep/(\d+)/toon/(\d+)')
        match = m.match(url)
        if not match:
            return

        domain, lang, code, ep, identifier = match.groups()
        instance = self.model(
            name=name,
            lang=lang,
            code=int(code),
            identifier=int(identifier),
            episode=int(ep),
            domain=domain
        )
        instance._driver = self._driver
        return instance

    async def leech(self, **kwargs) -> None:
        assert self.driver
        async for toon in self.filter(finished=False).lasts():
            toon._driver = self.driver
            await toon.leech()

    async def authenticate(self, username: str, password: str) -> None:
        driver = self.driver
        driver.get(f'https://{self.domain}/{self.lang}')
        try:
            driver.find_element_by_id('toggle-login').click()
        except Exception:
            pass

        driver.find_element_by_id('tab_sign_in').click()

        # click on login by email button
        driver.find_element_by_id('sns_login_fieldset') \
            .find_element_by_tag_name('button').click()

        # fill out the form with credentials
        driver.find_element_by_id('user_id').send_keys(username)
        driver.find_element_by_id('user_pw').send_keys(password)

        # click on the submit button
        driver.find_element_by_id('login_fieldset') \
            .find_element_by_tag_name('button').click()

    @property
    def driver(self) -> webdriver.Firefox:
        if self._driver is None:
            self._driver = webdriver.Firefox()
        return self._driver

    def copy(self) -> "ToomicManager":
        instance = super().copy()
        #instance._driver = self.driver
        return instance


class Toomic(AsyncToon):
    identifier: int
    code: int
    domain: str = 'toomics.com'

    _soup: Optional[BeautifulSoup.BeautifulSoup] = None
    _html: Optional[str] = None
    _driver: Optional[webdriver.Firefox] = None

    class Mongo:
        manager_class = ToomicManager
        collection = 'toons'
        filters = Q(domain='toomics.com')

    def get_cookies(self) -> dict:
        return {
            'cp': '928%7C134',
            # 'backurl': urlquote(self.url),
            'GTOOMICSlogin_chk_his': '1',
            'GTOOMICSlogin_attempt': '1',
            'GTOOMICSpidIntro': '1',
            'first_open_episode': 'Y',
            'GTOOMICSslave': 'sdb5',
            'content_lang': self.lang,
            'GTOOMICSvip_chk': 'email'
        }

    @property
    def url(self):
        return f'https://toomics.com/{self.lang}/webtoon/detail/code/' \
               f'{self.code}/ep/{self.episode}/toon/{self.identifier}'

    def parse(self):
        self.get_html()
        container = self._soup.find('div', {'id': 'viewer-img'})
        if not container:
            return []
        return container.find_all('img')

    async def get_pages(self):
        return list([img.get('src') for img in self.parse()])

    def get_html(self):
        if self._html:
            return self
        self.go()
        self._html = self._driver.page_source
        self._soup = BeautifulSoup.BeautifulSoup(self._html, 'lxml')
        return self

    def go(self):
        """Open the current chapter on the selenium navigator
        """
        driver = self._driver
        if driver.current_url != self.url:
            driver.get(self.url)

    def get_pagination(self):
        footer_links = self._driver \
            .find_element_by_tag_name('footer') \
            .find_elements_by_tag_name('a')
        previous, current, next_chapter = footer_links
        return (previous, current, next_chapter)

    async def get_next(self) -> Optional["Toomic"]:
        self.go()
        next_chapter = self.get_pagination()[2]
        next_chapter_url = next_chapter.get_property('href')
        instance = self.objects.from_url(next_chapter_url, name=self.name)
        if not instance:
            return None
        instance.corporate = self.corporate
        instance.lang = self.lang
        instance._driver = self._driver
        return instance

    async def leech(self):
        try:
            return await super().leech()
        except (UnexpectedAlertPresentException, StopAsyncIteration):
            return None

    async def load_extra_attributes(self, new_toon):
        new_toon._driver = self._driver
