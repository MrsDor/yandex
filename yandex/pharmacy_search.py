import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from io import BytesIO

import requests
from PIL import Image

from spn_utils import get_spn

GEOCODER_API_URL = "https://geocode-maps.yandex.ru/1.x/"
GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"

SEARCH_API_URL = "https://search-maps.yandex.ru/v1/"
SEARCH_API_KEY = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

MAP_API_URL = "https://static-maps.yandex.ru/v1"
MAP_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"


def geocode(query: str) -> tuple[dict, float, float] | None:
    """Возвращает (toponym, lon, lat) или None."""
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": query,
        "format": "json",
        "results": 1,
    }
    response = requests.get(GEOCODER_API_URL, params=params)
    if not response:
        print(f"Ошибка геокодера: {response.status_code} {response.reason}")
        return None
    members = response.json()["response"]["GeoObjectCollection"]["featureMember"]
    if not members:
        print("Адрес не найден.")
        return None
    toponym = members[0]["GeoObject"]
    lon, lat = map(float, toponym["Point"]["pos"].split())
    return toponym, lon, lat


def find_pharmacy(ll: str) -> dict | None:
    """Ищет ближайшую аптеку к точке ll='lon,lat'."""
    params = {
        "apikey": SEARCH_API_KEY,
        "text": "аптека",
        "lang": "ru_RU",
        "ll": ll,
        "type": "biz",
        "results": 1,
    }
    response = requests.get(SEARCH_API_URL, params=params)
    if not response:
        print(f"Ошибка поиска: {response.status_code} {response.reason}")
        return None
    features = response.json().get("features", [])
    if not features:
        print("Аптека не найдена.")
        return None
    return features[0]


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Расстояние между двумя точками в метрах (формула Гаверсина)."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def auto_spn(lon1: float, lat1: float, lon2: float, lat2: float) -> tuple[float, float, float, float]:
    """Возвращает (center_lon, center_lat, spn_lon, spn_lat) для двух точек."""
    center_lon = (lon1 + lon2) / 2
    center_lat = (lat1 + lat2) / 2
    spn_lon = max(abs(lon2 - lon1) * 1.5, 0.005)
    spn_lat = max(abs(lat2 - lat1) * 1.5, 0.005)
    return center_lon, center_lat, spn_lon, spn_lat


def show_map(center_lon: float, center_lat: float,
             spn_lon: float, spn_lat: float,
             pt_origin: str, pt_pharmacy: str) -> None:
    params = {
        "ll": f"{center_lon},{center_lat}",
        "spn": f"{spn_lon},{spn_lat}",
        "apikey": MAP_API_KEY,
        "pt": f"{pt_origin}~{pt_pharmacy}",
    }
    response = requests.get(MAP_API_URL, params=params)
    if not response:
        print(f"Ошибка карты: {response.status_code} {response.reason}")
        return
    Image.open(BytesIO(response.content)).show()


def format_hours(org: dict) -> str:
    try:
        hours = org["properties"]["CompanyMetaData"]["Hours"]["text"]
        return hours
    except KeyError:
        return "не указано"


def main():
    if len(sys.argv) < 2:
        print("Использование: python pharmacy_search.py <адрес>")
        print("Пример: python pharmacy_search.py Москва, Тверская, 1")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Ищу адрес: {query}")

    result = geocode(query)
    if result is None:
        sys.exit(1)
    toponym, orig_lon, orig_lat = result
    orig_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
    print(f"Адрес найден: {orig_address} ({orig_lon:.6f}, {orig_lat:.6f})")

    print("Ищу ближайшую аптеку…")
    pharmacy = find_pharmacy(f"{orig_lon},{orig_lat}")
    if pharmacy is None:
        sys.exit(1)

    ph_coords = pharmacy["geometry"]["coordinates"]
    ph_lon, ph_lat = ph_coords[0], ph_coords[1]
    ph_meta = pharmacy["properties"]["CompanyMetaData"]
    ph_name = ph_meta.get("name", "—")
    ph_address = ph_meta.get("address", "—")
    ph_hours = format_hours(pharmacy)
    distance = haversine(orig_lon, orig_lat, ph_lon, ph_lat)

    print()
    print("=" * 50)
    print(f"  Аптека:    {ph_name}")
    print(f"  Адрес:     {ph_address}")
    print(f"  Режим:     {ph_hours}")
    print(f"  Расстояние: {distance:.0f} м")
    print("=" * 50)

    center_lon, center_lat, spn_lon, spn_lat = auto_spn(orig_lon, orig_lat, ph_lon, ph_lat)
    pt_origin = f"{orig_lon},{orig_lat},pm2blm"      # синяя метка — исходный адрес
    pt_pharmacy = f"{ph_lon},{ph_lat},pm2rdm"         # красная метка — аптека
    show_map(center_lon, center_lat, spn_lon, spn_lat, pt_origin, pt_pharmacy)


if __name__ == "__main__":
    main()
