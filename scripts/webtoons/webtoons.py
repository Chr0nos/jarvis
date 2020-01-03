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

import mongomodel


class Toon(mongomodel.Document):
    collection = 'mongotoon'
    name = mongomodel.StringField()
    epno = mongomodel.IntegerField()
    titleno = mongomodel.IntegerField()
    gender = mongomodel.StringField(maxlen=200)
    chapter = mongomodel.StringField()
    fetched = mongomodel.BoolField(False)
    last_fetch = mongomodel.DateTimeField(required=False)
    created = mongomodel.DateTimeField(default=lambda: datetime.now())
    finished = mongomodel.BoolField(False)

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
        toon = Toon(name=name, epno=int(episode_no), chapter=episode,
                    titleno=int(title_no), gender=gender_name)
        return toon.commit()

    @property
    def path(self):
        if not self.name:
            return None
        return os.path.join('/home/adamaru/Downloads/webtoons/', self.name)
        # return os.path.join('/run/media/adamaru/Aiur/Scans/Webtoons/', self.name)

    @property
    def cbz_path(self):
        if not self.chapter or not self.path:
            return None
        return os.path.join(self.path, f'{self.chapter}.cbz')

    @property
    def url(self):
        return f'https://webtoons.com/en/{self.gender}/{self.name}/{self.chapter}/viewer?title_no={self.titleno}&episode_no={self.epno}'

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
                sys.stdout.flush()
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
        qs = Toon.objects.exclude(finished=True)
        if smart:
            print('smart fetch')
            last_week = datetime.today() - timedelta(days=7)
            qs = qs.filter(last_fetch__lte=last_week)
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
        cls.pull_toon(Toon.objects.get(name=name))


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
        qs = Toon.objects.__iter__(
            sort=['last_fetch' if args.time else 'name'])
        for toon in qs:
            print(f'{toon.name:30} {toon.chapter:40} {get_date(toon.last_fetch)} {toon.gender}')

    if args.add:
        toon = Toon.from_url(args.add)

    if args.pullall:
        ToonManager.pull_all(args.smart)

    elif args.pull:
        ToonManager.pull(args.pull)

    if args.delete:
        try:
            for toon in Toon.objects.get(name=args.delete):
                print(toon.name, 'deleted')
                toon.delete()
        except mongomodel.DocumentNotFoundError:
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
        for old in Toon.objects.filter(name=t.name).all():
            old.delete()
        t.save()
        print('updated', t.name)
