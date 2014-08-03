import flask
app = flask.Flask(__name__)

import mimetypes
mimetypes.add_type('text/html', '.angular')

@app.route('/')
def torrents_by_day():
    return app.send_static_file('index.angular')

@app.route('/torrents/<day_delta>')
def get_torrents(day_delta):
    from torrents import get_torrents
    return flask.jsonify(get_torrents(day_delta))
    
if __name__ == '__main__':
    app.run(debug = True)