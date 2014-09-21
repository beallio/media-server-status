import json
import datetime

from flask import render_template, Response, request

from serverstatus import app
from assets import apifunctions


@app.route('/')
@app.route('/index')
def index():
    start_time = datetime.datetime.now()
    return render_template('index.html',
                           time=datetime.datetime.now() - start_time,
                           testing=app.config['TESTING'])


@app.route('/api/<data>', methods=['GET'])
def get_json(data):
    values, status = BACKENDCALLS.get_data(data)
    json_data = json.dumps(values)
    # set mimetype to prevent client side manipulation since we're not using
    # jsonify
    return Response(json_data, status=status, mimetype='application/json')


@app.route('/html/<data>')
def html_generator(data):
    values, status = BACKENDCALLS.get_data(data)
    start = datetime.datetime.now()
    rendered_html = render_template(data + '.html', values=values)
    app.logger.debug(
        'Render time for {}: {}'.format(data, datetime.datetime.now() - start))
    # set mimetype to prevent users browser from rendering rendered HTML
    return Response(rendered_html, status=status, mimetype='text/plain')


@app.route('/img/<data>')
def get_img_data(data):
    start = datetime.datetime.now()
    resp = BACKENDCALLS.get_image_data(request)
    app.logger.debug('Image request time for {}: {}'
                     .format(data, datetime.datetime.now() - start))
    return resp


class BackEndCalls(object):
    """
    Provides access points into the API Functions of the backend.
    Also loads API configs to remedy issues where the config hasn't been
    loaded for a particular server.

    Provides access for images requests to Plex and Subsonic
    """

    def __init__(self):
        self.api_functions = None
        self.api_functions = self.get_api_functions()

    def get_api_functions(self):
        """
        Provides access to API Functions module through class
        :return: API_Functions
        """
        self._load_apis()
        return self.api_functions

    def get_data(self, data):
        """
        From flask request at http://servername.com/api/{api_call} fetches
        {api_call} from apifunctions module, and returns data.

        Disallows public access to any function in apifunctions starting with
        "_" (underscore)
        :type data: unicode or LocalProxy
        :return:
        """
        values = None
        status = 404
        values = getattr(self.api_functions, str(data).lstrip('_'))()
        status = 200
        """
        try:
            values = getattr(self.api_functions, str(data).lstrip('_'))()
            status = 200
        except (AttributeError, TypeError) as err:
            app.logger.error(err)
            # no api function for call, return empty json
        except:
            app.logger.error('An unknown error occurred')"""
        return values, status

    def get_image_data(self, flask_request):
        """
        Parses flask request from
        http://servername.com/img/{plex | subsonic}?14569852 where
        {plex|subsonic} is the server requested.  Routes request to appropriate
        server to get thumbnail image data

        :type flask_request: werkzeug.local.LocalProxy
        :return:
        """
        resp = Response('null', status=404, mimetype='text/plain')
        # convert to string since flask requests returns unicode
        data_low = str(flask_request.view_args.get('data', None).lower())
        if data_low == 'plex':
            resp = Response(
                self.api_functions._get_plex_cover_art(flask_request.args),
                status=200,
                mimetype='image/jpeg')
        elif data_low == 'subsonic':
            resp = Response(self._check_subsonic_request(flask_request),
                            status=200,
                            mimetype='image/jpeg')
        return resp

    def _load_apis(self):
        """
        Check if api_functions is set, set if not.

        :return:
        """
        if self.api_functions is None:
            self.api_functions = apifunctions.APIFunctions(app.config)

    def _check_subsonic_request(self, request_args):
        """
        Parses flask request to determine parameters for requesting cover art
        from Subsonic server

        :type request_args: werkzeug.local.LocalProxy
        :return: binary
        """
        query_string = request_args.query_string
        args = request_args.args
        try:
            # check if only cover id was submitted
            # e.g. /img/subsonic?28102
            cover_id = int(query_string)
            cover_size = None
        except ValueError:
            try:
                # check if cover id is included in request_args
                # e.g. /img/subsonic?cover=28102
                cover_id = args['cover']
            except KeyError:
                # we need a cover to look up
                raise
            try:
                # check if cover size is included in request_args
                # e.g. /img/subsonic?cover=28102&size=145
                cover_size = args['size']
                try:
                    # check if cover size is an integer
                    cover_size = int(cover_size)
                except ValueError:
                    # incorrect cover size requested
                    cover_size = None
            except KeyError:
                # cover size not included in request_args
                cover_size = None
        return self.api_functions._get_subsonic_cover_art(cover_id, cover_size)


BACKENDCALLS = BackEndCalls()
