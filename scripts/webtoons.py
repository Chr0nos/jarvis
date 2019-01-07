#!/usr/bin/python3
# Author: Chr0nos
# Version: 1.02
# License: GPL v3+

import zipfile
import os
import sys
import pymongo
import requests
import re
import bs4 as BeautifulSoup
import shutil
from http.client import RemoteDisconnected
import json

DOWNLOAD_DIR = '/run/media/adamaru/Aiur/Scans/Webtoons'

class Database():
	def __init__(self):
		self.db = None
		self.c = None

	def __del__(self):
		if self.db:
			# print("Disconnecting database")
			self.db.close()

	def connect(self, database):
		if self.db:
			print("Already connected to database: skipping")
			return self
		# print("Connecting to database")
		self.db = pymongo.MongoClient("localhost", 27017)
		self.c = self.db[database]
		return self

	def insert(self, table, item):
		return (self.c[table].insert_one(item))

	def list(self):
		print('-- Database --')
		for x in self.c.subs.find():
			print(x)
		print('---- END ----')

	def find(self, table, item):
		return (self.c[table].find_one(item))

	def drop(self, table):
		self.c[table].drop()

	def remove(self, table, item):
		self.c[table].delete_one(item)


class WebToons():
	def __init__(self, db):
		 self.db = db
		 self.subs = 'subs'

	def from_url(self, url):
		if type(url) != str:
			raise(ValueError(url))
		r = re.compile(r'^https:\/\/([\w\.]+)\/en\/([\w-]+)\/([\w-]+)\/([\w-]+)\/viewer\?title_no=(\d+)&episode_no=(\d+)')
		m = r.match(url)
		if not m:
			print("url regex does not match. sorry bro.")
			return None
		site, category, name, episode, title_no, episode_no = m.groups()
		item = {
			'name': name,
			'url': url,
			'site': site,
			'episode': episode,
			'epno': int(episode_no),
			'titleno': int(title_no),
			'category': category,
			'done': False
		}
		return (item)

	def register(self, url):
		item = self.from_url(url)
		if self.db.find(self.subs, {'name': item['name']}):
			print('{} is already registred.'.format(item['name']))
			return False
		self.db.insert(self.subs, item)
		return True

	def unregister(self, name):
		self.db.remove(self.subs, {'name': name})

	def geturl(self, toon):
		if type(toon) == str:
			toon = self.db.find(self.subs, {'name': toon})
		url = 'https://{}/en/{}/{}/{}/viewer?title_no={}&episode_no={}'.format(
			toon['site'], toon['category'], toon['name'], toon['episode'],
			toon['titleno'], toon['epno'])
		return url

	def update(self, url):
		item = self.from_url(url)
		if not item:
			print('invalid url format.')
			return False
		if self.db.c[self.subs].find_one({'url': url}):
			print('refusing to update: the url is the same as before')
			return False
		self.db.c[self.subs].update_one({'name': item['name']}, {'$set': item})
		print(item['name'], 'updated')
		return True

	"""
	return a tupple with (name, toon)
	name: str
	toon: dict (the thing in the database)
	"""
	def getToonObject(self, item):
		if type(item) == str:
			return (item, self.db.find(self.subs, {'name': item}))
		if type(item) == dict and item.get('epno'):
			return (item['name'], item)
		print("Invalid item provided to getToonObject")
		raise(ValueError(item))

	def pull(self, name):
		(name, toon) = self.getToonObject(name)
		if not toon:
			print("error: {} is not registed".format(name))
			return False
		print("Pulling", name)
		lst, next_page = self.index(name)
		if toon.get('done'):
			print('chapter already done')
			# if the chapter is already done BUT there is a new one available
			# we update it with the new link then re-fetch
			if next_page and self.update(next_page):
				return self.pull(name)
			print('There is no new chapter, sorry.')
			return False

		if lst:
			target = '{}/{}/{:03}'.format(DOWNLOAD_DIR, name, toon['epno'])
			print(target)
			if not os.path.isdir(target):
				print("creating", target)
				os.makedirs(target)
			self.fetch_list(lst, target)
			self.cbz(target, os.path.join(DOWNLOAD_DIR, name, '{}.cbz'.format(toon['episode'])))
			shutil.rmtree(target)
			if not self.update(next_page):
				self.db.c[self.subs].update_one({'name': name}, {'$set': {'done': True}})
				return False
			return True

	def leech(self, name):
		while self.pull(name) == True:
			pass

	"""
	return a list of tuple, may return None in case of error.
	"""
	def index(self, toon):
		print(self.geturl(toon))
		lst = []
		page = requests.get(self.geturl(toon))
		if page.status_code != 200:
			print("Server has returned {} : stopping.".format(page.status_code))
			return None
		soup = BeautifulSoup.BeautifulSoup(page.text, 'lxml')
		i = 0
		for img in soup.find_all('img', class_="_images"):
			url = img['data-url']
			if 'jpg' not in url:
				continue
			lst.append(url)
		next_page = soup.find_all("a", class_='pg_next')
		return (lst, next_page[0].get('href'))

	def fetch_list(self, lst, target, overwrite=False):
		if type(target) != str:
			raise(ValueError(target))
		i = 0
		header = {
			'Referer': 'www.webtoons.com',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
		}
		for url in lst:
			filepath = "{}/{:04}.jpg".format(target, i)
			i += 1
			if os.path.exists(filepath):
				if not overwrite:
					print("skipping", filepath)
					continue
				else:
					os.unlink(filepath)
			print("getting {} to {}".format(url, filepath))
			try:
				rq = requests.get(url, headers=header, stream=True)
				if rq.status_code == 200:
					with open(filepath, 'wb') as fd:
						for chunk in rq.iter_content(4096):
							fd.write(chunk)
				else:
					print("error on fetch: {}", rq.status_code)
			except RemoteDisconnected as e:
				print("remote server disconnected us:", e)
				return False
		print("fetch done.")
		return True

	def cbz(self, path, target):
		z = zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED)
		for file in os.listdir(path):
			z.write(os.path.join(path, file))
		z.close()
		print('done')

	def leechall(self):
		for toon in self.db.c[self.subs].find():
			self.leech(toon)

	def export(self):
		lst = []
		for toon in self.db.c[self.subs].find():
			del(toon['_id'])
			lst.append(toon)
		return (json.dumps(lst, sort_keys=True, indent=4))

	def force_ep(self, url):
		target = self.from_url(url)
		if not target:
			raise (ValueError(url))
		backup = self.db.c[self.subs].find_one({"name": target['name']})
		if not backup:
			raise(ValueError(url))
		self.db.c[self.subs].update_one({'name': target['name']}, {'$set': target})
		self.pull(target['name'])
		print("restoring previous position")
		self.db.c[self.subs].update_one({'name': target['name']}, {'$set': backup})



def help(db=None, params=None):
	print("""available commands:
	add [url]
	del [url]
	pull [name]
	info [name]
	pullall
	cbz [name]
	drop
	update [url]
	pullall
	list""")


def test(db, params):
	db.connect('webtoons_test')
	w = WebToons(db)
	# w.register('https://www.webtoons.com/en/fantasy/unordinary/episode-104/viewer?title_no=679&episode_no=110')
	w.register('https://www.webtoons.com/en/fantasy/unordinary/episode-79/viewer?title_no=679&episode_no=85')
	lst, next_page = w.index('unordinary')
	for url in lst:
		print(url)
	db.drop('subs')


def add(db, params):
	w = WebToons(Database().connect('webtoons'))
	w.register(params[0])


def list_webtoons(db, params):
	db.connect('webtoons')
	print("Currenty registred toons:")
	for x in db.c.subs.find():
		print("{:30} - chapter: {:3} - {}".format(
			x['name'], x['epno'], x['category']))


def pull(db, params):
	WebToons(Database().connect('webtoons')).leech(params[0])


def drop(db, params):
	db.connect('webtoons').drop('subs')


def update(db, params):
	db.connect('webtoons')
	w = WebToons(db)
	w.update(params[0])


def geturl(db, params):
	print(WebToons(db.connect('webtoons')).geturl(params[0]))

def leechall(db, params):
	WebToons(db.connect('webtoons')).leechall()

def export(db, params):
	print(WebToons(db.connect('webtoons')).export())

def redl(db, params):
	w = WebToons(db.connect('webtoons'))
	w.force_ep(params[0])

def remove(db, params):
	db.connect('webtoons')
	db.remove('subs', {'name': params[0]})

def commands(cmd, params):
	cmds = {
		'test': (0, test),
		'add': (1, add),
		'list': (0, list_webtoons),
		'pull': (1, pull),
		'drop': (0, drop),
		'url': (1, geturl),
		'update': (1, update),
		'help': (0, help),
		'-h': (0, help),
		'pullall': (0, leechall),
		'export': (0, export),
		'redl': (1, redl),
		'del': (1, remove)
	}
	db = Database()
	if cmd not in cmds:
		print("unknow command", cmd)
		return
	arg_needed, func = cmds[cmd]
	if len(params) < arg_needed:
		print("missing parameters for", cmd)
		return
	func(db, params)

"""
usage:
./webtoons.py add unordinary
"""
def main():
	if not os.path.exists(DOWNLOAD_DIR):
		print(DOWNLOAD_DIR, "is not currently available, think to mount it ?")
		sys.exit(1)
	if len(sys.argv) == 1:
		help()
		return
	commands(sys.argv[1], sys.argv[2:])

if __name__ == "__main__":
	main()
