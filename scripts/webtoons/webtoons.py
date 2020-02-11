#!./venv/bin/python
import os
import re
import requests
import bs4 as BeautifulSoup

from datetime import datetime, timedelta

from toonbase import ToonBase, ToonBaseUrlInvalidError
import mongomodel
import click


class Toon(ToonBase):
    collection = 'mongotoon'
    titleno = mongomodel.IntegerField()
    gender = mongomodel.StringField(maxlen=200)
    chapter = mongomodel.StringField()
    soup = None

    def get_cookies(self):
        return {
            'needGDPR': 'false',
            'ageGatePass': 'true',
            'allowedCookie': 'ga',
            'contentLanguage': 'en',
            'locale': 'en'
        }

    def get_headers(self):
        return {
            'Referer': 'www.webtoons.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/61.0.3112.113 Safari/537.36',
        }

    def __repr__(self):
        return f'<Toon {self.name}> {self.chapter}'

    def __str__(self):
        def get_date(d):
            return d.strftime("%d/%m/%Y") if d else ''

        return f'{self.name:30} {self.chapter:40} {get_date(self.last_fetch)} {self.gender}'

    @staticmethod
    def from_url(url):
        # print('parsing ', url)
        r = re.compile(r'^https:\/\/([\w\.]+)\/en\/([\w-]+)\/([\w-]+)\/([\w-]+)\/viewer\?title_no=(\d+)&episode_no=(\d+)')
        m = r.match(url)
        if not m:
            raise ToonBaseUrlInvalidError(url)
        site, gender_name, name, episode, title_no, episode_no = m.groups()
        toon = Toon(
            name=name,
            episode=int(episode_no),
            chapter=episode,
            titleno=int(title_no),
            gender=gender_name,
            lang='en',
            domain='webtoon.com'
        )
        return toon

    @property
    def path(self):
        if not self.name:
            return None
        # return os.path.join('/home/adamaru/Downloads/webtoons/', self.name)
        return os.path.join('/run/media/adamaru/Aiur/Scans/Webtoons/',
                            self.name)

    @property
    def cbz_path(self):
        if not self.chapter or not self.path:
            return None
        return os.path.join(self.path, f'{self.chapter}.cbz')

    @property
    def url(self):
        return ''.join(
            f'https://webtoons.com/en/{self.gender}/{self.name}/'
            f'{self.chapter}/viewer?title_no={self.titleno}'
            f'&episode_no={self.episode}'
        )

    def index(self):
        if not self.soup:
            self.get_soup()
        for img in self.soup.find_all('img', class_="_images"):
            url = img['data-url']
            if 'jpg' not in url and 'JPG' not in url and 'png' not in url:
                # print('i', url)
                continue
            yield url

    def pages(self):
        return list(self.index())

    def get_soup(self):
        page = self.session.get(self.url)
        if page.status_code != 200:
            print('error: failed to fetch', self.url)
            raise ValueError(page.status_code)
        self.soup = BeautifulSoup.BeautifulSoup(page.text, 'lxml')
        return self.soup

    def inc(self):
        if not self.soup:
            self.get_soup()
        try:
            next_page = self.soup.find_all("a", class_='pg_next')[0].get('href')
        except AttributeError as err:
            raise ToonBaseUrlInvalidError from err
        instance = Toon.from_url(next_page)
        self.episode = instance.episode
        self.chapter = instance.chapter
        self.lang = instance.lang
        self.domain = instance.domain
        self.soup = None
        return instance


class ToonManager:
    @staticmethod
    def pull_toon(toon):
        try:
            toon.leech()
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
                toon.leech()
            except KeyboardInterrupt:
                return
            except requests.exceptions.ConnectionError as err:
                os.unlink(toon.cbz_path)
                print('connection error, removed incomplete cbz', err)
                return

    @classmethod
    def pull(cls, name):
        cls.pull_toon(Toon.objects.get(name=name))


@click.command('list')
@click.option('--sort', default='name')
def display_list(sort):
    print('subscribed toons:')
    for toon in Toon.objects.sort([sort]):
        print(str(toon))


@click.command('delete')
@click.argument('name')
def delete(name):
    Toon.objects.get(name=name).delete()


@click.command('pull')
@click.argument('name')
def pull(name):
    toon = Toon.objects.get(name=name)
    ToonManager.pull_toon(toon)


@click.command('redl', help='Re-Download a chapter without telling to the db')
@click.argument('url')
def redl(url):
    Toon.from_url(url).pull(getnext=False)


@click.command('pullall')
def pullall():
    one_week_ago = datetime.now() - timedelta(days=7)
    qs = Toon.objects.exclude(finished=True) \
        .filter(last_fetch__lte=one_week_ago)
    for toon in qs:
        try:
            ToonManager.pull_toon(toon)
        except KeyboardInterrupt:
            return
        except requests.exceptions.ConnectionError as err:
            os.unlink(toon.cbz_path)
            print('connection error, removed incomplete cbz', err)
            return


@click.command('pullable')
def pullable():
    one_week_ago = datetime.now() - timedelta(days=7)
    qs = Toon.objects.exclude(last_fetch__gt=one_week_ago, finished=True)
    print(*sorted(qs.distinct('name')), sep='\n')


@click.command('update',
               help='update a current subscribed toon to a previous state')
@click.argument('url')
def update(url):
    toon = Toon.from_url(url)
    Toon.objects.get(name=toon.name).delete()
    toon.save()


@click.command('add', help='Subscribe to a toon, give the url as parameter')
@click.argument('url')
def add(url):
    toon = Toon.from_url(url)
    if Toon.objects.filter(name=toon.name).count() > 0:
        click.echo('This toon is already subscribed')
        return
    toon.save()


@click.group()
def cli():
    pass


if __name__ == "__main__":
    cli.add_command(add)
    cli.add_command(display_list)
    cli.add_command(delete)
    cli.add_command(redl)
    cli.add_command(pull)
    cli.add_command(pullall)
    cli.add_command(pullable)
    cli.add_command(update)
    cli()
