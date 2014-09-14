from collections import OrderedDict

# from serverstatus import app
from weather import ForecastData
from services import CheckCrashPlan, ServerSync, Plex, SubSonic
from sysinfo import GetSystemInfo, get_network_speed, get_ping, get_wan_ip, get_partitions_space, get_total_system_space
import wrappers


class APIFunctions(object):
    def __init__(self, config):
        print 'APIFunction touched'
        self.config = config
        try:
            self.subsonic = SubSonic(self.config['SUBSONIC_INFO'])
        except KeyError:
            self.subsonic = None
        try:
            self.plex = Plex(self.config['PLEX_INFO'])
        except KeyError:
            self.plex = None
        try:
            self.server_sync = ServerSync(self.config['SERVERSYNC_INFO'])
        except KeyError:
            self.server_sync = None
        try:
            self.crashplan = CheckCrashPlan(self.config['CRASHPLAN_INFO'])
        except KeyError:
            self.crashplan = None
        try:
            self.weather = ForecastData(self.config['WEATHER'])
        except KeyError:
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
        self._test_configs()
        servers = [self.plex, self.subsonic, self.server_sync, self.crashplan]
        servers_mapped = [getattr(s, 'getStatusMapping') for s in servers]
        servers_dict = OrderedDict()
        for s in servers_mapped:
            servers_dict = OrderedDict(servers_dict.items() + s.items())
        return servers_dict

    @wrappers.logger('debug')
    def media(self):
        self._test_configs()
        subsonic = self.subsonic
        plex = self.plex
        return subsonic.getNowPlayingOrRecentlyAdded()

    @wrappers.logger('debug')
    def forecast(self):
        return self.weather.getForecastData()

    def _test_configs(self):
        service_variables = [(self.subsonic, SubSonic(self.config['SUBSONIC_INFO'])),
                             (self.plex, Plex(self.config['PLEX_INFO'])),
                             (self.server_sync, ServerSync(self.config['SERVERSYNC_INFO'])),
                             (self.crashplan, CheckCrashPlan(self.config['CRASHPLAN_INFO'])),
                             (self.weather, ForecastData(self.config['WEATHER']))]
        missing_vars = [var for var in service_variables if var[0] not in locals()]
