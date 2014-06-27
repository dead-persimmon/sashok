#!/usr/bin/env python

from time import sleep

from os.path import isfile as is_file
from os import remove as del_file

from urllib.request import urlopen as open_url
from xml.etree.ElementTree import parse as parse_tree

import parsers

lock_file_name = 'crawler.lock'

###
try:
	del_file(lock_file_name)
except Exception:
	pass
###

if is_file(lock_file_name):
	print('locked')
	exit()

open(lock_file_name, 'a').close()

init = [('http://www.nyaa.se/?page=rss&cats=1_37&filter=2&offset=%d', parsers.nyaa_rss)]

for site, parser in init:
	try:
		tree = parse_tree(open_url(site % 1))
		parser(tree)
	except Exception as exception:
		print(exception)
	
del_file(lock_file_name)