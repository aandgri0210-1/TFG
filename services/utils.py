import json
from functools import lru_cache
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import urlopen


WEATHER_CODES = {
    0: 'Despejado',
    1: 'Mayormente despejado',
    2: 'Parcialmente nublado',
    3: 'Nublado',
    45: 'Niebla',
    48: 'Niebla helada',
    51: 'Llovizna ligera',
    61: 'Lluvia ligera',
    63: 'Lluvia moderada',
    65: 'Lluvia intensa',
    71: 'Nieve ligera',
    73: 'Nieve moderada',
    75: 'Nieve intensa',
    80: 'Chubascos ligeros',
    81: 'Chubascos moderados',
    82: 'Chubascos intensos',
    95: 'Tormenta',
}


@lru_cache(maxsize=64)
def get_weather_for_city(city):
    if not city:
        return None

    try:
        geocoding_url = (
            'https://geocoding-api.open-meteo.com/v1/search?name='
            f'{quote_plus(city)}&count=1&language=es&format=json'
        )
        with urlopen(geocoding_url, timeout=5) as response:
            geocoding_payload = json.loads(response.read().decode('utf-8'))

        results = geocoding_payload.get('results') or []
        if not results:
            return None

        location = results[0]
        weather_url = (
            'https://api.open-meteo.com/v1/forecast?latitude='
            f"{location['latitude']}&longitude={location['longitude']}&current=temperature_2m,wind_speed_10m,weather_code&timezone=auto"
        )
        with urlopen(weather_url, timeout=5) as response:
            weather_payload = json.loads(response.read().decode('utf-8'))

        current = weather_payload.get('current') or {}
        weather_code = current.get('weather_code')
        return {
            'city': location.get('name'),
            'country': location.get('country'),
            'temperature': current.get('temperature_2m'),
            'wind_speed': current.get('wind_speed_10m'),
            'description': WEATHER_CODES.get(weather_code, 'Estado del tiempo no disponible'),
        }
    except (URLError, TimeoutError, KeyError, ValueError, TypeError):
        return None
