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
    
    re_episode_number_variants = [re.compile('(?: - )([0-9]+)(?:v[0-9]+)? '), re.compile(' ep?([0-9]+)(?:v[0-9]+)? ', re.I)]
    re_volume_number_variants = [re.compile('\s*-?\s*vol\.?\s*([0-9]+)', re.I)]
    
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
                title = re_episode_number.sub(' ', title)
                break
        
        for re_volume_number in re_volume_number_variants:
            title = re_volume_number.sub(' Vol. \\1', title)
        
        title = re_solo_hyphens.sub(' — ', title)
        title = re_multiple_bangs.sub('!', title)
        title = re_greedy_numbers.sub(normalize_number, title)
        
        title = title.strip()
        return (title or original_title, episode_number)
    return normalize_title

normalize_title = build_normalize_title()

def global_downloads():
    groups = {}
    with MongoClient(mongodb_url) as client:
        collection = client.sashok.torrents
        for torrent in collection.find():
            group_title, episode_number = normalize_title(torrent['title'])
            if group_title not in groups:
                groups[group_title] = { 'downloads': 0, 'num_files': 0 }
            groups[group_title]['downloads'] += int(torrent['downloads'])
            groups[group_title]['num_files'] += 1
            
    filtered_groups = []
    for key in groups.keys():
        group = groups[key]
        if group['num_files'] >= 10:
            filtered_groups.append(dict({'title': key, 'downloads_per_file': group['downloads'] // group['num_files']}, **group))
    return json.dumps(filtered_groups, indent = 2)
            
def torrents(num_days = 2, offset = 0):
    days = [{} for _ in range(num_days)]
    
    ts_now = datetime.utcnow()
    ts_ceil = ts_now - timedelta(days = num_days * offset)
    ts_floor = ts_ceil - timedelta(days = num_days)
    
    with MongoClient(mongodb_url) as client:
        collection = client.sashok.torrents
        for torrent in collection.find({ '$and': [{ 'timestamp': { '$lte': ts_ceil } }, { 'timestamp': { '$gte': ts_floor } }] }):
            day = days[(ts_now - torrent['timestamp']).days - num_days * offset]
            
            #torrent['timestamp'] = calendar.timegm(torrent['timestamp'].utctimetuple())
            
            group_title, episode_number = normalize_title(torrent['title'])
            group_id = group_title + ' EP:' + str(episode_number) if episode_number else group_title
            
            if group_id not in day.keys():
                day[group_id] = { 'title': group_title, 'torrents': [], 'seeders': 0, 'leechers': 0, 'downloads': 0 }

            day[group_id]['episode'] = episode_number
            day[group_id]['torrents'].append(torrent)
            day[group_id]['seeders'] += int(torrent['seeders'])
            day[group_id]['leechers'] += int(torrent['leechers'])
            day[group_id]['downloads'] += int(torrent['downloads'])
            
            del torrent['_id']
            del torrent['timestamp']

    for index, day in enumerate(days):
        groups = []
        for group_id in day.keys():
            groups.append(dict(day[group_id], **{ 'group_id': group_id }))
        days[index] = groups

    return json.dumps(days, indent = 2)
 
if __name__ == '__main__':
    print( global_downloads() )