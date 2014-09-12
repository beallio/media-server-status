from collections import OrderedDict

from serverstatus import app
import weather as Weather
from services import CheckCrashPlan, SubSonic, ServerSync, Plex
from sysinfo import GetSystemInfo, get_network_speed, get_ping, get_wan_ip, get_partitions_space, get_total_system_space
import wrappers

config = app.config


@wrappers.logger('debug')
def system_info():
    get_system_info = GetSystemInfo()
    output = get_system_info.get_info()
    return output


@wrappers.logger('debug')
def network_speed():
    return get_network_speed(sleep=5)


@wrappers.logger('debug')
def ping():
    return dict(ping='{:.0f}'.format(get_ping()))


@wrappers.logger('debug')
def storage():
    paths = get_partitions_space(config['PARTITIONS'])
    return dict(total=get_total_system_space(), paths=paths)


@wrappers.logger('debug')
def ip_address():
    return dict(wan_ip=get_wan_ip(), internal_ip=config['INTERNAL_IP'])


@wrappers.logger('debug')
def services():
    servers = [Plex(config['PLEX_INFO']), SubSonic(config['SUBSONIC_INFO']),
               ServerSync(config['SERVERSYNC_INFO']),
               CheckCrashPlan(config['CRASHPLAN_INFO'])]
    servers_mapped = [getattr(s, 'getStatusMapping') for s in servers]
    servers_dict = OrderedDict()
    for s in servers_mapped:
        servers_dict = OrderedDict(servers_dict.items() + s.items())
    return servers_dict


@wrappers.logger('debug')
def media():
    plex_server_creds = config['PLEX_INFO']
    s = SubSonic(config['SUBSONIC_INFO'])
    return s.getNowPlayingOrRecentlyAdded()


@wrappers.logger('debug')
def weather():
    w = Weather.ForecastData(config['WEATHER'])
    return w.getForecastData()