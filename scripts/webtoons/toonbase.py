import os
import sys

import mongomodel
import requests
from datetime import datetime
from requests.cookies import cookiejar_from_dict
from tempfile import TemporaryDirectory
import zipfile


mongomodel.setup_database('10.8.1.1')


class ToonBaseUrlInvalidError(Exception):
    pass


class Chdir:
    def __init__(self, path):
        self.dir = path
        self.previous_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.dir)

    def __exit__(self, *_):
        os.chdir(self.previous_dir)


class ToonBase(mongomodel.Document):
    name = mongomodel.StringField()
    created = mongomodel.DateTimeField(default=lambda: datetime.now())
    fetched = mongomodel.BoolField(False)
    last_fetch = mongomodel.DateTimeField(required=False)
    lang = mongomodel.StringField(maxlen=2)
    domain = mongomodel.StringField(maxlen=255)
    episode = mongomodel.IntegerField()
    finished = mongomodel.BoolField(default=lambda: False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.headers = self.get_headers()
        self.session.cookies = cookiejar_from_dict(self.get_cookies())

    def pre_save(self, data, is_new=False):
        self.created = data.get('created')

    def get_cookies(self):
        return {}

    def get_headers(self):
        return {
            'Referer': self.domain,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/61.0.3112.113 Safari/537.36',
        }

    def __repr__(self):
        return f'<Toon {self.name}>'

    @property
    def path(self):
        return f'/run/media/adamaru/Aiur/Scans/Toomics/{self.name}'

    @property
    def cbz_path(self):
        return f'{self.path}/{self.episode}.cbz'

    def pages(self):
        return []

    def pull(self):
        if not self.name:
            print('setup a name first !')
            return
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        pages = self.pages()
        print(self.name, self.episode, end=': ')
        if not pages:
            print('no pages')
            return

        with TemporaryDirectory() as tmpd:
            with Chdir(tmpd):
                cbz = zipfile.ZipFile(self.cbz_path, 'w', zipfile.ZIP_DEFLATED)
                for i, url in enumerate(pages):
                    filepath = os.path.join(tmpd, f'{i:03}.jpg')
                    page_response = self.session.get(
                        url, headers={'Referer': self.url})
                    assert page_response.status_code == 200, \
                        page_response.status_code
                    page_data = page_response.content
                    with open(filepath, 'wb') as fp:
                        fp.write(page_data)
                    print('.', end='')
                    sys.stdout.flush()
                    cbz.write(filepath, os.path.basename(filepath))
            cbz.close()
            print('\n', end='')
        self.last_fetch = datetime.now()
        self.fetched = True

    def exists(self):
        return os.path.exists(self.cbz_path)

    def inc(self):
        raise NotImplementedError

    def auth(self, username, password) -> 'ToonBase':
        """Override this method to perform authentication on the scrapped site
        return None if the autentication failed.
        """
        return self

    def leech(self, **kwargs) -> 'ToonBase':
        try:
            while True:
                if not self.exists():
                    self.pull()
                    self.save()
                self.inc(**kwargs)
        except (StopIteration, ToonBaseUrlInvalidError):
            return self

    def rename(self, newname):
        if newname == self.name:
            return
        folder = os.path.join('/', *self.path.split('/')[0:-1])
        new_folder = os.path.join(folder, newname)
        os.rename(self.path, new_folder)
        self.name = newname
        return self.save()
