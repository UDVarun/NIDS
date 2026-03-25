"""
backend/utils/geoip.py
=======================
IP geolocation using the MaxMind GeoLite2-City database.
Provides offline, no-API-key IP → country/city/lat/lon lookup.
"""

import os
import ipaddress
from utils.logger import get_logger

logger = get_logger('geoip')

_DB_PATH  = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                          'GeoLite2-City.mmdb')
_reader   = None
GEOIP_OK  = False

try:
    import geoip2.database
    if os.path.exists(_DB_PATH):
        _reader  = geoip2.database.Reader(_DB_PATH)
        GEOIP_OK = True
        logger.info(f"GeoIP database loaded: {_DB_PATH}")
    else:
        logger.warning(f"GeoIP database not found at {_DB_PATH}")
        logger.warning("Geolocation remains inactive until GeoLite2-City.mmdb is provided.")
except ImportError:
    logger.warning("geoip2 not installed. Run: pip install geoip2")


_PRIVATE_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('::1/128'),
]


def _is_private(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in _PRIVATE_RANGES)
    except ValueError:
        return True


def lookup(ip_str: str) -> dict | None:
    if _is_private(ip_str):
        return {
            'ip':      ip_str,
            'country': 'Local Network',
            'city':    'Private IP',
            'lat':     None,
            'lon':     None,
            'private': True
        }

    if not GEOIP_OK or _reader is None:
        return None

    try:
        record = _reader.city(ip_str)
        return {
            'ip':      ip_str,
            'country': record.country.name or 'Unknown',
            'city':    record.city.name or '',
            'lat':     record.location.latitude,
            'lon':     record.location.longitude,
            'private': False
        }
    except Exception:
        return None
