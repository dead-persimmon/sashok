import flask
app = flask.Flask(__name__)

import mimetypes
mimetypes.add_type('text/html', '.angular')

@app.route('/')
def torrents_by_day():
    return app.send_static_file('torrents_by_day.angular')

@app.route('/torrents/<day_delta>')
def torrents(day_delta):
    from torrents import torrents_for_day
    return flask.Response(torrents_for_day(day_delta), mimetype = 'application/json', status = '200')
    
if __name__ == '__main__':
    app.run(debug = True)