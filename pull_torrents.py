__LOCAL = False

if __LOCAL:
	mongodb_url = 'mongodb://localhost:27017/'
else:
	import os
	mongodb_url = os.environ['OPENSHIFT_MONGODB_DB_URL']

from pymongo import MongoClient
from datetime import datetime, timedelta
import calendar
import json

def pull_torrents(num_days = 3):
	ts_now = datetime.utcnow()
	
	data = dict()
	
	with MongoClient(mongodb_url) as client:
		collection = client.sashok.torrents
		for torrent in collection.find({'timestamp': {'$gt': (ts_now - timedelta(days = num_days))}}):
			day = (ts_now - torrent['timestamp']).days
			if not day in data.keys(): data[day] = []
			unix_timestamp = calendar.timegm(torrent['timestamp'].utctimetuple())
			data[day].append({'title': torrent['title'], 'link': torrent['torrent_link'], 'timestamp': unix_timestamp, 'seeders': torrent['seeders'], 'leechers': torrent['leechers'], 'downloads': torrent['downloads']})

	for key in data.keys():
		data[key].sort(key = lambda torrent: -int(torrent['downloads']))
	return json.dumps(data)

#with open('test.json', 'a') as f:
#	f.write(pull_torrents(3))