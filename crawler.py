import time
from datetime import datetime

import os

from os.path import isfile as is_file
from os import remove as del_file
from os import linesep as line_sep

from urllib.request import urlopen as open_url
import xml.etree.ElementTree as ET

import re

from bson.objectid import ObjectId as ObjectID

import hashlib

lock_file_name = 'crawler.lock'
log_file_name = 'crawler.log'

def log(message):
	with open(log_file_name, 'a') as log_file:
		log_file.write(str(message) + line_sep)

log(line_sep + str(datetime.now()))

if is_file(lock_file_name):
	log('Already running. Probably.')
	exit()

open(lock_file_name, 'a').close()

data = []

def nyaa_rss_parser(tree):
	counter = 0
	for item in tree.findall('.//item'):
		try:
			title, category, torrent_link, details_link, meta_string, date_string = (child.text for child in item.getchildren())
			s, l, d = re.match('^([0-9]+) seeder\(s\), ([0-9]+) leecher\(s\), ([0-9]+) download\(s\)', meta_string).groups()
			id = ObjectID('{:0>24}'.format(hex(int(re.match('.*=([0-9]+)$', torrent_link).group(1)))[2:]))
			timestamp = time.strptime(date_string, '%a, %d %b %Y %H:%M:%S %z')
			data.append({'_id': id, 'title': title, 'torrent_link': torrent_link, 'seeders': s, 'leechers': l, 'downloads': d, 'timestamp': timestamp})
			counter += 1
		except Exception as exception: #ValueError
			log(exception)
	log('Collected %d items from Nyaa.' % counter)

sites = [('http://www.nyaa.se/?page=rss&cats=1_37&filter=2&offset=%d', nyaa_rss_parser, range(1, 3))]

for site, site_parser, page_offsets in sites:
	try:
		for page_offset in page_offsets:
			tree = ET.parse(open_url(site % page_offset))
			site_parser(tree)
	except Exception as exception:
		log(exception)

from pymongo import MongoClient

with MongoClient('mongodb://localhost:27017/') as client:
#with MongoClient(os.environ['OPENSHIFT_MONGODB_DB_URL']) as client:
	collection = client.sashok.torrents
	for d in data:
		collection.save(d)

del_file(lock_file_name)