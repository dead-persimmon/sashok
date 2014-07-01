﻿import debug

if debug.local_run():
    mongodb_url = 'mongodb://localhost:27017/'
else:
    import os
    mongodb_url = os.environ['OPENSHIFT_MONGODB_DB_URL']

from pymongo import MongoClient
from datetime import datetime, timedelta
import calendar
import json

def pull_torrents(num_days = 2, offset = 0):
    torrents = dict()

    ts_now = datetime.utcnow()
    
    ts_ceil = ts_now - timedelta(days = num_days * offset)
    ts_floor = ts_ceil - timedelta(days = num_days)
    
    with MongoClient(mongodb_url) as client:
        collection = client.sashok.torrents
        for torrent in collection.find({ '$and': [{ 'timestamp': { '$lte': ts_ceil } }, { 'timestamp': { '$gte': ts_floor } }] }):
            day = (ts_now - torrent['timestamp']).days
            if not day in torrents.keys(): torrents[day] = []
            torrent['timestamp'] = calendar.timegm(torrent['timestamp'].utctimetuple())
            del torrent['_id']
            torrents[day].append(torrent)

    #for key in data.keys():
    #    data[key].sort(key = lambda torrent: -int(torrent['downloads']))
    return json.dumps(torrents)

#with open('pull_torrents', 'w+') as f:
#    f.write(pull_torrents(10, 0))