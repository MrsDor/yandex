import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from io import BytesIO

import requests
from PIL import Image

from spn_utils import get_spn

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


def find_pharmacies(lon: float, lat: float, count: int = 10) -> list:
    params = {
        "apikey": SEARCH_API_KEY,
        "text": "аптека",
        "lang": "ru_RU",
        "ll": f"{lon},{lat}",
        "type": "biz",
        "results": count,
    }
    response = requests.get(SEARCH_API_SERVER, params=params)
    if not response:
        print(f"Ошибка поиска: {response.status_code} {response.reason}")
        return []
    return response.json().get("features", [])


def pharmacy_color(pharmacy: dict) -> str:
    """
    Возвращает цвет маркера:
      зелёный  (gn) — круглосуточно,
      синий    (bl) — есть часы, но не круглосуточно,
      серый    (gr) — данных нет.
    """
    try:
        hours_text = pharmacy["properties"]["CompanyMetaData"]["Hours"]["text"].lower()
        if "круглосуточно" in hours_text or "24" in hours_text:
            return "gn"
        return "bl"
    except KeyError:
        return "gr"


def build_pt_param(origin_lon: float, origin_lat: float, pharmacies: list) -> str:
    # Исходная точка — красная метка (флаг)
    parts = [f"{origin_lon},{origin_lat},flag"]
    color_map = {"gn": "gn", "bl": "bl", "gr": "gr"}
    for ph in pharmacies:
        ph_lon, ph_lat = ph["geometry"]["coordinates"]
        color = pharmacy_color(ph)
        parts.append(f"{ph_lon},{ph_lat},pm2{color_map[color]}m")
    return "~".join(parts)


def auto_bbox(origin_lon: float, origin_lat: float, pharmacies: list) -> tuple[str, str]:
    all_lons = [origin_lon] + [ph["geometry"]["coordinates"][0] for ph in pharmacies]
    all_lats = [origin_lat] + [ph["geometry"]["coordinates"][1] for ph in pharmacies]
    center_lon = (min(all_lons) + max(all_lons)) / 2
    center_lat = (min(all_lats) + max(all_lats)) / 2
    spn_lon = max((max(all_lons) - min(all_lons)) * 1.4, 0.005)
    spn_lat = max((max(all_lats) - min(all_lats)) * 1.4, 0.005)
    return f"{center_lon},{center_lat}", f"{spn_lon},{spn_lat}"


def show_map(origin_lon: float, origin_lat: float, pharmacies: list) -> None:
    ll, spn = auto_bbox(origin_lon, origin_lat, pharmacies)
    params = {
        "ll": ll,
        "spn": spn,
        "apikey": MAP_API_KEY,
        "pt": build_pt_param(origin_lon, origin_lat, pharmacies),
    }
    response = requests.get(MAP_API_SERVER, params=params)
    if not response:
        print(f"Ошибка карты: {response.status_code} {response.reason}")
        return
    image = Image.open(BytesIO(response.content))
    image.show()


def main():
    if len(sys.argv) < 2:
        print("Использование: python pharmacies.py <адрес>")
        print("Пример: python pharmacies.py Москва, Тверская, 1")
        sys.exit(1)

    address = " ".join(sys.argv[1:])
    print(f"Ищу адрес: {address}")

    coords = geocode_address(address)
    if coords is None:
        sys.exit(1)
    origin_lon, origin_lat = coords

    pharmacies = find_pharmacies(origin_lon, origin_lat, count=10)
    if not pharmacies:
        print("Аптеки не найдены.")
        sys.exit(1)

    print(f"\nНайдено аптек: {len(pharmacies)}\n")
    print(f"{'#':<3} {'Название':<35} {'Часы работы':<30} {'Цвет'}")
    print("-" * 80)
    for i, ph in enumerate(pharmacies, 1):
        meta = ph["properties"]["CompanyMetaData"]
        name = meta.get("name", "—")[:34]
        try:
            hours = meta["Hours"]["text"][:29]
        except KeyError:
            hours = "нет данных"
        color_map = {"gn": "зелёный (круглосуточно)", "bl": "синий", "gr": "серый (нет данных)"}
        color = color_map[pharmacy_color(ph)]
        print(f"{i:<3} {name:<35} {hours:<30} {color}")

    show_map(origin_lon, origin_lat, pharmacies)


if __name__ == "__main__":
    main()
