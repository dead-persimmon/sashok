#!/usr/bin/env python

import os

def request_env(environment):
	return '\n'.join(['%s == %s' % (key, value) for key, value in environment.items()])

def request_root(environment):
	return '/'

def application(environment, start_response):
	request_map = {'/': request_root, '/env': request_env}
	
	request = environment['PATH_INFO']
	if request in request_map.keys(): reply = request_map[request](environment)
	else: reply = 'invalid request'

	response_body = '<html><body><pre>%s</pre></body></html>' % reply

	status = '200 OK'
	response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(response_body)))]

	start_response(status, response_headers)
	return [response_body.encode('utf-8')]

if __name__ == '__main__':
	from wsgiref.simple_server import make_server
	httpd = make_server('localhost', 8051, application)
	# Wait for a single request, serve it and quit.
	httpd.handle_request()