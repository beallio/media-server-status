import datetime

import flask

from app import app, test_data
import app.assets.api_functions as api_functions


@app.route('/')
@app.route('/index')
def index():
    t1 = datetime.datetime.now()
    results = api_functions.media_results()
    status = api_functions.server_status()
    system_info = api_functions.system_info()
    storage = api_functions.storage()
    return flask.render_template('index.html',
                                 subsonic_info=test_data.SUBSONIC_INFO,
                                 plex_info=test_data.PLEX_INFO,
                                 results=results,
                                 server_status=status,
                                 sys_info=system_info,
                                 storage=storage['paths'],
                                 total_storage=storage['total'],
                                 plex_transcodes=0,
                                 time=datetime.datetime.now() - t1)


@app.route('/api/<data>', methods=['GET'])
def get_info(data):
    try:
        values = getattr(api_functions, data)()
    except AttributeError:
        # no api function for call, return empty json
        values = dict()
    return flask.jsonify(**values)
