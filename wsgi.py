#!/usr/bin/env python

import html
import os

def request_env(environment):
	#lines = []
	#max_key_width = len(max(environment.keys(), key = lambda x: len(x)))
	#for key, value in sorted(environment.items()):
	#	lines += [('{:>%d}   {}' % max_key_width).format(key, html.escape(str(value)))]
	#return '\n'.join(lines)
	return '_'

def request_torrents(environment):
	from pull_torrents import pull_torrents
	return pull_torrents(3)

def request_root(environment):
	return open(environment['OPENSHIFT_REPO_DIR'] + 'index.html', 'rb').read()

def application(environment, start_response):
	request_map = {'/': request_root, '/env': request_env, '/pull_torrents': request_torrents}
	
	request = environment['PATH_INFO']
	if request in request_map.keys(): reply = request_map[request](environment)
	else: reply = 'invalid request'

	status = '200 OK'
	response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(reply)))]

	start_response(status, response_headers)
	return [reply]

if __name__ == '__main__':
	from wsgiref.simple_server import make_server
	httpd = make_server('localhost', 8051, application)
	# Wait for a single request, serve it and quit.
	httpd.handle_request()