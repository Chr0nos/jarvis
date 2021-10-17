#!./venv/bin/python
import os
import re
import bs4 as BeautifulSoup

from datetime import datetime, timedelta

from toonbase import ToonBase, ToonBaseUrlInvalidError, AsyncToonMixin
import mongomodel
import click


class ToonManager(mongomodel.queryset.QuerySet):
    def from_url(self, url: str):
        # print('parsing ', url)
        r = re.compile(r'^https:\/\/([\w\.]+)\/en\/([\w-]+)\/([\w-]+)\/([\w-]+)\/viewer\?title_no=(\d+)&episode_no=(\d+)')
        m = r.match(url)
        if not m:
            raise ToonBaseUrlInvalidError(url)
        site, gender_name, name, episode, title_no, episode_no = m.groups()
        toon = self.model(
            name=name,
            episode=int(episode_no),
            chapter=episode,
            titleno=int(title_no),
            gender=gender_name,
            lang='en',
            domain='webtoon.com'
        )
        return toon


class Toon(AsyncToonMixin, ToonBase):
    manager_class = ToonManager
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
            'locale': 'en',
            'countryCode': 'US'
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

    async def pages(self):
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
        instance = Toon.objects.from_url(next_page)
        self.episode = instance.episode
        self.chapter = instance.chapter
        self.lang = instance.lang
        self.domain = instance.domain
        self.soup = None
        self.page_content = None
        return instance

    async def leech(self, *args, **kwargs):
        await self.log(f'leeching {self}', end='\n')
        return await super().leech(*args, **kwargs)


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
    toon.leech()


@click.command('redl', help='Re-Download a chapter without telling to the db')
@click.argument('url')
def redl(url):
    Toon.objects.from_url(url).pull(getnext=False)


# @click.command('pullall')
async def pullall():
    for toon in Toon.objects.exclude(finished=True):
        await toon.leech()


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
    # cli.add_command(pullall)
    cli.add_command(pullable)
    cli.add_command(update)
    cli()
