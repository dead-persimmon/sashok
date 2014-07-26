#!/usr/bin/env python

import debug, os, cgi, html

BAD_REQUEST = ('400 Bad Request', [('Content-Type', 'text/html')], 'Nope!')

def request_root(env):
    response_status = '200 OK'
    response_headers = [('Content-Type', 'text/html')]
    if debug.local_run(): response_body = open('index.html', 'rb').read()
    else: response_body = open(env['OPENSHIFT_REPO_DIR'] + 'index.html', 'rb').read()
    return (response_status, response_headers, response_body)

def request_torrents(env):
    query = cgi.parse(None, env)
    if 'num_days' in query.keys() and 'offset' in query.keys():
        from torrents import torrents
        response_status = '200 OK'
        response_headers = [('Content-Type', 'application/json')]
        response_body = torrents(int(query['num_days'][0]), int(query['offset'][0]))
    else:
        return BAD_REQUEST
    return (response_status, response_headers, response_body)

def application(env, start_response):
    allowed_requests = {'/': request_root, '/torrents': request_torrents}

    request = env['PATH_INFO']
    if request in allowed_requests.keys(): response_status, response_headers, response_body = allowed_requests[request](env)
    else: response_status, response_headers, response_body = BAD_REQUEST

    if type(response_body) != bytes:
        response_body = response_body.encode('utf-8')
    start_response(response_status, response_headers)
    return [response_body]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    for _ in range(2):
        httpd.handle_request()