import debug

if debug.local_run():
    mongodb_url = 'mongodb://localhost:27017/'
else:
    import os
    mongodb_url = os.environ['OPENSHIFT_MONGODB_DB_URL']

from pymongo import MongoClient
from sashok_tools import normalize_filename

data = {}

with MongoClient(mongodb_url) as client:
    collection = client.sashok.torrents
    for torrent in collection.find():
        normalized, tags, original = normalize_filename(torrent['title'])
        if normalized in data: data[normalized].append(original)
        else: data[normalized] = [original]

import json
print ( json.dumps(data) )