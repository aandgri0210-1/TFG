import json
from functools import lru_cache
from math import radians, sin, cos, sqrt, atan2
from urllib.parse import quote_plus
from urllib.request import urlopen

from django.conf import settings

# Geoapify forward geocoding endpoints
GEOAPIFY_SEARCH_URL = 'https://api.geoapify.com/v1/geocode/search?text={query}&limit={limit}&lang={language}&apiKey={key}&format=json&filter=countrycode:{country}'

# Prefer key from Django settings
GEOAPIFY_API_KEY = getattr(settings, 'GEOAPIFY_API_KEY', '').strip()

# Fallback list of Spanish municipalities including cities and towns (when API key is not available)
FALLBACK_SPANISH_MUNICIPALITIES = [
    # Grandes ciudades
    ('Madrid', 40.416775, -3.703790),
    ('Barcelona', 41.385064, 2.173403),
    ('Valencia', 39.469301, -0.376288),
    ('Sevilla', 37.389092, -5.984459),
    ('Zaragoza', 41.648823, -0.889085),
    ('Málaga', 36.721261, -4.421236),
    ('Bilbao', 43.263588, -2.934496),
    ('Murcia', 37.986006, -1.130472),
    ('Alicante', 38.345405, -0.481050),
    ('Córdoba', 37.884697, -4.779388),
    # Ciudades medianas
    ('Palma', 39.569541, 2.750340),
    ('Las Palmas', 28.102733, -15.587126),
    ('Almería', 36.839874, -2.393832),
    ('Oviedo', 43.360475, -5.849392),
    ('Santander', 43.462222, -3.809722),
    ('Ávila', 40.656295, -4.699047),
    ('Burgos', 42.340695, -3.699136),
    ('Cuenca', 40.073056, -1.131389),
    ('Guadalajara', 40.634206, -3.163935),
    ('Jaén', 37.768648, -3.790009),
    ('Toledo', 39.858889, -4.027222),
    ('Valladolid', 41.652251, -4.724792),
    ('Salamanca', 40.969250, -5.663389),
    ('Cádiz', 36.540150, -6.298755),
    ('Granada', 37.176050, -3.597892),
    ('Huelva', 37.261389, -6.949444),
    ('Lugo', 42.611389, -8.328056),
    ('A Coruña', 43.361389, -8.388611),
    ('Pontevedra', 42.433056, -8.644167),
    ('Ourense', 42.338611, -7.862778),
    ('Lleida', 41.614901, 0.621170),
    ('Girona', 41.984600, 2.826065),
    ('Tarragona', 41.117222, 1.244444),
    ('Huesca', 42.138056, -0.408333),
    ('Teruel', 40.356389, -1.108333),
    ('Soria', 41.764444, -2.473333),
    ('Albacete', 38.984722, -1.858889),
    ('Ciudad Real', 38.988333, -3.924167),
    # Pueblos y municipios - Andalucía
    ('Ronda', 36.747222, -5.163056),
    ('Marbella', 36.509722, -4.888889),
    ('Nerja', 36.748333, -3.869722),
    ('Torremolinos', 36.737778, -4.128056),
    ('Benalmádena', 36.598333, -4.114444),
    ('Antequera', 37.024167, -4.573056),
    ('Lucena', 37.387500, -4.483333),
    ('Montilla', 37.611389, -4.627500),
    ('Osuna', 37.235278, -5.385833),
    ('Marchena', 37.352500, -5.419167),
    ('Jerez de la Frontera', 36.683611, -6.135000),
    ('Sanlúcar de Barrameda', 36.777500, -6.348889),
    ('Chipiona', 36.734722, -6.432222),
    ('Conil de la Frontera', 36.252778, -6.064167),
    ('Barbate', 36.176944, -5.945556),
    ('Ubrique', 36.627222, -5.383889),
    ('Alhaurín de la Torre', 36.763611, -4.327778),
    ('Alhauría de Granada', 36.883889, -3.793889),
    # Pueblos y municipios - Madrid y alrededores
    ('Alcalá de Henares', 40.483056, -3.358889),
    ('Leganés', 40.334722, -3.763611),
    ('Getafe', 40.308333, -3.730556),
    ('Fuenlabrada', 40.294444, -3.808889),
    ('Alcobendas', 40.533889, -3.633889),
    ('San Sebastián de los Reyes', 40.554444, -3.632778),
    ('Pinto', 40.283056, -3.640556),
    ('Mostoles', 40.332778, -3.877222),
    ('Torrejón de Ardoz', 40.465278, -3.510000),
    ('Coslada', 40.433889, -3.582222),
    ('Arganda del Rey', 40.293611, -3.428889),
    # Pueblos y municipios - Cataluña
    ('Sabadell', 41.544444, 2.108889),
    ('Terrassa', 41.561111, 2.020833),
    ('Mataró', 41.538889, 2.441667),
    ('Granollers', 41.602222, 2.281667),
    ('Manresa', 41.730556, 1.833333),
    ('Berga', 42.078889, 1.906111),
    ('Puigcerdà', 42.442222, 1.951667),
    ('Solsona', 42.012222, 1.542222),
    ('Vic', 41.930556, 2.251111),
    ('Igualada', 41.576389, 1.609167),
    ('Tàrrega', 41.730556, 1.304167),
    ('Cervera', 41.672222, 1.276667),
    # Pueblos y municipios - País Vasco
    ('Vitoria', 42.845417, -2.672467),
    ('Donostia', 43.318333, -1.981389),
    ('Getxo', 43.333333, -3.026389),
    ('Barakaldo', 43.306944, -3.095556),
    ('Rentería', 43.305556, -1.873889),
    ('Tolosa', 43.182222, -2.103889),
    ('Bergara', 43.147222, -2.282222),
    ('Oñati', 43.051389, -2.460833),
    ('Ordicia', 43.126111, -2.142222),
    # Pueblos y municipios - Valencia
    ('Castelló de la Plana', 39.986111, 0.043611),
    ('Gandia', 38.971389, -0.169722),
    ('Torrent', 39.432222, -0.519167),
    ('Requena', 39.778056, -1.165278),
    ('Chiva', 39.393889, -0.608889),
    ('Denia', 38.853333, 0.103333),
    ('Jávea', 38.748889, 0.175833),
    ('Benidorm', 38.540000, 0.120000),
    ('Altea', 38.603333, 0.056389),
    # Pueblos y municipios - Islas Baleares
    ('Ibiza', 38.905556, 1.431111),
    ('Maó', 39.890833, 4.265833),
    ('Pollença', 39.881667, 3.137222),
    ('Sóller', 39.766111, 2.733611),
    ('Port de Sóller', 39.763611, 2.720000),
    ('Valldemossa', 39.754444, 2.653056),
    ('Calvià', 39.607222, 2.431111),
    ('Marratxí', 39.476389, 2.898889),
    # Pueblos y municipios - Castilla y León
    ('Segovia', 40.954726, -4.119191),
    ('León', 42.598779, -5.567029),
    ('Ponferrada', 42.544167, -6.596389),
    ('Benavente', 42.382778, -5.670833),
    ('Medina del Campo', 41.393889, -4.903333),
    ('Aranda de Duero', 41.671111, -3.686111),
    ('Soria', 41.764444, -2.473333),
    ('Ólvega', 41.926111, -2.466667),
    ('Numancia', 41.781667, -2.316667),
    ('Ávilès', 41.790556, -5.937500),
    ('Gijón', 43.544444, -5.661389),
    ('Aviles', 43.554167, -5.918889),
    # Pueblos y municipios - Extremadura
    ('Badajoz', 38.879167, -6.970278),
    ('Cáceres', 39.476667, -6.371111),
    ('Plasencia', 40.076111, -6.082500),
    ('Trujillo', 39.446944, -5.917222),
    ('Mérida', 38.918333, -6.340833),
    ('Hervás', 40.273889, -5.857222),
    ('Montijo', 39.046944, -6.692500),
    ('Zafra', 38.429722, -6.409167),
    ('Fregenal de la Sierra', 38.164167, -6.484444),
    ('Llerena', 38.286667, -6.302500),
    # Pueblos y municipios - Galicia
    ('Santiago de Compostela', 42.880139, -8.544444),
    ('Vigo', 42.231389, -8.723889),
    ('Ferrol', 43.479167, -8.255000),
    ('Noia', 42.770833, -9.018056),
    ('Muros', 42.777778, -9.076389),
    ('Oleiros', 43.343056, -8.366667),
    ('Neves', 42.050556, -8.717222),
    ('Villagarcía de Arosa', 42.605278, -8.766667),
    ('Cambados', 42.586389, -8.720556),
    ('Ribadumia', 42.639444, -8.789444),
    # Pueblos y municipios - Canarias
    ('Santa Cruz de Tenerife', 28.462778, -16.253333),
    ('Las Palmas de Gran Canaria', 28.102733, -15.587126),
    ('San Cristóbal de La Laguna', 28.487500, -16.318056),
    ('Puerto de la Cruz', 28.413056, -16.313056),
    ('Arrecife', 28.959722, -13.640833),
    ('Yaiza', 28.923333, -13.782222),
    ('Tegueste', 28.534722, -16.316667),
    # Pueblos y municipios - Asturias
    ('Gijón', 43.544444, -5.661389),
    ('Avilés', 43.554167, -5.918889),
    ('Mieres', 43.243333, -5.788889),
    ('Langreo', 43.267222, -5.611667),
    ('Llanera', 43.361111, -5.863333),
    ('Cabrales', 43.329167, -4.820833),
    ('Cabranes', 43.392222, -5.222222),
    # Pueblos y municipios - Murcia
    ('Lorca', 37.673333, -1.700000),
    ('Cartagena', 37.606111, -0.990000),
    ('Alcantarilla', 37.938611, -1.280833),
    ('Molina de Segura', 38.048889, -1.316389),
    ('Jumilla', 38.483611, -1.325278),
    ('Yecla', 38.615833, -1.125833),
    # Pueblos y municipios - Navarra
    ('Pamplona', 42.812526, -1.645773),
    ('Tudela', 42.072222, -1.594167),
    ('Estella', 42.680000, -2.041667),
    ('Sangüesa', 42.561667, -1.541667),
    ('Olite', 42.476111, -1.666111),
    ('Corella', 42.202222, -1.718611),
    # Pueblos y municipios - La Rioja
    ('Logroño', 42.465556, -2.445833),
    ('Calahorra', 42.304167, -2.079444),
    ('Haro', 42.629167, -2.862222),
    ('Santo Domingo de la Calzada', 42.433333, -3.050000),
    ('Nájera', 42.428889, -3.165556),
    # Pueblos y municipios - Aragón
    ('Barbastro', 41.780833, 0.119444),
    ('Monzón', 41.918333, 0.224167),
    ('Calatayud', 41.353611, -1.644444),
    ('Daroca', 41.226667, -1.408333),
    ('Utebo', 41.729444, -0.809444),
    ('Ejea de los Caballeros', 42.165000, -1.351667),
    ('Tarazona', 41.915556, -1.729167),
    # Pueblos y municipios - Castilla-La Mancha
    ('Puertollano', 38.701111, -4.098333),
    ('Alcázar de San Juan', 39.386389, -3.199722),
    ('Tomelloso', 39.166667, -3.001667),
    ('Valdepeñas', 38.761111, -3.426389),
    ('Talavera de la Reina', 39.952222, -4.331111),
    ('Cuenca', 40.073056, -1.131389),
    ('Hellín', 38.754167, -2.109444),
]


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two coordinates."""
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def _normalize_result(result):
    # Geoapify sometimes returns a flat dict or nested under 'properties'
    props = result.get('properties') or result
    lat = props.get('lat') or props.get('latitude') or props.get('y')
    lon = props.get('lon') or props.get('longitude') or props.get('x')
    formatted = props.get('formatted') or props.get('name') or ''
    place_id = props.get('place_id') or props.get('gid') or None
    if not place_id:
        # Build a stable-ish fallback id from coords + label
        if lat is not None and lon is not None:
            place_id = f'geoapify:{lat}:{lon}:{formatted}'
        else:
            place_id = formatted

    # Round coordinates to 6 decimal places (max precision for DecimalField in Service model)
    if lat is not None:
        lat = round(float(lat), 6)
    if lon is not None:
        lon = round(float(lon), 6)

    return {
        'place_id': place_id,
        'label': formatted,
        'latitude': lat,
        'longitude': lon,
        'country': props.get('country') or props.get('country_code'),
        'municipality': props.get('city') or props.get('town') or props.get('village') or props.get('county') or '',
    }


@lru_cache(maxsize=256)
def search_locations(query, limit=6, country='ES', language='es', typeahead=True):
    query = (query or '').strip()
    if not query or not GEOAPIFY_API_KEY:
        return []

    url = GEOAPIFY_SEARCH_URL.format(
        query=quote_plus(query),
        limit=limit,
        language=language,
        key=GEOAPIFY_API_KEY,
        country=country.lower(),
    )

    try:
        with urlopen(url, timeout=6) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except Exception:
        return []

    # Geoapify may return results in 'results' or 'features'; normalize to iterable
    raw_results = payload.get('results') or payload.get('features') or []
    return [_normalize_result(r) for r in raw_results]


def validate_location(query, place_id):
    if not query or not place_id:
        return None
    # If we have an API key, try to find exact place_id in strict search
    if GEOAPIFY_API_KEY:
        for location in search_locations(query, limit=10, country='ES', language='es', typeahead=False):
            if location['place_id'] == place_id:
                return location
        return None

    # No API key: support fallback place_ids created from FALLBACK_SPANISH_MUNICIPALITIES
    # Fallback place_id format: 'fallback:Name'
    if isinstance(place_id, str) and place_id.startswith('fallback:'):
        name = place_id.split(':', 1)[1]
        for nm, lat, lon in FALLBACK_SPANISH_MUNICIPALITIES:
            if nm.lower() == name.lower():
                return {
                    'place_id': f'fallback:{nm}',
                    'label': nm,
                    'latitude': lat,
                    'longitude': lon,
                    'country': 'ES',
                    'municipality': nm,
                }
    return None


def resolve_map_location(service):
    """Resolve map location with city validation.
    
    Priority:
    1. Use stored coordinates if available
    2. Search full address but validate it's within city boundaries
    3. Fallback to city centroid if address not in city or not found
    """
    # If already stored coords, return them
    latitude = service.latitude
    longitude = service.longitude
    if latitude is not None and longitude is not None:
        return {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'label': service.city,
        }

    # Get city reference coordinates first
    city_locations = search_locations(service.city, limit=1, country='ES', language='es', typeahead=False)
    if not city_locations:
        return None
    
    city_ref = city_locations[0]
    city_lat = city_ref['latitude']
    city_lon = city_ref['longitude']
    max_distance_km = 25  # Accept results within 25km of city center
    
    # Try full address if provided
    if service.address:
        query = f"{service.address}, {service.city}"
        address_locations = search_locations(query, limit=5, country='ES', language='es', typeahead=False)
        
        # Validate results are within city radius
        for loc in address_locations:
            if loc['latitude'] is not None and loc['longitude'] is not None:
                distance = _haversine(city_lat, city_lon, loc['latitude'], loc['longitude'])
                # Must be in same city (within radius) and label must contain city name
                if distance <= max_distance_km and service.city.lower() in (loc.get('label', '') or '').lower():
                    return {
                        'latitude': loc['latitude'],
                        'longitude': loc['longitude'],
                        'label': loc['label'],
                    }
    
    # Fallback to city centroid if address not found or out of range
    return {
        'latitude': city_lat,
        'longitude': city_lon,
        'label': city_ref['label'],
    }


def search_municipalities(query, limit=12):
    """Search for municipalities/cities in Spain only (not full addresses).
    
    Returns only official municipalities/towns/villages with place_ids,
    excluding arbitrary street addresses or points of interest.
    """
    query = (query or '').strip()
    if not query:
        return []

    # If API key is not available, use fallback list
    if not GEOAPIFY_API_KEY:
        return _search_fallback_municipalities(query, limit)
    
    # Use the same search endpoint but filter results to ones that include a municipality/city
    candidates = search_locations(query, limit=limit*2, country='ES', language='es', typeahead=True)
    
    # Filter to official municipalities: must have municipality name, place_id, and valid coordinates
    municipalities = []
    for c in candidates:
        # Skip if no municipality name or place_id
        if not c.get('municipality') or not c.get('place_id'):
            continue
        # Skip if no valid coordinates
        if c.get('latitude') is None or c.get('longitude') is None:
            continue
        municipalities.append(c)
        if len(municipalities) >= limit:
            break
    
    return municipalities


def _search_fallback_municipalities(query, limit=6):
    """Fallback search when API key is not available.
    
    Searches the static list of popular Spanish municipalities.
    """
    query_lower = query.lower()
    results = []
    
    for name, lat, lon in FALLBACK_SPANISH_MUNICIPALITIES:
        if query_lower in name.lower():
            results.append({
                'place_id': f'fallback:{name}',
                'label': name,
                'latitude': lat,
                'longitude': lon,
                'country': 'ES',
                'municipality': name,
            })
            if len(results) >= limit:
                break
    
    return results


def reverse_location(lat, lon, language='es'):
    """Reverse geocode coordinates to a municipality-like result.

    Returns a normalized dict matching search_locations/_normalize_result structure,
    or None if nothing suitable is found.
    """
    # If API key is available, use Geoapify reverse endpoint
    if GEOAPIFY_API_KEY:
        try:
            url = f"https://api.geoapify.com/v1/geocode/reverse?lat={lat}&lon={lon}&lang={language}&apiKey={GEOAPIFY_API_KEY}&format=json"
            with urlopen(url, timeout=6) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except Exception:
            return None

        raw_results = payload.get('results') or payload.get('features') or []
        if not raw_results:
            return None
        # Prefer the first result that includes a municipality/town/village
        for r in raw_results:
            norm = _normalize_result(r)
            if norm.get('municipality'):
                return norm
        # fallback to the first normalized result
        return _normalize_result(raw_results[0])

    # No API key: pick nearest municipality from fallback list
    best = None
    best_dist = None
    for name, mlat, mlon in FALLBACK_SPANISH_MUNICIPALITIES:
        dist = _haversine(lat, lon, mlat, mlon)
        if best is None or dist < best_dist:
            best = (name, mlat, mlon)
            best_dist = dist

    if best and best_dist is not None and best_dist <= 200:  # arbitrary 200km max
        name, mlat, mlon = best
        return {
            'place_id': f'fallback:{name}',
            'label': name,
            'latitude': round(float(mlat), 6),
            'longitude': round(float(mlon), 6),
            'country': 'ES',
            'municipality': name,
        }

    return None
