import json

from flask import render_template, Response, request

from serverstatus import app
from assets import apifunctions


api_functions = None

import datetime

@app.route('/')
@app.route('/index')
def index():
    t1 = datetime.datetime.now()
    return render_template('index.html',
                           time=datetime.datetime.now() - t1,
                           testing=app.config['TESTING'])


@app.route('/api/<data>', methods=['GET'])
def get_json(data):
    values, status = _get_data(data)
    # flask.jsonify(**values)
    js = json.dumps(values)
    # set mimetype to prevent client side manipulation since we're not using jsonify
    return Response(js, status=status, mimetype='application/json')


@app.route('/html/<data>')
def html_generator(data):
    values, status = _get_data(data)
    start = datetime.datetime.now()
    f = render_template(data + '.html', values=values)
    app.logger.debug('Render time for {}: {}'.format(data, datetime.datetime.now() - start))
    return Response(f, status=status, mimetype='text/plain')


@app.route('/img/<data>')
def get_img_data(data):
    start = datetime.datetime.now()
    global api_functions
    _load_APIs()
    resp = Response('null', status=404, mimetype='text/plain')
    query_string = request.query_string
    data_low = data.lower()
    if data_low == 'plex':
        status = 200
        img_resp = api_functions._get_plex_cover_art(query_string)
    elif data_low == 'subsonic':
        img_resp = _check_subsonic_request(request)
        status = 200
    else:
        return resp
    resp = Response(img_resp, status=status, mimetype='image/jpeg')
    app.logger.debug('Image request time for {}: {}'.format(data, datetime.datetime.now() - start))
    return resp


def _get_data(data):
    values = None
    status = 404
    _load_APIs()
    try:
        values = getattr(api_functions, str(data).lstrip('_'))()
        status = 200
    except (AttributeError, TypeError) as e:
        app.logger.error(e)
        # no api function for call, return empty json
    except:
        app.logger.error('An unknown error occurred')
    return values, status


def _load_APIs():
    global api_functions
    if api_functions is None:
        api_functions = apifunctions.APIFunctions(app.config)


def _check_subsonic_request(request):
    query_string = request.query_string
    args = request.args
    try:
        # check if only cover id was submitted
        # e.g. /img/subsonic?28102
        cover_id = int(query_string)
        cover_size = None
    except ValueError:
        try:
            # check if cover id is included in request
            # e.g. /img/subsonic?cover=28102
            cover_id = args['cover']
        except KeyError:
            # we need a cover to look up
            raise
        try:
            # check if cover size is included in request
            # e.g. /img/subsonic?cover=28102&size=145
            cover_size = args['size']
            try:
                # check if cover size is an integer
                cover_size = int(cover_size)
            except ValueError:
                # incorrect cover size requested
                cover_size = None
        except KeyError:
            # cover size not included in request
            cover_size = None
    return api_functions._get_subsonic_cover_art(cover_id, cover_size)