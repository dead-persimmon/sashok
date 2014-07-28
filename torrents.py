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
    from datetime import datetime
    from datetime import timedelta
    
    groups = {}
    with MongoClient(mongodb_url) as client:
        collection = client.sashok.torrents
        for torrent in collection.find():
            group_title, episode_number = normalize_title(torrent['title'])
            if group_title not in groups:
                groups[group_title] = { 'downloads': 0, 'num_files': 0, 'most_recent_file': datetime.min }
            group = groups[group_title]
            group['most_recent_file'] = max(group['most_recent_file'], torrent['timestamp'])
            group['downloads'] += int(torrent['downloads'])
            group['num_files'] += 1
            
    filtered_groups = []
    dt_now = datetime.now()
    
    for key in groups.keys():
        group = groups[key]
        most_recent_file = (dt_now - group['most_recent_file']).days
        if group['num_files'] > 1 and most_recent_file <= 10:
            group['most_recent_file'] = most_recent_file
            filtered_groups.append(dict({'title': key, 'downloads_per_file': group['downloads'] // group['num_files']}, **group))
    return json.dumps(filtered_groups, indent = 2)
            
def torrents(day_delta = 0):
    day_floor = datetime.utcnow().date() - timedelta(days = day_delta)
    day_ceil = datetime.combine(day_floor, datetime.max.time())
    day_floor = datetime.combine(day_floor, datetime.min.time())
    
    groups = {}
    
    with MongoClient(mongodb_url) as client:
        collection = client.sashok.torrents
        for torrent in collection.find({ '$and': [{ 'timestamp': { '$lte': day_ceil } }, { 'timestamp': { '$gte': day_floor } }] }):
            #torrent['timestamp'] = calendar.timegm(torrent['timestamp'].utctimetuple())
            
            group_title, episode_number = normalize_title(torrent['title'])
            group_id = ''.join((group_title, ' [EP:', str(episode_number), ']')) if episode_number else group_title
            
            if group_id not in groups.keys():
                groups[group_id] = { 'title': group_title, 'torrents': [], 'seeders': 0, 'leechers': 0, 'downloads': 0 }

            groups[group_id]['episode'] = episode_number
            groups[group_id]['torrents'].append(torrent)
            groups[group_id]['seeders'] += int(torrent['seeders'])
            groups[group_id]['leechers'] += int(torrent['leechers'])
            groups[group_id]['downloads'] += int(torrent['downloads'])
            
            del torrent['_id']
            #del torrent['timestamp']
            torrent['timestamp'] = torrent['timestamp'].strftime("%Y-%m-%d %H:%M:%S")

    groups_array = []
    for group_id in groups.keys():
        groups_array.append(dict(groups[group_id], **{ 'group_id': group_id }))

    return json.dumps(groups_array)
 
if __name__ == '__main__':
    print( torrents() )