"""
Custom exceptions for managing different servers
"""

class MissingConfigFile(Exception):
    """
    Config file not found
    """
    pass


class MissingForecastIOKey(Exception):
    """
    No Forecast.IO API key found
    """
    pass


class PlexAPIKeyNotFound(Exception):
    """
    No Plex API key found
    """
    pass


class MissingConfigValue(Exception):
    """
    General exception catch all for missing config values
    """
    pass


class PlexConnectionError(Exception):
    """
    Error connecting to specified Plex server
    """
    pass


class PlexAPIDataError(Exception):
    """
    Plex returned malformed data, or data in a format unfamiliar with
    (perhaps an API change)
    """
    pass


class PlexImageError(Exception):
    """
    Error retrieving image cover from Plex server
    """
    pass


class SubsonicConnectionError(Exception):
    """
    Error connection to specified Subsonic server
    """
    pass