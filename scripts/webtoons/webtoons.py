#!./venv/bin/python
import os
import sys
import argparse
import re
import requests
import bs4 as BeautifulSoup
from tempfile import TemporaryDirectory
import zipfile

from neomodel import (
	config, StructuredNode, StringProperty, IntegerProperty,
	UniqueIdProperty, RelationshipTo, One, BooleanProperty
)

PASSWORD = os.getenv('PASSWORD')
if not PASSWORD:
	raise Exception

config.DATABASE_URL = f'bolt://neo4j:{PASSWORD}@10.8.0.1:7687'


class Gender(StructuredNode):
	name = StringProperty(unique=True)

	def post_create(self):
		print('created a new gender', self.name)

	@staticmethod
	def get_or_create(name):
		try:
			return Gender.nodes.get(name=name)
		except Gender.DoesNotExist:
			return Gender(name=name).save()


class Toon(StructuredNode):
	name = StringProperty()
	epno = IntegerProperty()
	titleno = IntegerProperty()
	gender = RelationshipTo('Gender', 'Genre', cardinality=One)
	chapter = StringProperty()
	fetched = BooleanProperty(default=False)

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
		return os.path.join('/run/media/adamaru/Aiur/Scans/Webtoons/', self.name)

	@property
	def cbz_path(self):
		return os.path.join(self.path, f'{self.chapter}.cbz')

	@property
	def url(self):
		return f'https://webtoons.com/en/{self.gender.name}/{self.name}/{self.chapter}/viewer?title_no={self.titleno}&episode_no={self.epno}'

	@staticmethod
	def purge():
		for toon in Toon.nodes.all():
			toon.delete()

	@staticmethod
	def iter():
		for toon in Toon.nodes.order_by('name').all():
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
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3112.113 Safari/537.36'
		}

	def fetch_url(self, url, filepath):
		response = requests.get(url, stream=True, headers=self.headers)
		if response.status_code != 200:
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
		page = requests.get(self.url)
		if page.status_code != 200:
			raise ValueError(page.status_code)
		soup = BeautifulSoup.BeautifulSoup(page.text, 'lxml')
		return soup

	def get_next_instance(self, soup: BeautifulSoup):
		next_page = soup.find_all("a", class_='pg_next')[0].get('href')
		next_toon = Toon.from_url(next_page)
		self.delete()
		return next_toon

	def pull(self, force=False):
		if not os.path.exists(self.path):
			os.mkdir(self.path)

		soup = self.get_soup()
		if not force and os.path.exists(self.cbz_path):
			print(f'{self.name} {self.chapter} : skiped, already present')
			return self.get_next_instance(soup)

		def leech():
			print(f'{self.name} {self.chapter} : ', end='')
			with TemporaryDirectory() as tmpd:
				os.chdir(tmpd)
				i  = 0
				cbz = zipfile.ZipFile(self.cbz_path, 'w', zipfile.ZIP_DEFLATED)
				for url in self.index(soup):
					filepath = self.fetch_url(url, os.path.join(tmpd, f'{i:03}.jpg'))
					cbz.write(filepath, os.path.basename(filepath))
					i += 1
				cbz.close()
			self.fetched = True
			self.save()
			sys.stdout.write('\n')
			sys.stdout.flush()

		if not self.fetched:
			leech()
		return self.get_next_instance(soup)


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
	def pull_all(cls):
		for toon in Toon.nodes:
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


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-a', '--add')
	parser.add_argument('-l', '--list', action='store_true')
	parser.add_argument('-p', '--pull')
	parser.add_argument('-P', '--pullall', action='store_true')
	parser.add_argument('-d', '--delete')
	parser.add_argument('-r', '--redl')
	parser.add_argument('-u', '--update')

	args = parser.parse_args()
	if args.list:
		print('subscribed toons:')
		for toon in Toon.iter():
			print(f'{toon.name:30} {toon.chapter}')

	if args.add:
		Toon.from_url(args.add)

	if args.pullall:
		ToonManager.pull_all()

	elif args.pull:
		ToonManager.pull(args.pull)

	if args.delete:
		try:
			Toon.nodes.get(name=args.delete).delete()
			print('deleted')
		except Toon.DoesNotExist:
			print(f'no such toon {args.delete}')


	if args.redl:
		t = Toon.from_url(args.redl)
		try:
			t.pull().delete()
		except KeyboardInterrupt:
			pass
		print('removed temporary toon.')

	if args.update:
		t = Toon.from_url(args.update)
		t.delete()
		for old in Toon.nodes.filter(name=t.name).all():
			old.delete()
		t.save()
		print('updated', t.name)
