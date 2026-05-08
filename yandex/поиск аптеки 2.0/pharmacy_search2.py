import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from io import BytesIO

import requests
from PIL import Image

GEOCODER_API_SERVER = "https://geocode-maps.yandex.ru/1.x/"
GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"

SEARCH_API_SERVER = "https://search-maps.yandex.ru/v1/"
SEARCH_API_KEY = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

MAP_API_SERVER = "https://static-maps.yandex.ru/v1"
MAP_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"


def geocode_address(address: str) -> tuple[float, float] | None:
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": address,
        "format": "json",
        "results": 1,
    }
    response = requests.get(GEOCODER_API_SERVER, params=params)
    if not response:
        print(f"Ошибка геокодера: {response.status_code} {response.reason}")
        return None
    members = response.json()["response"]["GeoObjectCollection"]["featureMember"]
    if not members:
        print("Адрес не найден.")
        return None
    pos = members[0]["GeoObject"]["Point"]["pos"].split()
    return float(pos[0]), float(pos[1])


def find_nearest_pharmacy(lon: float, lat: float) -> dict | None:
    params = {
        "apikey": SEARCH_API_KEY,
        "text": "аптека",
        "lang": "ru_RU",
        "ll": f"{lon},{lat}",
        "type": "biz",
        "results": 1,
    }
    response = requests.get(SEARCH_API_SERVER, params=params)
    if not response:
        print(f"Ошибка поиска: {response.status_code} {response.reason}")
        return None
    features = response.json().get("features", [])
    if not features:
        print("Аптека не найдена.")
        return None
    return features[0]


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371000  # метры
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def auto_bbox(lon1: float, lat1: float, lon2: float, lat2: float) -> tuple[str, str]:
    center_lon = (lon1 + lon2) / 2
    center_lat = (lat1 + lat2) / 2
    spn_lon = max(abs(lon2 - lon1) * 1.5, 0.005)
    spn_lat = max(abs(lat2 - lat1) * 1.5, 0.005)
    ll = f"{center_lon},{center_lat}"
    spn = f"{spn_lon},{spn_lat}"
    return ll, spn


def show_map(origin_lon: float, origin_lat: float, pharmacy_lon: float, pharmacy_lat: float) -> None:
    ll, spn = auto_bbox(origin_lon, origin_lat, pharmacy_lon, pharmacy_lat)
    params = {
        "ll": ll,
        "spn": spn,
        "apikey": MAP_API_KEY,
        "pt": f"{origin_lon},{origin_lat},pm2blm~{pharmacy_lon},{pharmacy_lat},pm2rdm",
    }
    response = requests.get(MAP_API_SERVER, params=params)
    if not response:
        print(f"Ошибка карты: {response.status_code} {response.reason}")
        return
    image = Image.open(BytesIO(response.content))
    image.show()


def format_hours(pharmacy: dict) -> str:
    try:
        hours = pharmacy["properties"]["CompanyMetaData"]["Hours"]["text"]
        return hours
    except KeyError:
        return "не указано"


def main():
    if len(sys.argv) < 2:
        print("Использование: python pharmacy_search2.py <адрес>")
        print("Пример: python pharmacy_search2.py Москва, Тверская, 1")
        sys.exit(1)

    address = " ".join(sys.argv[1:])
    print(f"Ищу адрес: {address}")

    coords = geocode_address(address)
    if coords is None:
        sys.exit(1)
    origin_lon, origin_lat = coords
    print(f"Координаты: {origin_lon}, {origin_lat}")

    pharmacy = find_nearest_pharmacy(origin_lon, origin_lat)
    if pharmacy is None:
        sys.exit(1)

    meta = pharmacy["properties"]["CompanyMetaData"]
    ph_lon, ph_lat = pharmacy["geometry"]["coordinates"]

    distance = haversine(origin_lon, origin_lat, ph_lon, ph_lat)
    if distance < 1000:
        distance_str = f"{distance:.0f} м"
    else:
        distance_str = f"{distance / 1000:.2f} км"

    print()
    print("=" * 40)
    print(f"Название:    {meta.get('name', '—')}")
    print(f"Адрес:       {meta.get('address', '—')}")
    print(f"Часы работы: {format_hours(pharmacy)}")
    print(f"Расстояние:  {distance_str}")
    print("=" * 40)

    show_map(origin_lon, origin_lat, ph_lon, ph_lat)


if __name__ == "__main__":
    main()
