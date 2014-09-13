import datetime
import json

from flask import render_template, Response

from serverstatus import app
from assets import apifunctions


@app.route('/')
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


def _get_data(data):
    values = None
    status = 404
    try:
        values = getattr(apifunctions, data)()
        status = 200
    except (AttributeError, TypeError) as e:
        app.logger.error(e)
        # no api function for call, return empty json
    except:
        app.logger.error('An unknown error occurred')
    return values, status