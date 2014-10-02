from unittest import TestCase
import unittest
from collections import OrderedDict
from copy import deepcopy

from serverstatus import app
from serverstatus.assets.apifunctions import APIFunctions
from serverstatus.assets.services import ServerSync, SubSonic
from serverstatus.assets.weather import Forecast


class TestApiFunctions(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.apifunctions = APIFunctions(app.config)

    def test_ping(self):
        self.assertTrue(isinstance(self.apifunctions.ping(), dict))

    def test_system_info(self):
        self.assertTrue(isinstance(self.apifunctions.system_info(), dict))

    def test_storage(self):
        self.assertTrue(isinstance(self.apifunctions.storage(), dict))

    def test_network_speed(self):
        self.assertTrue(isinstance(self.apifunctions.network_speed(), dict))

    def test_services(self):
        self.assertTrue(isinstance(self.apifunctions.services(), OrderedDict))

    def test_weather(self):
        self.assertTrue(isinstance(self.apifunctions.forecast(), dict))

    def test_media(self):
        results = self.apifunctions.media()
        self.assertIsInstance(results, dict)
        for key in results:
            if 'plex_nowplaying' in key:
                self.plex_nowplaying(results[key])
            if 'plex_recentlyadded' in key:
                self.plex_recentlyadded(results[key])
            if 'subsonic_nowplaying' in key:
                self.subsonic_nowplaying(results[key])

    def test_plex_transcodes(self):
        self.assertTrue(isinstance(self.apifunctions.plex_transcodes(), dict))

    def plex_recentlyadded(self, result):
        self.assertIsInstance(result, dict)
        for vid_type in result:
            self.assertIsInstance(result[vid_type], list)
            for video in result[vid_type]:
                self.assertIsInstance(video, dict)

    def subsonic_recentlyadded(self, result):
        self.assertIsInstance(result, list)
        for album in result:
            self.assertIsInstance(result[album], dict)

    def plex_nowplaying(self, result):
        if not result:
            self.assertIs(result, None)
        if result:
            for key in result:
                self.assertIsInstance(result[key], dict)

    def subsonic_nowplaying(self, result):
        if not result:
            self.assertIs(result, None)
        if result:
            for key in result:
                self.assertIsInstance(result[key], dict)


class TestSubSonicServer(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.config = app.config['SUBSONIC_INFO']
        self.config_test_values = dict(
            url='http://192.168.1.100',
            port=40,
            user='guestuser',
            password='password',
            serverpath='/subbybad/'
        )

    def est_bad_config_values(self):
        for key in self.config_test_values:
            config = deepcopy(self.config)
            config[key] = self.config_test_values[key]
            self.subsonic = SubSonic(config)
            print key, self.config_test_values[key]
            self.assertTrue(self.subsonic.connection_status)

    def test_bad_server_url(self):
        bad_url = 'http://192.168.1.100'
        config = deepcopy(self.config)
        config['url'] = bad_url
        self.subsonic = SubSonic(config)
        self.assertFalse(self.subsonic.connection_status)

    def test_bad_port(self):
        config = deepcopy(self.config)
        config['port'] = 40
        self.subsonic = SubSonic(config)
        self.assertFalse(self.subsonic.connection_status)

    def test_bad_username(self):
        config = deepcopy(self.config)
        config['user'] = 'guestuser'
        self.subsonic = SubSonic(config)
        self.assertFalse(self.subsonic.connection_status)

    def test_bad_password(self):
        config = deepcopy(self.config)
        config['password'] = 'password'
        self.subsonic = SubSonic(config)
        self.assertFalse(self.subsonic.connection_status)

    def test_bad_serverpath(self):
        config = deepcopy(self.config)
        config['serverpath'] = '/subbybad/'
        self.subsonic = SubSonic(config)
        self.assertFalse(self.subsonic.connection_status)


class TestForecastIO(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.config = app.config['WEATHER']

    def test_bad_apikey(self):
        config = deepcopy(self.config)
        config['Forecast_io_API_key'] = 'thisisabadkey'
        with self.assertRaises(ValueError):
            Forecast(config)


class TestServerSync(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.config = app.config['SERVERSYNC_INFO']

    def test_no_lockfile_path(self):
        config = deepcopy(self.config)
        del config['lockfile_path']
        serversync = ServerSync(config)
        self.assertFalse(serversync.connection_status)

    def test_bad_lockfile_path(self):
        config = deepcopy(self.config)
        config['lockfile_path'] = '/tmp/badfile.lock'
        serversync = ServerSync(config)
        self.assertFalse(serversync.connection_status)


if __name__ == '__main__':
    unittest.main()