from typing import Optional
import bs4 as BeautifulSoup

import re
import os

from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
from motorized import Q
from toonbase import AsyncToon


class Chdir:
    def __init__(self, path):
        self.dir = path
        self.previous_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.dir)

    def __exit__(self, *_):
        os.chdir(self.previous_dir)


class Toomic(AsyncToon):
    identifier: int
    code: int
    domain: str = 'toomics.com'
    _soup = None
    _html = None
    _driver = None

    class Mongo:
        collection = 'toomic'
        filters = Q(domain='toomics.com')

    def copy(self):
        instance = Toomic(
            code=self.code,
            name=self.name,
            episode=self.episode,
            domain=self.domain,
            lang=self.lang,
            identifier=self.identifier
        )
        instance._html = self._html
        instance._soup = self._soup
        driver = getattr(self, '_driver', None)
        if driver:
            instance._driver = driver
        return instance

    def __repr__(self):
        return f'<Toomic: {self.name}> episode: {self.episode}'

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

    @classmethod
    def from_url(cls, url, driver=None):
        m = re.compile(r'^https://([\w.]+)/(\w+)/webtoon/detail/code/(\d+)/'
                       r'ep/(\d+)/toon/(\d+)')
        match = m.match(url)
        assert match

        domain, lang, code, ep, identifier = match.groups()
        instance = cls(
            lang=lang,
            code=int(code),
            identifier=int(identifier),
            episode=int(ep),
            domain=domain
        )
        instance.driver = driver
        return instance

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

    @property
    def path(self):
        return f'/run/media/adamaru/Aiur/Scans/Toomics/{self.name}'

    def __iadd__(self, x: int):
        self.code += x
        self.episode += x
        self._soup = None
        self._html = None
        return self

    def __isub__(self, x: int):
        self.code -= x
        self.episode -= x
        self._soup = None
        self._html = None
        return self

    def get_driver(self):
        if not self.driver:
            self.driver = webdriver.Firefox()
        return self.driver

    def get_html(self):
        if self._html:
            return self
        driver = self.get_driver()
        self.go()
        self._html = driver.page_source
        self._soup = BeautifulSoup.BeautifulSoup(self._html, 'lxml')
        return self

    def auth(self, username, password):
        driver = self.get_driver()
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

        # go back to the toon page
        driver.get(self.url)
        return self

    def go(self):
        """Open the current chapter on the selenium navigator
        """
        driver = self.get_driver()
        if driver.current_url != self.url:
            driver.get(self.url)

    def get_pagination(self):
        footer_links = self.get_driver() \
            .find_element_by_tag_name('footer') \
            .find_elements_by_tag_name('a')
        previous, current, next_chapter = footer_links
        return (previous, current, next_chapter)

    def move(self, to_next=True):
        self.go()
        try:
            next_chapter = self.get_pagination()[2 if to_next else 0]
            next_chapter_url = next_chapter.get_property('href')
            instance = self.from_url(next_chapter_url)
        except (AssertionError, ValueError) as err:
            raise StopIteration from err

        self.code = instance.code
        self.episode = instance.episode
        self.domain = instance.domain
        self.lang = instance.lang
        self._html = None
        self._soup = None
        return self

    def inc(self):
        return self.move(to_next=True)

    def dec(self):
        return self.move(to_next=False)

    async def get_next(self) -> Optional["Toomic"]:
        instance = self.copy()
        instance.move(to_next=True)
        return instance

    async def leech(self):
        try:
            return super().leech()
        except UnexpectedAlertPresentException:
            return None


async def pullall(user_id, password, **kwargs):
    driver: Optional[webdriver.Firefox] = None
    async for toon in Toomic.objects.lasts():
        if not driver:
            toon.auth(user_id, password)
            driver = toon.driver
        await toon.leech()
    return driver
