import os

import libsonic


class Service(object):
    def __init__(self, service_info):
        assert type(service_info) is dict
        self.server_info = service_info
        self.SERVICES_STATUS_MAPPING = self._get_status_mappings_dict()
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
            output = {service_name: self.SERVICES_STATUS_MAPPING[str(self.connect_status)]}
            output[service_name]['title'] = self._add_service_name_to_status_mapping()
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
        delim = '/'
        path = os.path.split(os.path.realpath(__file__))[0]
        basepath_to_remove = ''.join(path.split(delim)[-2]) + delim
        return filepath.replace(basepath_to_remove, '')

    def _test_file_path(self, file_path_key):
        output = None
        try:
            file_path = self.server_info[file_path_key]
            if os.path.exists(file_path):
                output = file_path
        except KeyError:
            print "key doesn't exist"
            pass
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


class SubSonic(Service):
    def __init__(self, server_info):
        Service.__init__(self, server_info)
        self.service_name = 'subsonic'
        self.image_dir = 'app/static/img/tmp/'
        self.conn = libsonic.Connection(baseUrl=self.server_info['url'],
                                        username=self.server_info['user'],
                                        password=self.server_info['password'],
                                        port=self.server_info['port'],
                                        appName=self.server_info['appname'],
                                        apiVersion=self.server_info['api'],
                                        serverPath=self.server_info['serverpath'])
        self.connect_status = self._test_server_connection()
        self.server_full_url = self._get_server_full_url()
        self.resolved_status_mapping = self._get_status_mapping()

    def getNowPlayingOrRecentlyAdded(self, number_of_results=10):
        entries = {}
        now_playing_count = 0
        if not self.connect_status:
            return
        try:
            entries['now_playing'] = self._get_now_playing()
            now_playing_count = len(entries['now_playing'])
            if now_playing_count > number_of_results:
                entries['now_playing'] = entries['now_playing'][:number_of_results]
        except TypeError:
            pass
        finally:
            if now_playing_count < number_of_results:
                entries['recently_added'] = self._get_recently_added(num_results=number_of_results)
                recently_added_count = len(entries['recently_added'])
                show_recently_added = recently_added_count - now_playing_count
                entries['recently_added'] = entries['recently_added'][: show_recently_added]
        return entries

    def set_output_directory(self, directory):
        self.image_dir = directory
        return self.image_dir == directory

    def _test_server_connection(self):
        connection_status = False
        try:
            connection_status = self.conn.ping()
            assert connection_status
        except AssertionError:
            print "Unable to reach Subsonic server"
        finally:
            return connection_status

    def _create_cover_art_file(self, coverArtID, size=600):
        """
        size in getCoverArt method for subsonic returns a square image with dimensions in pixels equal to size
        :param coverArtID:
        :return:
        """
        img_data = self.conn.getCoverArt(aid=coverArtID, size=size)
        cover_dir = os.path.join(self.image_dir, 'covers')
        if not os.path.isdir(cover_dir):
            os.makedirs(cover_dir)
        filename = 'cover'
        ext = '.jpg'
        short_filepath = filename + str(coverArtID) + '_' + str(size) + ext
        full_filepath = os.path.join(cover_dir, short_filepath)
        if not os.path.isfile(full_filepath):
            print "write new cover art"
            with open(full_filepath, 'wb') as f:
                f.write(img_data.read())
        return self._strip_base_path(full_filepath)

    def _get_entry_info(self, entry):
        """
        appends URL coverart link to Subsonic entry dict
        :param entry: subsonic entry dict
        :return: entry
        """
        assert type(entry) == dict
        entry['coverartURL'] = '{url}?u={user}&p={pw}&v={ver}&c={app}&id={covertArtID}'.format(
            url='{url}getCoverArt.view'.format(url=self.server_full_url),
            user=self.server_info['user'],
            pw=self.server_info['password'],
            ver=self.server_info['api'],
            app=self.server_info['appname'],
            covertArtID=entry['coverArt'])
        entry['coverArtLocalLink'] = self._create_cover_art_file(entry['coverArt'])
        try:
            """ Return progress on currently playing song(s).  No good way to do this since Subsonic
            doesn't have access to this info through it's API.  Calculate progress by taking last time song was accessed
            and divide by progress
            """
            entry['progress'] = min(float(entry['minutesAgo']) / float(entry['duration'] / 60), 1)
        except KeyError:
            entry['progress'] = 1
        finally:
            entry['progress_pct'] = '{:.2%}'.format(entry['progress'])
            entry['progress_whole'] = entry['progress'] * 100
        return entry

    def _get_now_playing(self):
        entries = []
        nowplaying = self.conn.getNowPlaying()
        if type(nowplaying['nowPlaying']['entry']) == list:  # multiple songs playing
            entries = [self._get_entry_info(entry) for entry in nowplaying['nowPlaying']['entry']]
        elif type(nowplaying['nowPlaying']['entry']) == dict:  # single song playing
            entries.append(self._get_entry_info(nowplaying['nowPlaying']['entry']))
        # remove entries from now playing if user hasn't touched them or playlist auto advanced in X min
        entries = [entry for entry in entries if entry['minutesAgo'] <= 10]
        return entries

    def _get_recently_added(self, num_results=10):
        recently_added = self.conn.getAlbumList("newest", num_results)
        recently_added = recently_added['albumList']['album']
        return [self._get_entry_info(entry) for entry in recently_added]

    def _get_server_full_url(self):
        return '{url}:{port:d}{path}'.format(url=self.server_info['url'], port=self.server_info['port'],
                                             path=self.server_info['serverpath'])


class CheckCrashPlan(Service):
    def __init__(self, server_info):
        Service.__init__(self, server_info)
        self.service_name = 'backups'
        self.file_path = self._test_file_path('logfile_path')
        self.connect_status = self._test_server_connection()
        self.resolved_status_mapping = self._get_status_mapping()

    def _test_server_connection(self):
        items_to_keep = ['scanning', 'backupenabled']
        with open(self.file_path, 'r') as f:
            items = [line.lower().split() for line in f.readlines() for x in items_to_keep if x in line.lower()]
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
            return os.path.exists(self.lockfile_path)
        except TypeError:
            return False


class Plex(Service):
    def __init__(self, server_info):
        Service.__init__(self, server_info)
        assert type(server_info) is dict
        self.server_info = server_info
        self.service_name = 'plex'
        self.connect_status = self._test_server_connection()
        self.resolved_status_mapping = self._get_status_mapping()

    def _test_server_connection(self):
        return True