from app.info_services import subsonic_info
from app.info_services.check_crashplan import CheckCrashPlan
from app.info_services.system_info import GetSystemInfo, get_network_speed, get_ping, get_wan_ip
from app import test_data
from os import path
from collections import OrderedDict


def system_info():
    get_system_info = GetSystemInfo()
    return get_system_info.get_info()


def network_speed():
    return get_network_speed()


def ping():
    return dict(ping='{:.0f}'.format(get_ping()))


def storage():
    get_system_info = GetSystemInfo()
    paths = get_system_info.get_partitions_space(test_data.PARTITIONS)
    # place in ordered dictionary so paths always display in alphabetical order on page
    paths_ordered = OrderedDict(sorted(paths.items(), key=lambda x: x[0]))
    return dict(total=get_system_info.get_total_system_space(),
                paths=paths_ordered)


def ip_address():
    return dict(wan_ip=get_wan_ip(), internal_ip=test_data.INTERNAL_IP)


def server_status():
    subsonic_server_creds = test_data.SUBSONIC_INFO
    plex_server_creds = test_data.PLEX_INFO
    s = subsonic_info.SubSonic(subsonic_server_creds)
    return dict(subsonic_status=s.connect_status,
                server_sync_status=path.exists(test_data.SERVERSYNC_LOCKFILE_PATH),
                plex_status=True,
                backup_server_status=CheckCrashPlan(test_data.CRASHPLAN_LOGFILE_PATH).status())


def media_results():
    subsonic_server_creds = test_data.SUBSONIC_INFO
    plex_server_creds = test_data.PLEX_INFO
    s = subsonic_info.SubSonic(subsonic_server_creds)
    return s.retrieve_now_playing_or_recently_added()