from collections import OrderedDict
import logging

from serverstatus.assets.weather import Forecast
from serverstatus.assets.services import CheckCrashPlan, ServerSync, Plex, \
    SubSonic
from serverstatus.assets.sysinfo import GetSystemInfo, get_network_speed, \
    get_ping, get_wan_ip, get_partitions_space, get_total_system_space
import serverstatus.assets.wrappers as wrappers


class APIFunctions(object):
    def __init__(self, config):
        self.logger = LOGGER
        LOGGER.debug('{} initialized'.format(__name__))
        self.config = config
        self.subsonic = None
        self.plex = None
        self.server_sync = None
        self.crashplan = None
        self.weather = None

    @staticmethod
    @wrappers.logger('debug')
    def system_info():
        get_system_info = GetSystemInfo()
        output = get_system_info.get_info()
        return output

    @staticmethod
    @wrappers.logger('debug')
    def network_speed():
        return get_network_speed(sleep=5)

    @staticmethod
    @wrappers.logger('debug')
    def ping():
        return dict(ping='{:.0f}'.format(get_ping()))

    @wrappers.logger('debug')
    def storage(self):
        paths = get_partitions_space(self.config['PARTITIONS'])
        return dict(total=get_total_system_space(), paths=paths)

    @wrappers.logger('debug')
    def ip_address(self):
        return dict(wan_ip=get_wan_ip(), internal_ip=self.config['INTERNAL_IP'])

    @wrappers.logger('debug')
    def services(self):
        self._load_configs()
        servers = [self.plex, self.subsonic, self.server_sync, self.crashplan]
        for server in servers:
            status = server.get_connection_status
            self.logger.debug('{} connection updated to: {}'.
                              format(server.service_name,
                                     status))
        servers_mapped = [getattr(server, 'get_status_mapping') for server in
                          servers]
        servers_dict = OrderedDict()
        for server in servers_mapped:
            servers_dict = OrderedDict(servers_dict.items() + server.items())
        return servers_dict

    @wrappers.logger('debug')
    def media(self):
        self._load_configs()
        subsonic = self.subsonic
        plex = self.plex
        return dict(
            subsonic_nowplaying=subsonic.now_playing(),
            plex_nowplaying=plex.now_playing(),
            subsonic_recentlyadded=subsonic.recently_added(num_results=6),
            plex_recentlyadded=plex.recently_added(num_results=6))

    @wrappers.logger('debug')
    def forecast(self):
        self._load_configs()
        return self.weather.get_data()

    @wrappers.logger('debug')
    def plex_transcodes(self):
        self._load_configs()
        return dict(plex_transcodes=self.plex.transcodes)

    def _get_plex_cover_art(self, args):
        self._load_configs()
        return self.plex.get_cover_image(**args)

    def _get_subsonic_cover_art(self, cover_id, size):
        self._load_configs()
        cover_id = int(cover_id)
        return self.subsonic.get_cover_art(cover_id, size)

    def _load_configs(self):
        if self.subsonic is None:
            try:
                self.subsonic = SubSonic(self.config['SUBSONIC_INFO'])
            except KeyError:
                LOGGER.debug('Subsonic not loaded yet')
        if self.plex is None:
            try:
                self.plex = Plex(self.config['PLEX_INFO'])
            except KeyError:
                LOGGER.debug('Plex not loaded yet')
        if self.server_sync is None:
            try:
                self.server_sync = ServerSync(self.config['SERVERSYNC_INFO'])
            except KeyError:
                LOGGER.debug('Server Sync not loaded yet')
        if self.crashplan is None:
            try:
                self.crashplan = CheckCrashPlan(self.config['CRASHPLAN_INFO'])
            except KeyError:
                LOGGER.debug('CrashPlan not loaded yet')
        if self.weather is None:
            try:
                self.weather = Forecast(self.config['WEATHER'])
            except KeyError:
                LOGGER.debug('weather not loaded yet')


LOGGER = logging.getLogger(__name__)
