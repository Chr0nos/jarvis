#!./venv/bin/python
import os
import sys
import argparse
import re
import requests
import bs4 as BeautifulSoup
from tempfile import TemporaryDirectory
import zipfile
from datetime import datetime, timedelta
from requests.cookies import cookiejar_from_dict

from neomodel import (
    config, StructuredNode, StringProperty, IntegerProperty,
    RelationshipTo, One, BooleanProperty,
    DateTimeProperty, Q
)
from neomodel.core import db

PASSWORD = os.getenv('PASSWORD')
if not PASSWORD:
    raise Exception

config.DATABASE_URL = f'bolt://neo4j:{PASSWORD}@10.8.0.1:7687'


class Gender(StructuredNode):
    name = StringProperty(unique=True, required=True)

    def post_create(self):
        print('created a new gender', self.name)

    @staticmethod
    def get_or_create(name):
        try:
            return Gender.nodes.get(name=name)
        except Gender.DoesNotExist:
            print('creating a new gender', name)
            return Gender(name=name).save()


class Toon(StructuredNode):
    session = None
    name = StringProperty(required=True)
    epno = IntegerProperty(required=True)
    titleno = IntegerProperty(required=True)
    gender = RelationshipTo('Gender', 'Genre', cardinality=One)
    chapter = StringProperty(required=True)
    fetched = BooleanProperty(default=False)
    last_fetch = DateTimeProperty(optional=True, default=None)
    created = DateTimeProperty(default=datetime.now())
    finished = BooleanProperty(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.headers = self.headers
        self.session.cookies = cookiejar_from_dict({
            'needGDPR': 'false',
            'ageGatePass': 'true',
            'allowedCookie': 'ga',
            'contentLanguage': 'en',
            'locale': 'en'
        })

    class exceptions:
        class UrlInvalid(Exception):
            pass

    @staticmethod
    def from_url(url):
        # print('parsing ', url)
        r = re.compile(r'^https:\/\/([\w\.]+)\/en\/([\w-]+)\/([\w-]+)\/([\w-]+)\/viewer\?title_no=(\d+)&episode_no=(\d+)')
        m = r.match(url)
        if not m:
            raise Toon.exceptions.UrlInvalid(url)
        site, gender_name, name, episode, title_no, episode_no = m.groups()
        gender = Gender.get_or_create(gender_name)
        toon = Toon(name=name, epno=episode_no, chapter=episode, titleno=title_no)
        toon.save()
        toon.gender.connect(gender)
        return toon

    @property
    def path(self):
        return os.path.join('/home/adamaru/Downloads/webtoons/', self.name)
        # return os.path.join('/run/media/adamaru/Aiur/Scans/Webtoons/', self.name)

    @property
    def cbz_path(self):
        return os.path.join(self.path, f'{self.chapter}.cbz')

    @property
    def url(self):
        return f'https://webtoons.com/en/{self.gender.single().name}/{self.name}/{self.chapter}/viewer?title_no={self.titleno}&episode_no={self.epno}'

    @staticmethod
    def purge():
        for toon in Toon.nodes.all():
            toon.delete()

    @staticmethod
    def iter(order='name'):
        for toon in Toon.nodes.order_by(order):
            yield toon

    def index(self, soup: BeautifulSoup):
        for img in soup.find_all('img', class_="_images"):
            url = img['data-url']
            if 'jpg' not in url and 'JPG' not in url and 'png' not in url:
                # print('i', url)
                continue
            yield url

    @property
    def headers(self):
        return {
            'Referer': 'www.webtoons.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3112.113 Safari/537.36',
        }

    def fetch_url(self, url, filepath):
        response = self.session.get(url, stream=True)
        if response.status_code != 200:
            print(url)
            raise ValueError(response.status_code)
        with open(filepath, 'wb') as fd:
            for chunk in response.iter_content(8192):
                fd.write(chunk)
            fd.close()
        sys.stdout.write('.')
        sys.stdout.flush()
        # print('->', filepath)
        return filepath

    def get_soup(self):
        page = self.session.get(self.url)
        if page.status_code != 200:
            print('error: failed to fetch', self.url)
            raise ValueError(page.status_code)
        soup = BeautifulSoup.BeautifulSoup(page.text, 'lxml')
        return soup

    def get_next_instance(self, soup: BeautifulSoup):
        # print(soup)
        next_page = soup.find_all("a", class_='pg_next')[0].get('href')
        next_toon = Toon.from_url(next_page)
        if self.last_fetch:
            next_toon.last_fetch = self.last_fetch
            next_toon.save()
        self.delete()
        return next_toon

    def pull(self, force=False, getnext=True):
        """Retrive the .jpgs and pack them into self.cbz
        force: overwrite any existing.cbz file for this chapter
        getnext: try to get the next page
        return an instance of Toon
        """
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        soup = self.get_soup()
        if not force and os.path.exists(self.cbz_path):
            print(f'{self.name} {self.chapter} : skiped, already present')
            # self.last_fetch = datetime.now()
            # self.save()
            return self.get_next_instance(soup)

        def leech():
            print(f'{self.name} {self.chapter} : ', end='')
            with TemporaryDirectory() as tmpd:
                os.chdir(tmpd)
                i = 0
                cbz = zipfile.ZipFile(self.cbz_path, 'w', zipfile.ZIP_DEFLATED)
                for url in self.index(soup):
                    filepath = self.fetch_url(
                        url, os.path.join(tmpd, f'{i:03}.jpg'))
                    cbz.write(filepath, os.path.basename(filepath))
                    i += 1
                cbz.close()
            self.fetched = True
            self.last_fetch = datetime.now()
            self.save()
            sys.stdout.write('\n')
            sys.stdout.flush()

        instance = self
        if not self.fetched:
            leech()
        if getnext:
            instance = self.get_next_instance(soup)
        return instance


class ToonManager:
    @staticmethod
    def pull_toon(toon):
        try:
            while True:
                toon = toon.pull()
        except Toon.exceptions.UrlInvalid:
            pass
        except KeyboardInterrupt:
            os.unlink(toon.cbz_path)
            print('canceled, removed incomplete cbz', toon.cbz_path)
            raise KeyboardInterrupt
        except requests.exceptions.ConnectionError as err:
            os.unlink(toon.cbz_path)
            print('connection error, removed incomplete cbz', err)

    @classmethod
    def pull_all(cls, smart):
        qs = Toon.nodes.exclude(finished=True)
        if smart:
            print('smart fetch')
            last_week = datetime.today() - timedelta(days=7)
            qs = qs.filter(
                Q(last_fetch__lte=last_week) | (Q(last_fetch__isnull=True))
            )
        for toon in qs:
            try:
                cls.pull_toon(toon)
            except KeyboardInterrupt:
                return
            except requests.exceptions.ConnectionError as err:
                os.unlink(toon.cbz_path)
                print('connection error, removed incomplete cbz', err)
                return

    @classmethod
    def pull(cls, name):
        cls.pull_toon(Toon.nodes.get(name=name))


def get_date(d):
    if not d:
        return ''
    return d.strftime("%d/%m/%Y")
    # return d.ctime()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add')
    parser.add_argument('-l', '--list', action='store_true')
    parser.add_argument('-p', '--pull')
    parser.add_argument('-P', '--pullall', action='store_true')
    parser.add_argument('-d', '--delete')
    parser.add_argument('-r', '--redl')
    parser.add_argument('-u', '--update')
    parser.add_argument('-s', '--smart', action='store_true')
    parser.add_argument('-t', '--time', action='store_true')
    args = parser.parse_args()
    if args.list:
        print('subscribed toons:')
        for toon in Toon.iter('-last_fetch' if args.time else 'name'):
            gender_name = toon.gender.single().name
            print(f'{toon.name:30} {toon.chapter:30} {get_date(toon.last_fetch)} {gender_name}')

    if args.add:
        toon = Toon.from_url(args.add)

    if args.pullall:
        ToonManager.pull_all(args.smart)

    elif args.pull:
        ToonManager.pull(args.pull)

    if args.delete:
        try:
            for toon in Toon.nodes.filter(name=args.delete):
                print(toon.name, 'deleted')
                toon.delete()
        except Toon.DoesNotExist:
            print(f'no such toon {args.delete}')

    if args.redl:
        t = Toon.from_url(args.redl)
        try:
            t.pull(getnext=False).delete()
        except KeyboardInterrupt:
            t.delete()
        print('removed temporary toon.')

    if args.update:
        t = Toon.from_url(args.update)
        t.delete()
        for old in Toon.nodes.filter(name=t.name).all():
            old.delete()
        t.save()
        print('updated', t.name)
    db.driver.close()
