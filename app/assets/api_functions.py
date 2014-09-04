from app.assets import services
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


def server_status():
    subsonic = SubSonic(config.SUBSONIC_INFO)
    plex = Plex(config.PLEX_INFO)
    return dict(subsonic_status=subsonic.getConnectionStatus,
                server_sync_status=ServerSync(config.SERVERSYNC_LOCKFILE_PATH).getConnectionStatus,
                plex_status=plex.getConnectionStatus,
                backup_server_status=CheckCrashPlan(config.CRASHPLAN_LOGFILE_PATH).getConnectionStatus)


def media_results():
    plex_server_creds = config.PLEX_INFO
    s = services.SubSonic(config.SUBSONIC_INFO)
    return s.retrieve_now_playing_or_recently_added()