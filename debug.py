import os

def local_run():
	return os.path.isfile('local.debug')

def get_mongodb_url():
    return 'mongodb://localhost:27017/' if local_run() else os.environ['OPENSHIFT_MONGODB_DB_URL']
