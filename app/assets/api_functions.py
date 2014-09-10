from collections import OrderedDict

from app.assets import services as Services, weather as Weather
from app.assets.services import CheckCrashPlan, SubSonic, ServerSync, Plex
from app.assets.system_info import GetSystemInfo, get_network_speed, get_ping, get_wan_ip, get_partitions_space, \
    get_total_system_space
from app import app
import test_data as config


def system_info():
    get_system_info = GetSystemInfo()
    output = get_system_info.get_info()
    return _log_debug(output)


def network_speed():
    output = get_network_speed()
    return _log_debug(output)


def ping():
    output = dict(ping='{:.0f}'.format(get_ping()))
    return _log_debug(output)


def storage():
    paths = get_partitions_space(config.PARTITIONS)
    output = dict(total=get_total_system_space(),
                  paths=paths)
    return _log_debug(output)


def ip_address():
    output = dict(wan_ip=get_wan_ip(), internal_ip=config.INTERNAL_IP)
    return _log_debug(output)


def services():
    servers = [Plex(config.PLEX_INFO), SubSonic(config.SUBSONIC_INFO), ServerSync(config.SERVERSYNC_INFO),
               CheckCrashPlan(config.CRASHPLAN_INFO)]
    servers_mapped = [getattr(s, 'getStatusMapping') for s in servers]
    servers_dict = OrderedDict()
    for s in servers_mapped:
        servers_dict = OrderedDict(servers_dict.items() + s.items())
    output = servers_dict
    return _log_debug(output)


def media():
    plex_server_creds = config.PLEX_INFO
    s = Services.SubSonic(config.SUBSONIC_INFO)
    output = s.getNowPlayingOrRecentlyAdded()
    return _log_debug(output)


def weather():
    w = Weather.ForecastData(config.WEATHER)
    output = w.getForecastData()
    return _log_debug(output)


def _log_debug(output):
    if app.config['TESTING']:
        app.logger.debug(output)
    return output