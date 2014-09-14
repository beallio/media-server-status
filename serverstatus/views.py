import datetime
import json

from flask import render_template, Response, request

from serverstatus import app
from assets import apifunctions, services


plex = None
api_functions = None


@app.route('/')
@app.route('/index')
def index():
    t1 = datetime.datetime.now()
    return render_template('index.html',
                           time=datetime.datetime.now() - t1)


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
    f = render_template(data + '.html', values=values)
    return Response(f, status=status, mimetype='text/plain')


@app.route('/img/<data>')
def get_img_data(data):
    _load_APIs()
    global plex
    if plex is None:
        plex = services.Plex(app.config['PLEX_INFO'])
    resp = Response('null', status=404, mimetype='text/plain')
    query_string = request.query_string
    data_low = data.lower()
    if data_low == 'plex':
        status = 200
        img_resp = plex.getCoverImage(query_string)
    elif data_low == 'subsonic':
        status = 200
        img_resp = None
    else:
        return resp
    resp = Response(img_resp, status=status, mimetype='image/jpeg')
    return resp


def _get_data(data):
    values = None
    status = 404
    _load_APIs()
    try:
        values = getattr(api_functions, str(data))()
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