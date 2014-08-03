import debug, os, logging, re
from datetime import datetime
from bson.objectid import ObjectId as MongoID
from urllib.request import urlopen
from xml.etree import ElementTree
from pymongo import MongoClient

def main():
    path_prefix = '' if debug.local_run() else os.environ['OPENSHIFT_REPO_DIR']
    logging.basicConfig(filename = path_prefix + 'crawler.log', level = logging.DEBUG)
    log = logging.getLogger('crawler')
    log.info('>>> %s', datetime.utcnow())

    try: lock_file = open(path_prefix + 'crawler.lock', 'w')
    except IOError:
        log.exception('Already running. Probably.')
        return 0
    else: lock_file.close()

    def build_nyaa_rss_parser():
        re_SLD = re.compile('^([0-9]+) seeder\(s\), ([0-9]+) leecher\(s\), ([0-9]+) download\(s\)', re.I)
        def nyaa_rss_parser(tree):
            for item in tree.findall('.//item'):
                try: title, category, torrent_link, details_link, meta_string, date_string = (child.text for child in item.getchildren())
                except Exception:
                    log.exception('Assumed XML structure didn\'t quite match reality in item [%s].' % item)
                    continue
                try: s, l, d = re_SLD.match(meta_string).groups()
                except Exception:
                    log.exception('Failed to extract S/L/D numbers in item [%s].' % item)
                    continue
                try: torrent_ts = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S +0000')
                except Exception:
                    log.exception('Failed to extract timestamp in item [%s].' % item)
                    continue
                try: id = MongoID('{:0>24}'.format(hex(int(re.match('.*=([0-9]+)$', torrent_link).group(1)))[2:]))
                except Exception:
                    log.exception('Failed to generate MongoDB ID for item [%s].' % item)
                    continue
                yield {'_id': id, 'title': title, 'link': torrent_link, 'seeders': int(s), 'leechers': int(l), 'downloads': int(d), 'timestamp': torrent_ts}
        return nyaa_rss_parser

    torrents = []

    # site, site parser, page offsets
    sites = [('http://www.nyaa.se/?page=rss&cats=1_37&filter=2&offset=%d', build_nyaa_rss_parser(), (offset + 1 for offset in range(16)))]

    for site, site_parser, offsets in sites:
        for page_offset in offsets:
            resource = site % page_offset
            try: site_xml = urlopen(resource)
            except Exception: log.exception('Failed to load [%s].', resource)
            else:
                try: site_tree = ElementTree.parse(site_xml)
                except Exception: log.exception('Failed to parse [%s].', resource)
                else:
                    for torrent in site_parser(site_tree):
                        torrents.append(torrent)

    try:
        with MongoClient(debug.get_mongodb_url()) as client:
            collection = client.sashok.torrents
            for torrent in torrents: collection.save(torrent)
    except Exception:
        log.exception('Failed to commit data to MongoDB.')

    log.info('Collected [%d] items.', len(torrents))

    try: os.remove(path_prefix + 'crawler.lock')
    except Exception: log.exception('Lock file lives on! Ho!')

if __name__ == '__main__':
    main()