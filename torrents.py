import debug, os

if debug.local_run(): mongodb_url = 'mongodb://localhost:27017/'
else: mongodb_url = os.environ['OPENSHIFT_MONGODB_DB_URL']

from pymongo import MongoClient
from datetime import datetime, timedelta
import calendar
import json

def build_normalize_title():
    import re
    esc = re.escape
    re_underscores = re.compile('_')
    re_dots = re.compile('\.')
    re_extensions = re.compile('|'.join(esc('.') + ext + '$' for ext in ('avi', 'mkv', 'mp4')), re.I)
    re_tags = re.compile('|'.join(esc(br[0]) + '[^' + esc(br[1]) + ']*' + esc(br[1]) for br in ('[]', '()', '{}')))
    re_spaces_greedy = re.compile('\s+')
    re_episode_number_variants = [re.compile('(?: - )([0-9]+)(?:v[0-9]+)? '), re.compile(' e([0-9]+)(?:v[0-9]+)? ', re.I)]
    re_solo_hyphens = re.compile(' -+ ')
    re_multiple_bangs = re.compile('!+')
    re_greedy_numbers = re.compile('[0-9]+')
    
    def normalize_number(number_string_mo):
        return str(int(number_string_mo.group(0)))
    
    def normalize_title(title):
        original_title = title
        if title.count('_') >= 2:
            title = re_underscores.sub(' ', title)
        title = re_extensions.sub('', title)
        if title.count('.') >= 2:
            title = re_dots.sub(' ', title)
        title = re_tags.sub('', title)
        title = re_spaces_greedy.sub(' ', title)

        episode_number = None
        for re_episode_number in re_episode_number_variants:
            result = re_episode_number.search(title)
            if result:
                episode_number, = result.groups()
                episode_number = int(episode_number)
                title = re_episode_number.sub(' — \\1 ', title)
                break
        
        title = re_solo_hyphens.sub(' — ', title)
        title = re_multiple_bangs.sub('!', title)
        title = re_greedy_numbers.sub(normalize_number, title)
        
        title = title.strip()
        return (title or original_title, episode_number)
    return normalize_title

normalize_title = build_normalize_title()

def torrents(num_days = 2, offset = 0):
    days = [{} for _ in range(num_days)]
    
    ts_now = datetime.utcnow()
    ts_ceil = ts_now - timedelta(days = num_days * offset)
    ts_floor = ts_ceil - timedelta(days = num_days)
    
    with MongoClient(mongodb_url) as client:
        collection = client.sashok.torrents
        for torrent in collection.find({ '$and': [{ 'timestamp': { '$lte': ts_ceil } }, { 'timestamp': { '$gte': ts_floor } }] }):
            del torrent['_id']
            day_id = (ts_now - torrent['timestamp']).days - num_days * offset
            torrent['timestamp'] = calendar.timegm(torrent['timestamp'].utctimetuple())

            day = days[day_id]

            group_title, episode_number = normalize_title(torrent['title'])
            if group_title not in day:
                day[group_title] = { 'torrents': [], 'seeders': 0, 'leechers': 0, 'downloads': 0 }

            day[group_title]['episode'] = episode_number
            day[group_title]['torrents'].append(torrent)
            day[group_title]['seeders'] += int(torrent['seeders'])
            day[group_title]['leechers'] += int(torrent['leechers'])
            day[group_title]['downloads'] += int(torrent['downloads'])

    for index, day in enumerate(days):
        groups = []
        for group_title in day.keys():
            groups.append(dict(day[group_title], **{ 'title': group_title }))
        days[index] = groups

    if debug.local_run(): return json.dumps(days, indent = 2)
    else: return json.dumps(days)