# coding=utf-8
from collections import namedtuple
from time import localtime, strftime

import forecastio


class ForecastData(object):
    def __init__(self, weather_config):
        assert type(weather_config) is dict
        self.forcastio_link_url = 'http://forecast.io/#/f/'
        self.api_key = weather_config['Forecast_io_API_key']
        self.lat = weather_config['Latitude']
        self.lng = weather_config['Longitude']
        self.units = weather_config['units']
        self.forecast = self._get_forecast_io()

    def getForecastData(self):
        json = self.forecast.json
        current = json['currently']
        hourly = json['hourly']
        minutely = json['minutely']
        daily = json['daily']['data'][0]
        output = dict(current_summary=current['summary'],
                      current_summary_icon=self._get_weather_icons(current['icon']),
                      current_temp=u'{:0.0f}°'.format(round(current['temperature'], 0)),
                      feels_like_temp=u'{:0.0f}°'.format(round(current['apparentTemperature'], 0)),
                      current_windspeed='{:0.0f}'.format(round(current['windSpeed'], 0)),
                      minutely_summary=minutely['summary'],
                      hourly_summary=hourly['summary'],
                      sunset=self._convert_time_to_text(daily['sunsetTime']),
                      sunrise=self._convert_time_to_text(daily['sunriseTime']),
                      url_link='{url}{lat},{lng}'.format(url=self.forcastio_link_url, lat=self.lat, lng=self.lng))
        if output['current_windspeed'] != 0:
            output['current_windbearing'] = self._get_wind_bearing_text(current['windBearing'])
        return output

    def reloadData(self):
        self.forecast.update()

    def _get_forecast_io(self):
        return forecastio.load_forecast(self.api_key, self.lat, self.lng, units=self.units)

    @staticmethod
    def _get_weather_icons(weather_icon):
        assert type(weather_icon) is unicode
        weather_icon = weather_icon.replace("-", "_")
        weather_mappings = dict(clear_day='B',
                                clear_night='C',
                                rain='R',
                                snow='W',
                                sleet='X',
                                wind='F',
                                fog='L',
                                cloudy='N',
                                partly_cloudy_day='H',
                                partly_cloudy_night='I')
        assert weather_icon in weather_mappings
        return weather_mappings[weather_icon]

    @staticmethod
    def _get_wind_bearing_text(degrees):
        # normalize windbearing so N starts at 0 degrees
        deg_norm = (float(degrees) + 11.25) / 22.5
        # convert range of windbearing degrees to lookup patterns
        deg_norm_lookup = int(deg_norm) + int((deg_norm // 1) > 0)
        direction_mappings = {1: ('North', 'N'),
                              2: ('North-northeast', 'NNE'),
                              3: ('Northeast', 'NE'),
                              4: ('East-northeast', 'ENE'),
                              5: ('East', 'E'),
                              6: ('East-southeast', 'ESE'),
                              7: ('Southeast', 'SE'),
                              8: ('South-southeast', 'SSE'),
                              9: ('South', 'S'),
                              10: ('South-southwest', 'SSW'),
                              11: ('Southwest', 'SW'),
                              12: ('West-southwest', 'WSW'),
                              13: ('West', 'W'),
                              14: ('West-northwest', 'WNW'),
                              15: ('Northwest', 'NW'),
                              16: ('North-northwest', 'NNW')}
        try:
            bearing_text = direction_mappings[int(deg_norm_lookup)]
        except KeyError:
            bearing_text = direction_mappings[1]
        # output namedtuple for Cardinal direction, and abbrevation text
        return namedtuple(typename='bearing_text', field_names=['cardinal', 'abbrev'])._make(bearing_text)

    @staticmethod
    def _convert_time_to_text(t):
        assert type(t) is int
        t = strftime('%I:%M %p', localtime(t))
        if t.startswith('0'):
            t = t[1:]
        return t
