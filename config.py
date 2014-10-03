SUBSONIC_INFO = dict(
    url='http://192.168.0.1',
    serverpath='/rest',
    port=4040,
    user='user',
    password='password',
    api=1.8,
    appname='py-sonic',
    external_url='http://www.example.com/subsonic'
)

PLEX_INFO = dict(
    external_url='http://www.example.com/plex',
    internal_url='http://192.168.0.1',
    internal_port=32400,
    user='user',
    password='password',
    auth_token='AUTH_TOKEN',
    local_network_auth=False
)

SERVERSYNC_INFO = dict(
    lockfile_path='/tmp/server_sync.lockfile')

CRASHPLAN_INFO = dict(
    logfile_path='/usr/local/crashplan/log/app.log')

PARTITIONS = dict(Partition_Name_1='/mnt/partition1',
                  Partition_Name_2='/mnt/partition2',
                  Partition_Name_3='/mnt/partition3',
                  Root='/',
                  Home='/home')

INTERNAL_IP = 'http://192.168.0.1'
WEATHER = dict(
    Forecast_io_API_key='FORECASTIOKEY',
    Latitude=37.8030,
    Longitude=122.4360,
    units='us')
SERVER_URL = 'http://www.example.com'
DEBUG = False
SECRET_KEY = 'my secret'

