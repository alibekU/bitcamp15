from json import loads
from re import compile, VERBOSE
from urllib import urlopen

FREE_GEOIP_URL = "http://freegeoip.net/json/{}"

def get_geodata(ip):
    """
    Search for geolocation information using http://freegeoip.net/
    """
    url = FREE_GEOIP_URL.format(ip)
    data = {}

    try:
        response = urlopen(url).read()
        data = loads(response)
    except Exception:
        pass

    return data
