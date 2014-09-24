import os
import logging
import urllib2
import urlparse
from collections import OrderedDict
from operator import itemgetter
from time import localtime, strftime
import datetime
from cStringIO import StringIO

from PIL import Image, ImageOps
import libsonic
import xmltodict

from serverstatus import app
import serverstatus.assets.exceptions as exceptions


LOGGER = logging.getLogger(__name__)


class Service(object):
    def __init__(self, service_info):
        assert type(service_info) is dict
        self.logger = LOGGER
        self.logger.debug(
            '{} class initialized'.format(self.__class__.__name__))
        self.server_info = service_info
        self._services_status_mapping = self._get_status_mappings_dict()
        self._service_name = None
        self._connect_status = None
        self._server_full_url = None
        self._resolved_status_mapping = dict()
        self._temp_img_dir = app.config.get('TEMP_IMAGES', '/tmp')

    @property
    def service_name(self):
        return self._service_name

    @property
    def get_status_mapping(self):
        self._resolved_status_mapping = self._get_status_mapping()
        return self._resolved_status_mapping

    @property
    def get_connection_status(self):
        self._connect_status = self._test_server_connection()
        return self._connect_status

    @property
    def get_server_full_url(self):
        return self._server_full_url

    @property
    def get_external_url(self):
        return self._get_config_attrib('external_url')

    @staticmethod
    def convert_date(dt_obj, in_format, out_format):
        dt_value = datetime.datetime.strptime(dt_obj, in_format)
        return dt_value.strftime(out_format)

    def _test_server_connection(self):
        # method to be overridden by subclasses
        return

    def _get_status_mapping(self):
        service_name = self._service_name
        output = {service_name: dict()}
        try:
            output = {service_name: self._services_status_mapping[
                str(self._connect_status)]}
            output[service_name][
                'title'] = self._add_service_name_to_status_mapping()
            if self.get_external_url:
                output[service_name]['external_url'] = self.get_external_url
        except KeyError:
            pass
        return output

    def _add_service_name_to_status_mapping(self):
        delim = '-'
        service_name = self._service_name
        if delim in service_name:
            title = service_name.split(delim)
            title = ' '.join([w.title() for w in title])
        else:
            title = service_name.title()
        return title

    def _get_config_attrib(self, attrib):
        try:
            return self.server_info[attrib]
        except KeyError:
            # Config attribute not found
            return None

    @staticmethod
    def _get_status_mappings_dict():
        return dict(
            False=dict(
                text='Offline',
                icon='icon-off icon-white',
                css_class='btn_mod btn btn-xs btn-danger',
            ),
            True=dict(
                text='Online',
                icon='icon-ok icon-white',
                css_class='btn_mod btn btn-xs btn-success',
            ),
            ServerSyncActive=dict(
                text='Online',
                icon='icon-download icon-white',
                css_class='btn_mod btn btn-xs btn-success',
            ),
            BackupServerActive=dict(
                text='Active',
                icon='icon-upload icon-white',
                css_class='btn_mod btn btn-xs btn-success',
            ),
            Waiting=dict(
                text='Pending',
                icon='icon-pause icon-white',
                css_class='btn_mod btn btn-xs btn-warning',
            )
        )

    def _log_warning_for_missing_config_value(self, cls_name, config_val,
                                              default):
        # Log warning that config value for plex is missing from config file.
        # Using default value instead
        self.logger.warning(
            ('{config_val} missing from config value for {cls_name}. '
             'Using {default} instead').
            format(cls_name=cls_name, default=default, config_val=config_val))

    @staticmethod
    def _convert_xml_to_json(resp_output):
        return xmltodict.parse(resp_output)

    @staticmethod
    def _build_external_img_path(service_name):
        base_path = 'img/'
        return ''.join([base_path, service_name, '?'])

    def _test_file_path(self, file_path_key):
        # //TODO Needed
        output = None
        try:
            file_path = self.server_info[file_path_key]
            if os.path.exists(file_path):
                output = file_path
        except KeyError as err:
            self.logger.error(err)
        finally:
            return output

    """
    @staticmethod
    def _strip_base_path(filepath):
        return filepath.replace(app.config['APP_MODULESLOCATION'], '').lstrip(
            '/')


    def _get_img_directory(self, subpath=None):
        #Creates absolutely directory path for temp images

        #:param subpath:
        #:return: string
        if subpath is None:
            subpath = ''
        dir_short = os.path.join(self._temp_img_dir, subpath)
        abs_path = os.path.join(app.config['APPLOCATION'], dir_short)
        if not os.path.isdir(abs_path):
            self.logger.info(
                'Directory not found. Creating directory: {}'.format(abs_path))
            try:
                os.makedirs(abs_path)
            except IOError as e:
                self.logger.error(e)
                raise IOError
        return abs_path


    """


class SubSonic(Service):
    def __init__(self, server_info):
        Service.__init__(self, server_info)
        self._service_name = 'subsonic'
        self.conn = libsonic.Connection(baseUrl=self.server_info['url'],
                                        username=self.server_info['user'],
                                        password=self.server_info['password'],
                                        port=self.server_info['port'],
                                        appName=self.server_info['appname'],
                                        apiVersion=self.server_info['api'],
                                        serverPath=self.server_info[
                                            'serverpath'])
        self._connect_status = self._test_server_connection()
        self._server_full_url = self._get_server_full_url()
        self._resolved_status_mapping = self._get_status_mapping()
        self._img_base_url = self._build_external_img_path(
            self._service_name) + 'cover='

    def getNowPlayingOrRecentlyAdded(self, num_of_results=None):
        if num_of_results is None:
            num_of_results = 9
        entries = {}
        now_playing_count = 0
        if not self._connect_status:
            return
        try:
            entries['now_playing'] = self.now_playing()
            now_playing_count = len(entries['now_playing'])
            if now_playing_count > num_of_results:
                entries['now_playing'] = entries['now_playing'][:num_of_results]
        except TypeError:
            pass
        finally:
            if now_playing_count < num_of_results:
                entries['recently_added'] = self.recently_added(
                    num_results=num_of_results)
                recently_added_count = len(entries['recently_added'])
                show_recently_added = recently_added_count - now_playing_count
                entries['recently_added'] = \
                    entries['recently_added'][:show_recently_added]
        return entries

    def recently_added(self, num_results=None):
        """
        Returns recently added entries.

        :param num_results: number of recently added results to return
        :type num_results: int
        :return: list of [dict]
        """

        def recently_added_generator(num):
            recently_added = self.conn.getAlbumList("newest", num)['albumList'][
                'album']
            for entry in recently_added:
                yield entry
            return

        if num_results is None:
            num_results = 10
        return [self._get_entry_info(entry) for entry in
                recently_added_generator(num_results)]

    def get_cover_art(self, cover_art_id, size=None):
        assert type(cover_art_id) is int
        if any([size is None, size <= 0, type(size) is not int]):
            return self.conn.getCoverArt(aid=cover_art_id)
        else:
            if size > 2000:
                # set max limit on size of photo returned
                size = 2000
            return self.conn.getCoverArt(aid=cover_art_id, size=size)

    def now_playing(self):
        """
        Returns now playing entries from Subsonic server in list format.  Each
        entry in list represents one song currently playing from server.  Each
        entry in list is a dict

        :returns: list of [dict]
        """
        entries = []
        nowplaying = self.conn.getNowPlaying()
        # multiple songs playing
        how_many_playing = type(nowplaying['nowPlaying']['entry'])
        if how_many_playing == list:
            entries = [self._get_entry_info(entry) for entry in
                       nowplaying['nowPlaying']['entry']]
        # single song playing
        elif how_many_playing == dict:
            entries.append(
                self._get_entry_info(nowplaying['nowPlaying']['entry']))
        # remove entries from now playing if user hasn't touched them or
        # playlist auto advanced in X min
        entries = [entry for entry in entries if entry['minutesAgo'] <= 10]
        return entries

    def set_output_directory(self, directory):
        # //TODO remove extraneous code
        self._temp_img_dir = directory
        return self._temp_img_dir == directory

    def _test_server_connection(self):
        """
        Test if we're able to connect to Subsonic server.

        :return: bool - True if able to connect, false otherwise
        :raise: exceptions.SubsonicConnectionError
        """
        connection_status = False
        try:
            connection_status = self.conn.ping()
            assert connection_status
        except AssertionError:
            err = 'Unable to reach Subsonic server'
            self.logger.error()
            raise exceptions.SubsonicConnectionError(err)
        finally:
            return connection_status

    def _create_cover_art_file(self, cover_art_id, size=None):
        """
        size in get_cover_art method for subsonic returns a square image with
        dimensions in pixels equal to size
        :param cover_art_id:
        :return:
        """
        # set default image size in pixels
        if size is None:
            size = 600
        img_data = self.conn.getCoverArt(aid=cover_art_id, size=size)
        cover_dir = self._temp_img_dir  # temp storage for created image files
        filename = 'cover'
        ext = '.jpg'
        short_filepath = filename + str(cover_art_id) + '_' + str(size) + ext
        full_filepath = os.path.join(cover_dir, short_filepath)
        if not os.path.exists(cover_dir):
            # check if filepath exists.  Attempt to create if it doesn't
            try:
                os.mkdir(cover_dir)
            except IOError:
                self.logger.error(
                    'Failed to create cover art directory: {}'.format(
                        full_filepath))
                return
        if not os.path.isfile(full_filepath):
            self.logger.info('Write cover art file: {}'.format(full_filepath))
            with open(full_filepath, 'wb') as img_file:
                img_file.write(img_data.read())
        return full_filepath

    def _get_entry_info(self, entry, min_size=None, max_size=None):
        """
        appends URL coverart link to Subsonic entry dict
        :param entry: subsonic entry
        :type entry: dict
        :return: dict
        """
        assert type(entry) == dict
        if min_size:
            min_size = 145
        if max_size:
            max_size = 500
        # create url link to thumbnail coverart, and full-size coverart
        cover_art_link = [''.join([self._img_base_url, str(entry['coverArt']),
                                   '&size=', str(size)]) for size in
                          (min_size, max_size)]
        entry.update(coverArtExternalLink_sm=cover_art_link[0],
                     coverArtExternalLink_xl=cover_art_link[1])
        created_date = self.convert_date(entry[u'created'], '%Y-%m-%dT%H:%M:%S',
                                         '%m/%d/%Y %I:%M%p')
        entry[u'created'] = created_date
        try:
            # Return progress on currently playing song(s).  No good way to do
            # this since Subsonic doesn't have access to this info through
            # it's API.  Calculate progress by taking last time
            # song was accessed divide by progress
            entry['progress'] = min(
                float(entry['minutesAgo']) / float(entry['duration'] / 60), 1)
        except KeyError:
            entry['progress'] = 1
        finally:
            entry.update(progress_pct='{:.2%}'.format(entry['progress']),
                         progress_whole=entry['progress'] * 100)
        return entry

    def _get_server_full_url(self):
        serverpath, _ = self.server_info['serverpath'].strip('/').split('/')
        return '{url}:{port:d}/{path}'.format(url=self.server_info['url'],
                                              port=self.server_info['port'],
                                              path=serverpath)


class CheckCrashPlan(Service):
    def __init__(self, server_info):
        Service.__init__(self, server_info)
        self._service_name = 'backups'
        self.file_path = self._test_file_path('logfile_path')
        self._connect_status = self._test_server_connection()
        self._resolved_status_mapping = self._get_status_mapping()

    def _test_server_connection(self):
        items_to_keep = ['scanning', 'backupenabled']
        with open(self.file_path, 'r') as log_file:
            items = [line.lower().split() for line in log_file.readlines()
                     for x in items_to_keep if x in line.lower()]
        # remove "=" from list
        for item in items:
            item.remove('=')
        items_values = [True if item[1] == 'true' else False for item in items]
        if all(items_values):
            return 'BackupServerActive'
        elif any(items_values):
            return 'Waiting'
        else:
            return False


class ServerSync(Service):
    def __init__(self, server_info):
        Service.__init__(self, server_info)
        self.server_info = server_info
        self.lockfile_path = self.server_info['lockfile_path']
        self._service_name = 'server-sync'
        self._connect_status = self._test_server_connection()
        self._resolved_status_mapping = self._get_status_mapping()

    def _test_server_connection(self):
        try:
            return os.path.exists(self.lockfile_path)
        except TypeError:
            self.logger.debug('Server Sync Lockfile does not exist at {}'.
                              format(self.lockfile_path))
            return False


class Plex(Service):
    """
    Note: Plex requires a PlexPass for access to the server API.  Plex won't
    allow you to connect to API otherwise

    Provides media metadata information from Plex
    """
    url_scheme = 'http://'

    def __init__(self, server_info):
        Service.__init__(self, server_info)
        assert type(server_info) is dict
        self.server_info = server_info
        self._service_name = 'plex'
        self.server_internal_url_and_port = self._get_full_url_and_port
        try:
            self._server_full_url = server_info['external_url']
        except KeyError as err:
            self.logger.error(
                'Missing config value {config_value} from {cls}'.format(
                    config_value='external_url',
                    cls=self.__class__.__name__))
            raise exceptions.MissingConfigValue(err)
        self._connect_status = self._test_server_connection()
        self._resolved_status_mapping = self._get_status_mapping()
        self._transcodes = 0
        self._cover_mapping = dict()
        self._img_base_url = self._build_external_img_path(self._service_name)

    def recently_added(self, num_results=None):
        """

        :type num_results: int or unknown
        :return: dict of [lists]
        """

        def process_video_data(videos):
            # sort the recently added list by date in descending order
            videos = sorted(videos, key=itemgetter('@addedAt'), reverse=True)
            # trim the list to the number of results we want
            videos_trimmed = videos[:num_results]
            return [self._get_video_data(video) for video in videos_trimmed]

        if not self._connect_status:
            return None
        if any([num_results is None, type(num_results) is not int]):
            # Check if correct for maximum number of results is entered
            # if not set default
            num_results = 6
        api_call = 'recentlyadded'
        json_data = self._get_xml_convert_to_json(api_call)
        # the media value we want are contained in lists so loop through the
        # MediaContainer, find the lists of data, and return each value in
        # the lists.  The lists contain Movies and Shows separately.

        movies = [media for value in json_data['MediaContainer'] if
                  type(json_data['MediaContainer'][value]) == list for
                  media in json_data['MediaContainer'][value] if
                  media['@type'] != 'season']
        tv_shows = [media for value in json_data['MediaContainer'] if
                    type(json_data['MediaContainer'][value]) == list for
                    media in json_data['MediaContainer'][value] if
                    media['@type'] == 'season']
        # remove extra data
        del json_data
        return dict(Movies=process_video_data(movies),
                    TVShows=process_video_data(tv_shows))

    def now_playing(self):
        """
        Returns now playing data from Plex server in a JSON-like dictionary

        :return: dict()
        """

        def generate_video_data(vid_data, api_call=None):
            """
            Generator function for creating relevant video data.  Takes JSON
            data, checks if is data is an OrderedDict
            then grabs the relevant data if the video is a TV show or Movie.
            """
            # In JSON form Plex returns multiple videos as a list of
            # OrderedDicts, and a single video as an OrderedDict
            # Convert the single video to a list for processing
            if type(vid_data) is OrderedDict:
                video_list = list()
                video_list.append(vid_data)
            elif type(vid_data) is list:
                video_list = vid_data
            else:
                # Plex returned data that we haven't seen before.
                # Raise exception to warn user.
                msg = (
                    'Plex returned API data that does not match to known '
                    'standards.Plex return data as {} when it should return a '
                    'list or OrderedDict').format(type(vid_data))
                self.logger.error(msg)
                raise exceptions.PlexAPIDataError(msg)
            for video in video_list:
                # Grab relevant data about Video from JSON data, send the API
                # call to calculate _transcodes, otherwise it will skip and
                # return 0
                yield self._get_video_data(video, api_call)
            return

        self._transcodes = 0  # reset serverinfo count
        api_call = 'nowplaying'
        now_playing_relevant_data = list()
        json_data = self._get_xml_convert_to_json(api_call)
        if not int(json_data['MediaContainer']['@size']):
            # Nothing is currently playing in plex
            return None
        for vid in generate_video_data(json_data['MediaContainer']['Video'],
                                       api_call):
            now_playing_relevant_data.append(vid)
        return now_playing_relevant_data

    def get_cover_image(self, plex_id, thumbnail=None, local=None):
        """
        Returns binary jpeg object for Plex item found local temp directory as
        set in config file.  Checks request argument against mapped value from
        Plex item ID

        :param plex_id: metadata coverart ID that corresponds to mapping
        dictionary
        :type plex_id: str
        :param thumbnail: boolean values that tells us to return thumbnail
        image if True.  Returns full scale image if False
        :type thumbnail: bool or NoneType
        :param local: boolean value that tells us to pull image from Plex
        server or return local copy
        :type local: bool or NoneType
        :return: binary
        :raises: exceptions.PlexImageError
        """

        def open_image(ext):
            try:
                return open(os.path.join(self._temp_img_dir, plex_id + ext),
                            'rb')
            except IOError as img_err:
                raise exceptions.PlexImageError(img_err)

        thumbnail = thumbnail is not None
        local = local is not None
        if self._cover_mapping is None:
            # if _cover_mapping is empty we need to initialize Now Playing
            self.now_playing()
        if thumbnail:
            resp = open_image('.thumbnail')
        elif local:
            resp = open_image('.jpg')
        else:
            try:
                resp = urllib2.urlopen(
                    urlparse.urljoin(self.server_internal_url_and_port,
                                     self._cover_mapping[plex_id]))
            except (TypeError, urllib2.HTTPError) as err:
                raise exceptions.PlexImageError(err)
        return resp

    @property
    def transcodes(self):
        """
        Returns number of current number of Plex transcode sessions

        >>> 0
        >>> 1

        :return: int
        """
        server_info = self.get_plex_server_info()
        self._transcodes = server_info.get('transcoderActiveVideoSessions', 0)
        return self._transcodes

    def get_plex_server_info(self):
        json_show_data = self._get_xml_convert_to_json('serverinfo')
        server_data = json_show_data.get('MediaContainer', None)
        data_dict = {str(key.strip('@')): server_data[key] for key in
                     server_data if type(server_data[key]) is unicode or
                     type(server_data[key]) is str}
        for key in data_dict:
            try:
                data_dict[key] = int(data_dict[key])
            except ValueError:
                if ',' in data_dict[key]:
                    split_values = data_dict[key].split(',')
                    data_dict[key] = [int(val) for val in split_values]
        return data_dict

    def _test_server_connection(self):
        """
        Test if connection to Plex is active or not
        >>> True
        >>> False
        :return: bool
        """
        resp = None
        try:
            if self.server_info['local_network_auth']:
                # local network authentication required
                # // TODO Need to complete code for authorization if necessary
                pass
        except KeyError:
            pass
        resp = self._get_plex_api_data('serverinfo')
        is_connectable = resp is not None
        if not is_connectable:
            self.logger.error('Could not connect to Plex server')
        return is_connectable

    def _get_api_url_suffix(self, the_data_were_looking_for):
        """
        https://code.google.com/p/plex-api/wiki/PlexWebAPIOverview
        contains information required Plex HTTP APIs

        serverinfo: Transcode bitrateinfo, myPlexauthentication info
        nowplaying: This will retrieve the "Now Playing" Information of the PMS.
        librarysections: Contains all of the sections on the PMS. This acts as
                        a directory and you are able to "walk" through it.
        prefs: Gets the server preferences
        servers: get the local List of servers
        ondeck: Show ondeck list
        channels_all: Returns all channels installed in Plex Server
        channels_recentlyviewed: Get listing of recently viewed channels
        recentlyadded: Gets listing of recently added media, in descending
                        order by date added
        metadata: Returns metadata from media, e.g. /library/metadata/<val>
                    when <val> is an integer tied to a specific episode or movie

        >>> '/library/recentlyAdded'

        :param the_data_were_looking_for:
        :return:
        """
        url_api_mapping = dict(
            serverinfo='/',
            nowplaying='/status/sessions',
            librarysections='/library/sections',
            prefs='/:/prefs',
            servers='/servers',
            ondeck='/library/onDeck',
            channels_all='/channels/all',
            recentlyadded='/library/recentlyAdded',
            metadata='/library/metadata/'
        )
        try:
            results = url_api_mapping[the_data_were_looking_for]
        except KeyError as err:
            self.logger.error(err)
            raise exceptions.PlexAPIKeyNotFound(err)
        return results

    @property
    def _get_full_url_and_port(self):
        """
        builds out internal url with port

        >>> 'http://localhost:32400'
        >>> 'http://192.168.0.1:32400'

        :return: str
        """
        port = str(self.server_info.get('internal_port', 32400))
        if port != self.server_info.get('internal_port'):
            self._log_warning_for_missing_config_value(
                cls_name=self.__class__.__name__, default=port,
                config_val='port')
        try:
            internal_url = self.server_info['internal_url'].replace(
                Plex.url_scheme, '').lstrip('/')
        except KeyError:
            internal_url = 'localhost'
            self._log_warning_for_missing_config_value(
                cls_name=self.__class__.__name__,
                default=internal_url, config_val='internal_url')
        return ''.join([Plex.url_scheme, internal_url, ':', port])

    def _get_plex_api_data(self, api_call, api_suffix=None):
        """
        Call plex api, and return XML data

        For /status/sessions:
        >>> '<MediaContainer size="0"></MediaContainer>'

        :param api_call:
        :return: str
        :raises: exceptions.PlexConnectionError
        """
        if api_suffix is None:
            # no extra api call for this
            api_suffix = ''
        try:
            full_api_call = ''.join(
                [self._get_api_url_suffix(api_call), api_suffix])
            resp = urllib2.urlopen(
                urlparse.urljoin(self.server_internal_url_and_port,
                                 full_api_call))
            output = resp.read()
        except urllib2.URLError as err:
            self.logger.error('Error connecting to Plex')
            raise exceptions.PlexConnectionError(err)
        else:
            resp.close()
        return output

    def _get_xml_convert_to_json(self, api_key, api_suffix=None):
        """
        Gets Plex data based on api key and converts Plex XML response to JSON
        format

        :type api_key: str
        :type api_suffix: unknown or str
        :return:
        """
        xml_data = self._get_plex_api_data(api_key, api_suffix)
        return self._convert_xml_to_json(xml_data)

    def _get_video_data(self, video, get_type=None):
        # need a separate dict for section mapping since Plex returns different
        # data for Now Playing and Recently Added
        library_section_mapping = {'1': 'Movies', '2': 'TV Shows'}
        # need a separate dict for section mapping since Plex returns different
        # data for Now Playing and Recently Added
        # all the video.gets below are to handle the different mappings
        # Plex sends for Now Playing/Recently Added.
        vidtype = video.get('@librarySectionTitle',
                            library_section_mapping.get(
                                video.get('@librarySectionID', 0)))
        if vidtype == 'TV Shows':
            video_data = self._get_tv_show_data(video, get_type)
        elif vidtype == 'Movies':
            release_date = video['@originallyAvailableAt']
            video_data = dict(showtitle=video['@title'],
                              summary=video['@summary'],
                              releasedate=self.convert_date(release_date,
                                                            '%Y-%m-%d',
                                                            '%m/%d/%Y'))
        else:
            # encountered an unexpected video type
            msg = 'Unexpected media type {} encountered'.format(vidtype)
            self.logger.error(msg)
            raise exceptions.PlexAPIDataError(msg)
        # add common elements to video dict
        plex_path_to_art = video['@thumb']
        self._save_cover_art(self.server_internal_url_and_port +
                             plex_path_to_art)
        arturlmapped_value = os.path.basename(plex_path_to_art)
        video_data.update(type=vidtype,
                          art_external_url=''.join([self._img_base_url,
                                                    arturlmapped_value]),
                          added_at=strftime('%m/%d/%Y %I:%M %p',
                                            localtime(int(video['@addedAt']))))
        # converts direct plex http link to thumbnail to internal mapping
        # security through obfuscation /s
        self._cover_mapping[arturlmapped_value] = plex_path_to_art
        video_data['rating'] = float(video.get('@rating', 0))
        if get_type == 'nowplaying':
            # only applicable if we want to retrieve now playing data from Plex
            try:
                # this is only relevant for videos that are currently playing
                video_data['progress'] = (float(video['@viewOffset']) / float(
                    video['@duration'])) * 100.0
            except KeyError:
                # video's not playing - not an issue
                video_data['progress'] = 0
                pass
        return video_data

    def _save_cover_art(self, cover_loc):
        # retrieve image data from Plex server metadata
        img_data = StringIO(urllib2.urlopen(
            urlparse.urljoin(self.server_internal_url_and_port,
                             cover_loc)).read())
        # pull temporary image directory location from flask configuration
        img_dir = self._temp_img_dir
        # check if temp directory exists, if not attempt to create directory
        if not os.path.exists(img_dir):
            try:
                os.mkdir(img_dir)
                self.logger.info('Creating temporary image directory {}'.
                                 format(img_dir))
            except OSError as err:
                self.logger.error(('Failure creating temporary image directory'
                                   ' {}.\nError message {}').format(img_dir,
                                                                    err))
                raise
        img = Image.open(img_data)
        exts = ('.jpg', '.thumbnail')
        sizes = [(568, 852), (144, 214)]
        # create filepaths to temp images in temp directory
        img_filepaths = [os.path.join(img_dir, ''.join(
            [str(cover_loc.split('/')[-1]), ext])) for ext in exts]
        # index 0 = size tuple
        # index 1 = path to file
        size_and_fps = zip(sizes, img_filepaths)
        for img_file in size_and_fps:
            # preserve original file for multiple manipulations
            temp_img = img.copy()
            size = img_file[0]
            filepath = img_file[1]
            if not os.path.exists(filepath):
                # create plex cover art file if file does not exist
                try:
                    temp_img = ImageOps.fit(image=temp_img, size=size,
                                            method=Image.ANTIALIAS)
                    temp_img.save(filepath, "JPEG")
                    self.logger.info(
                        'Write image file: {}'.format(filepath))
                except IOError as pil_err:
                    self.logger.error(
                        'Image file write failure at {}.  Reason: {}'.
                        format(filepath, pil_err))
            else:
                self.logger.debug('Image file already exists at: {}'.
                                  format(filepath))
        return img_filepaths[0]

    def _get_tv_show_data(self, video, get_type=None):
        video_data = dict(showtitle=
                          video.get('@parentTitle',
                                    video.get('@grandparentTitle')),
                          episode_number=int(video.get('@leafCount',
                                                       video.get('@index'))),
                          summary=video.get('@parentSummary',
                                            video.get('@summary')),
                          season=video['@title'])
        if get_type != 'nowplaying':
            json_show_data = self._get_xml_convert_to_json('serverinfo',
                                                           video['@key'].
                                                           lstrip('/'))
            vid = json_show_data['MediaContainer']
            video_data.update(rating=vid.get('@grandparentContentRating', ''),
                              studio=vid['@grandparentStudio'])
            try:
                # if there's more than one episode in the season
                vid_we_want = vid['Video'][
                    int(video_data['episode_number']) - 1]
            except KeyError:
                # first show in season
                vid_we_want = vid['Video']
            # get originally date playing on TV
            aired_date = vid_we_want['@originallyAvailableAt']
            video_data.update(title=vid_we_want['@title'],
                              aired_date=self.convert_date(aired_date,
                                                           "%Y-%m-%d",
                                                           "%m/%d/%Y"))

            # Set individual show summary to parent summary if show summary does
            # not exist
            if vid_we_want['@summary'] != '':
                video_data['summary'] = vid_we_want['@summary']
        return video_data