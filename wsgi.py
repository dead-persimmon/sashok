#!/usr/bin/env python

import debug
import html
import os

#def request_env(environment):
#    lines = []
#    max_key_width = len(max(environment.keys(), key = lambda x: len(x)))
#    for key, value in sorted(environment.items()):
#        lines += [('{:>%d}   {}' % max_key_width).format(key, html.escape(str(value)))]
#    return '<html><body><pre>%s</pre></body></html>' % '\n'.join(lines)

def request_torrents(environment):
    if debug.local_run():
        return open('pull_torrents', 'rb').read()
    else:
        import cgi
        query = cgi.parse(None, environment)
        if 'num_days' in query.keys() and 'offset' in query.keys():
            from pull_torrents import pull_torrents
            return pull_torrents(int(query['num_days'][0]), int(query['offset'][0])).encode('utf-8')
        else:
            # fix me
            return '{"0":[{"title":"Failed to pull torrents from the database, somehow."}]}'.encode('utf-8')

def request_root(environment):
    if debug.local_run(): return open('index.html', 'rb').read()
    else: return open(environment['OPENSHIFT_REPO_DIR'] + 'index.html', 'rb').read()

def application(environment, start_response):
    request_map = {'/': request_root, '/pull_torrents': request_torrents}
    
    request = environment['PATH_INFO']
    if request in request_map.keys(): reply = request_map[request](environment)
    else: reply = 'Try again!'

    status = '200 OK'
    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(reply)))]

    start_response(status, response_headers)
    return [reply]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    for _ in range(2):
        httpd.handle_request()