import os
import logging
import urllib2
import urlparse
from collections import OrderedDict, namedtuple
from operator import itemgetter
from time import localtime, strftime

from PIL import Image

import libsonic
import xmltodict

from serverstatus import app
import serverstatus.assets.exceptions as exceptions


logger = logging.getLogger(__name__)


class Service(object):
    def __init__(self, service_info):
        assert type(service_info) is dict
        self.logger = logger
        self.logger.debug(
            '{} class initialized'.format(self.__class__.__name__))
        self.server_info = service_info
        self.SERVICES_STATUS_MAPPING = self._get_status_mappings_dict()
        self.image_dir = 'serverstatus/static/img/tmp/'
        self.service_name = None
        self.connect_status = None
        self.server_full_url = None
        self.resolved_status_mapping = dict()

    @property
    def getStatusMapping(self):
        return self.resolved_status_mapping

    @property
    def getConnectionStatus(self):
        return self.connect_status

    @property
    def getServerFullURL(self):
        return self.server_full_url

    @property
    def getExternalURL(self):
        return self._get_config_attrib('external_url')

    def _test_server_connection(self):
        # method to be overridden by subclasses
        return

    def _get_status_mapping(self):
        service_name = self.service_name
        output = {service_name: dict()}
        try:
            output = {service_name: self.SERVICES_STATUS_MAPPING[
                str(self.connect_status)]}
            output[service_name][
                'title'] = self._add_service_name_to_status_mapping()
            if self.getExternalURL:
                output[service_name]['external_url'] = self.getExternalURL
        except KeyError:
            pass
        return output

    def _add_service_name_to_status_mapping(self):
        delim = '-'
        service_name = self.service_name
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
    def _strip_base_path(filepath):
        return filepath.replace(app.config['APP_MODULESLOCATION'], '').lstrip(
            '/')

    def _test_file_path(self, file_path_key):
        output = None
        try:
            file_path = self.server_info[file_path_key]
            if os.path.exists(file_path):
                output = file_path
        except KeyError as e:
            self.logger.error(e)
        finally:
            return output

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
        # Log warning that config value for plex is missing from config file.  Using default value instead
        self.logger.warning(
            '{config_val} missing from config value for {cls_name}.  Using {default} instead'.
            format(cls_name=cls_name, default=default, config_val=config_val))

    @staticmethod
    def _convert_xml_to_json(resp_output):
        return xmltodict.parse(resp_output)

    def _get_img_directory(self, subpath=None):
        """
        Creates absolutely directory path for temp images

        :param subpath:
        :return: string
        """
        if subpath is None:
            subpath = ''
        dir_short = os.path.join(self.image_dir, subpath)
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

    @staticmethod
    def _build_external_img_path(service_name):
        basepath = 'img/'
        return ''.join([basepath, service_name, '?'])


class SubSonic(Service):
    def __init__(self, server_info):
        Service.__init__(self, server_info)
        self.service_name = 'subsonic'
        self.conn = libsonic.Connection(baseUrl=self.server_info['url'],
                                        username=self.server_info['user'],
                                        password=self.server_info['password'],
                                        port=self.server_info['port'],
                                        appName=self.server_info['appname'],
                                        apiVersion=self.server_info['api'],
                                        serverPath=self.server_info[
                                            'serverpath'])
        self.connect_status = self._test_server_connection()
        self.server_full_url = self._get_server_full_url()
        self.resolved_status_mapping = self._get_status_mapping()
        self._img_base_url = self._build_external_img_path(
            self.service_name) + 'cover='

    def getNowPlayingOrRecentlyAdded(self, num_of_results=None):
        if num_of_results is None:
            num_of_results = 9
        entries = {}
        now_playing_count = 0
        if not self.connect_status:
            return
        try:
            entries['now_playing'] = self._get_now_playing()
            now_playing_count = len(entries['now_playing'])
            if now_playing_count > num_of_results:
                entries['now_playing'] = entries['now_playing'][:num_of_results]
        except TypeError:
            pass
        finally:
            if now_playing_count < num_of_results:
                entries['recently_added'] = self.get_recently_added(
                    num_results=num_of_results)
                recently_added_count = len(entries['recently_added'])
                show_recently_added = recently_added_count - now_playing_count
                entries['recently_added'] = entries['recently_added'][
                                            :show_recently_added]
        return entries

    def get_recently_added(self, num_results=None):
        if num_results is None:
            num_results = 9
        recently_added = self.conn.getAlbumList("newest", num_results)
        recently_added = recently_added['albumList']['album']
        return [self._get_entry_info(entry) for entry in recently_added]

    def get_cover_art(self, cover_art_id, size=None):
        assert type(cover_art_id) is int
        if any([size is None, size <= 0, type(size) is not int]):
            return self.conn.getCoverArt(aid=cover_art_id)
        else:
            if size > 2000:
                # set max limit on size of photo returned
                size = 2000
            return self.conn.getCoverArt(aid=cover_art_id, size=size)

    def set_output_directory(self, directory):
        self.image_dir = directory
        return self.image_dir == directory

    def _test_server_connection(self):
        connection_status = False
        try:
            connection_status = self.conn.ping()
            assert connection_status
        except AssertionError:
            self.logger.error("Unable to reach Subsonic server")
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
        cover_dir = '/tmp/flask-images'  # temp storage for created image files
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

    def _get_entry_info(self, entry):
        """
        appends URL coverart link to Subsonic entry dict
        :param entry: subsonic entry dict
        :return: entry
        """
        assert type(entry) == dict
        entry['coverArtExternalLink_sm'] = ''.join(
            [self._img_base_url, str(entry['coverArt']), '&size=145'])
        entry['coverArtExternalLink_xl'] = ''.join(
            [self._img_base_url, str(entry['coverArt']), '&size=500'])
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

    def _get_now_playing(self):
        entries = []
        nowplaying = self.conn.getNowPlaying()
        if type(nowplaying['nowPlaying'][
            'entry']) == list:  # multiple songs playing
            entries = [self._get_entry_info(entry) for entry in
                       nowplaying['nowPlaying']['entry']]
        elif type(nowplaying['nowPlaying'][
            'entry']) == dict:  # single song playing
            entries.append(
                self._get_entry_info(nowplaying['nowPlaying']['entry']))
        # remove entries from now playing if user hasn't touched them or
        # playlist auto advanced in X min
        entries = [entry for entry in entries if entry['minutesAgo'] <= 10]
        return entries

    def _get_server_full_url(self):
        serverpath, _ = self.server_info['serverpath'].strip('/').split('/')
        return '{url}:{port:d}/{path}'.format(url=self.server_info['url'],
                                              port=self.server_info['port'],
                                              path=serverpath)


class CheckCrashPlan(Service):
    def __init__(self, server_info):
        Service.__init__(self, server_info)
        self.service_name = 'backups'
        self.file_path = self._test_file_path('logfile_path')
        self.connect_status = self._test_server_connection()
        self.resolved_status_mapping = self._get_status_mapping()

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
        self.lockfile_path = self._test_file_path('lockfile_path')
        self.service_name = 'server-sync'
        self.connect_status = self._test_server_connection()
        self.resolved_status_mapping = self._get_status_mapping()

    def _test_server_connection(self):
        try:
            lockfile_exists = os.path.exists(self.lockfile_path)
            self.logger.debug(
                'Server Sync Lockfile exists {}'.format(lockfile_exists))
            return lockfile_exists
        except TypeError:
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
        self.service_name = 'plex'
        self.server_internal_url_and_port = self._get_full_url_and_port
        try:
            self.server_full_url = server_info['external_url']
        except KeyError as err:
            self.logger.error(
                'Missing config value {config_value} from {cls}'.format(
                    config_value='external_url',
                    cls=self.__class__.__name__))
            raise exceptions.MissingConfigValue(err)
        self.connect_status = self._test_server_connection()
        self.resolved_status_mapping = self._get_status_mapping()
        self.transcodes = 0
        self._cover_mapping = dict()
        self._img_base_url = self._build_external_img_path(self.service_name)

    def get_recently_added(self, num_results=None):
        if not self.connect_status:
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
        recently_added = [media for value in json_data['MediaContainer'] if
                          type(json_data['MediaContainer'][value]) == list for
                          media in json_data['MediaContainer'][value] if
                          media['@type'] != 'season']
        # remove extra data
        del json_data
        # sort the recently added list by date in descending order
        recently_added = sorted(recently_added, key=itemgetter('@addedAt'),
                                reverse=True)
        # trim the list to the number of results we want
        recently_added_trimmed = recently_added[:num_results]
        del recently_added
        recently_added_trimmed = [self._get_video_data(video) for video in
                                  recently_added_trimmed]
        return recently_added_trimmed

    def get_now_playing(self):
        """
        Returns now playing data from Plex server in a JSON-like dictionary

        :return: dict()
        """

        def generate_video_data(vid_data):
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
                # Grab relevant data about Video from JSON data
                yield self._get_video_data(video)

        self.transcodes = 0  # reset transcode count
        api_call = 'nowplaying'
        now_playing_relevant_data = list()
        json_data = self._get_xml_convert_to_json(api_call)
        if not int(json_data['MediaContainer']['@size']):
            # Nothing is currently playing in plex
            return None
        for vid in generate_video_data(json_data['MediaContainer']['Video']):
            now_playing_relevant_data.append(vid)
        return now_playing_relevant_data

    def get_cover_image(self, request_args):
        """
        Returns binary jpeg object from plex

        :type cover_loc: unicode or str
        :return:
        """
        if self._cover_mapping is None:
            # if _cover_mapping is empty we need to initialize Now Playing
            self.get_now_playing()
        args = list(request_args)
        args = sorted(args)
        if 'local' in args:
            resp = open('/tmp/flask-images/' + args[0] + '.jpg', 'r')
        else:
            try:
                resp = urllib2.urlopen(
                    urlparse.urljoin(self.server_internal_url_and_port,
                                     self._cover_mapping[args[0]]))
            except TypeError, urllib2.HTTPError:
                # // TODO insert LOGGER warning and raise error
                raise
        return resp

    @property
    def get_transcodes(self):
        """
        Returns number of current number of Plex transcode sessions

        >>> 0
        >>> 1

        :return: int
        """
        # // TODO need to stream line this once Plex code is fully
        # // integrated and out of testing
        _ = self.get_now_playing()
        return self.transcodes

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
        resp = self._get_plex_api_data('transcode')
        is_connectable = resp is not None
        if not is_connectable:
            self.logger.error('Could not connect to Plex server')
        return is_connectable

    def _get_api_url_suffix(self, the_data_were_looking_for):
        """
        https://code.google.com/p/plex-api/wiki/PlexWebAPIOverview
        contains information required Plex HTTP APIs

        transcode: Transcode bitrateinfo, myPlexauthentication info
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
            transcode='/',
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
        Gets Plex data based on api key and converts Plex XML response to JSON format

        :type api_key: str
        :type api_suffix: unknown or str
        :return:
        """
        xml_data = self._get_plex_api_data(api_key, api_suffix)
        return self._convert_xml_to_json(xml_data)

    def _get_video_data(self, video, get_type=None):
        vidtype = video['@librarySectionTitle']
        if vidtype == 'TV Shows':
            plex_path_to_art = video['@parentThumb']
            video_data = dict(showtitle=video['@parentTitle'],
                              episode_number=video['@leafCount'],
                              arturl=self.server_internal_url_and_port +
                                     plex_path_to_art,
                              summary=video['@parentSummary'],
                              season=video['@title'])
        elif vidtype == 'Movies':
            plex_path_to_art = video['@thumb']
            video_data = dict(showtitle=video['@title'],
                              arturl=self._save_cover_art(
                                  self.server_internal_url_and_port +
                                  plex_path_to_art),
                              summary=video['@summary'],
                              releasedate=self._convert_release_date(
                                  video['@originallyAvailableAt']))
        else:
            # encountered an unexpected video type
            msg = 'Unexpected media type {} encountered'.format(vidtype)
            self.logger.error(msg)
            raise exceptions.PlexAPIDataError(msg)
        # add common elements to video dict
        arturlmapped_value = os.path.basename(plex_path_to_art)
        video_data.update(type=vidtype,
                          art_external_url=''.join([self._img_base_url,
                                                    arturlmapped_value]),
                          added_at=strftime('%m/%d/%Y %I:%M %p',
                                            localtime(int(video['@addedAt']))))
        # converts direct plex http link to thumbnail to internal mapping
        # security through obfuscation /s
        self._cover_mapping[arturlmapped_value] = plex_path_to_art
        try:
            video_data['rating'] = float(video['@rating'])
        except KeyError:
            # log no rating info, set rating to 0
            self.logger.info('Rating data for {} is not available'.
                             format(
                video_data['showtitle'] if vidtype == 'Movies' else ' - '.
                join([video_data['showtitle'], video_data['season'],
                      video_data['episode_number']])))
            video_data['rating'] = 0
        if get_type == 'nowplaying':
            # only applicable if we want to retrieve now playing data from Plex
            try:
                # this is only relevant for videos that are currently playing
                video_data['progress'] = (float(video['@viewOffset']) / float(
                    video['@duration'])) * 100.0
            except KeyError:
                # video's not playing - not an issue
                pass
            self._calc_transcode_sessions(video)
        return video_data

    def _calc_transcode_sessions(self, video_data):
        """
        Calculates number of transcode sessions in now playing
        :param video_data:
        :return: None
        """
        video_transcoding = video_data['TranscodeSession'][
                                '@videoDecision'] == 'transcode'
        audio_transcoding = video_data['TranscodeSession'][
                                '@audioDecision'] == 'transcode'
        if any([video_transcoding, audio_transcoding]):
            self.transcodes += 1

    @staticmethod
    def _convert_release_date(reldate):
        """
        Converts date in string format YYYY-MM-DD to namedtuple

        > _convert_release_date('2013-11-22')
        >>> ReleaseDate(year=2013, month=11, day=22)

        :type reldate: unicode
        :return: namedtuple
        """
        split_rel_date = reldate.split('-')
        split_date_to_int = [int(x) for x in split_rel_date]
        tuple_date = namedtuple(typename='ReleaseDate',
                                field_names=['year', 'month', 'day'])
        return tuple_date._make(split_date_to_int)

    def _save_cover_art(self, cover_loc):
        img_data = urllib2.urlopen(
            urlparse.urljoin(self.server_internal_url_and_port, cover_loc))
        img_dir = '/tmp/flask-images'
        try:
            os.mkdir(img_dir)
        except OSError as err:
            print err
        filename = 'thumbArt'
        exts = ['.jpg', '.thumbnail']
        short_filepaths = [''.join([filename, str(cover_loc.split('/')[-1]),
                                    '_', ext]) for ext in exts]
        large_art_fp, thumb_art_fp = [os.path.join(img_dir, fp) for fp in
                                      short_filepaths]
        if not os.path.exists(large_art_fp):
            try:
                with open(large_art_fp, 'wb') as img_file:
                    img_file.write(img_data.read())
                self.logger.info(
                    'Write cover art file: {}'.format(large_art_fp))
            except IOError:
                self.logger.error('Cover art file write failure: {}'.
                                  format(large_art_fp))
            else:
                if not os.path.exists(thumb_art_fp):
                    try:
                        size = 199, 134.328
                        im = Image.open(large_art_fp)
                        im.thumbnail(size, Image.ANTIALIAS)
                        im.save(thumb_art_fp, "JPEG")
                    except IOError:
                        self.logger.error('Cannot create thumbnail for : {}'.
                                          format(large_art_fp))
        img_data.close()
        return large_art_fp
