import os, sys, logging
import time
from datetime import datetime
from urllib.request import urlopen as open_url
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from bson.objectid import ObjectId as ObjectID

import debug

if debug.local_run():
    lock_file_name = 'crawler.lock'
    log_file_name = 'crawler.log'
    mongodb_url = 'mongodb://localhost:27017/'
else:
    from os import environ as environment
    lock_file_name = environment['OPENSHIFT_REPO_DIR'] + 'crawler.lock'
    log_file_name = environment['OPENSHIFT_REPO_DIR'] + 'crawler.log'
    mongodb_url = environment['OPENSHIFT_MONGODB_DB_URL']

ts_now = datetime.utcnow()

def main():
    logging.basicConfig(filename=log_file_name, level=logging.DEBUG)
    log = logging.getLogger('crawler')

    log.info('Starting at %s', ts_now)

    try:
        lockfile = open(lock_file_name, 'w')
    except IOError:
        log.critical('Already running. Probably.')
        sys.exit(1)
    else;
        lockfile.close()

    import re
    def nyaa_rss_parser(tree):
        oldest_torrent_ts = ts_now
        for item in tree.findall('.//item'):
            try:
                title, category, torrent_link, details_link, meta_string, date_string = (child.text for child in item.getchildren())
                s, l, d = re.match('^([0-9]+) seeder\(s\), ([0-9]+) leecher\(s\), ([0-9]+) download\(s\)', meta_string).groups()
                id = ObjectID('{:0>24}'.format(hex(int(re.match('.*=([0-9]+)$', torrent_link).group(1)))[2:]))
                #timestamp = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %z')
                torrent_ts = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S +0000')
                oldest_torrent_ts = min(oldest_torrent_ts, torrent_ts)
                torrents.append({'_id': id, 'title': title, 'link': torrent_link, 'seeders': int(s), 'leechers': int(l), 'downloads': int(d), 'timestamp': torrent_ts})
            except Exception as exception:
                log.exception('Parsing torrent')
        return ts_now - oldest_torrent_ts

    sites = [('http://www.nyaa.se/?page=rss&cats=1_37&filter=2&offset=%d', nyaa_rss_parser)]
    torrents = []

    for site, site_parser in sites:
        try:
            page_offset = 1
            while True:
                tree = ET.parse(open_url(site % page_offset))
                oldest_torrent = site_parser(tree)
                if oldest_torrent.days <= 14: page_offset += 1
                else: break
        except Exception as exception:
            log.exception('Parsing url %s', site % page_offset)

    with MongoClient(mongodb_url) as client:
        collection = client.sashok.torrents
        for torrent in torrents:
            collection.save(torrent)

    log.info('Collected %d items.', len(torrents))

    try:
        os.remove(lock_file_name)
    except IOError:
        log.exception('Failed to remove lockfile')

if __name__ == '__main__':
    main()
