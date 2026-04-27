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

MAP_API_SERVER = "https://static-maps.yandex.ru/v1"
MAP_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"


def find_toponym(query: str) -> dict | None:
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": query,
        "format": "json",
        "results": 1,
    }
    response = requests.get(GEOCODER_API_SERVER, params=params)
    if not response:
        print(f"Ошибка геокодера: {response.status_code} {response.reason}")
        return None
    members = response.json()["response"]["GeoObjectCollection"]["featureMember"]
    if not members:
        print("Объект не найден.")
        return None
    return members[0]["GeoObject"]


def show_map(toponym: dict) -> None:
    lon, lat = toponym["Point"]["pos"].split()
    spn_lon, spn_lat = get_spn(toponym)

    params = {
        "ll": f"{lon},{lat}",
        "spn": f"{spn_lon},{spn_lat}",
        "apikey": MAP_API_KEY,
        "pt": f"{lon},{lat},pm2rdm",
    }
    response = requests.get(MAP_API_SERVER, params=params)
    if not response:
        print(f"Ошибка карты: {response.status_code} {response.reason}")
        return

    image = Image.open(BytesIO(response.content))
    image.show()


def main():
    if len(sys.argv) < 2:
        print("Использование: python full_search.py <запрос>")
        print("Пример: python full_search.py Москва, Тверская, 1")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Ищу: {query}")

    toponym = find_toponym(query)
    if toponym is None:
        sys.exit(1)

    name = toponym.get("name", "—")
    address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
    lon, lat = toponym["Point"]["pos"].split()
    spn_lon, spn_lat = get_spn(toponym)

    print(f"Найдено:  {name}")
    print(f"Адрес:    {address}")
    print(f"Координаты: {lon}, {lat}")
    print(f"Масштаб spn: {spn_lon:.6f}, {spn_lat:.6f}")

    show_map(toponym)


if __name__ == "__main__":
    main()
