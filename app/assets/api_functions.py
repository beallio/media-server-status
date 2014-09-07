from collections import OrderedDict

from app.assets import services, weather
from app.assets.services import CheckCrashPlan, SubSonic, ServerSync, Plex
from app.assets.system_info import GetSystemInfo, get_network_speed, get_ping, get_wan_ip, get_partitions_space, \
    get_total_system_space
from app import test_data as config


def system_info():
    get_system_info = GetSystemInfo()
    return get_system_info.get_info()


def network_speed():
    return get_network_speed()


def ping():
    return dict(ping='{:.0f}'.format(get_ping()))


def storage():
    paths = get_partitions_space(config.PARTITIONS)
    return dict(total=get_total_system_space(),
                paths=paths)


def ip_address():
    return dict(wan_ip=get_wan_ip(), internal_ip=config.INTERNAL_IP)


def services_status():
    servers = [Plex(config.PLEX_INFO), SubSonic(config.SUBSONIC_INFO), ServerSync(config.SERVERSYNC_INFO),
               CheckCrashPlan(config.CRASHPLAN_INFO)]
    servers_mapped = [getattr(s, 'getStatusMapping') for s in servers]
    servers_dict = OrderedDict()
    for s in servers_mapped:
        servers_dict = OrderedDict(servers_dict.items() + s.items())
    return servers_dict


def media_results():
    plex_server_creds = config.PLEX_INFO
    s = services.SubSonic(config.SUBSONIC_INFO)
    return s.getNowPlayingOrRecentlyAdded()


def weather_data():
    w = weather.ForecastData(config.WEATHER)
    return w.getForecastData()