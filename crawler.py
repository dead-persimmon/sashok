exit()

from datetime import datetime

from os.path import isfile as is_file
from os import remove as del_file
from os import linesep as line_sep

from urllib.request import urlopen as open_url
from xml.etree.ElementTree import parse as parse_tree

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

def nyaa_rss(tree):
	counter = 0
	for item in tree.findall('.//item'):
		try:
			title, category, torrent_link, details_link, meta_string, date = (child.text for child in item.getchildren())
			seeders, leechers, downloads = re.match('^([0-9]+) seeder\(s\), ([0-9]+) leecher\(s\), ([0-9]+) download\(s\)', meta_string).groups()
			counter += 1
		except Exception as exception: #ValueError
			log(exception)
			continue
	log('Collected %d items from Nyaa.' % counter)

init = [('http://www.nyaa.se/?page=rss&cats=1_37&filter=2&offset=%d', nyaa_rss)]

for site, parser in init:
	try:
		tree = parse_tree(open_url(site % 1))
		parser(tree)
	except Exception as exception:
		log(exception)
	
del_file(lock_file_name)