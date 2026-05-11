import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import requests

GEOCODER_API_SERVER = "https://geocode-maps.yandex.ru/1.x/"
GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"


def geocode(query: str, kind: str = None) -> list:
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": query,
        "format": "json",
        "results": 1,
    }
    if kind:
        params["kind"] = kind
    response = requests.get(GEOCODER_API_SERVER, params=params)
    if not response:
        print(f"Ошибка геокодера: {response.status_code} {response.reason}")
        return []
    return response.json()["response"]["GeoObjectCollection"]["featureMember"]


def main():
    if len(sys.argv) < 2:
        print("Использование: python district.py <адрес>")
        print("Пример: python district.py Москва, Тверская, 1")
        sys.exit(1)

    address = " ".join(sys.argv[1:])

    # Шаг 1: найти координаты адреса
    members = geocode(address)
    if not members:
        print("Адрес не найден.")
        sys.exit(1)

    geo = members[0]["GeoObject"]
    pos = geo["Point"]["pos"]
    lon, lat = pos.split()
    found_address = geo["metaDataProperty"]["GeocoderMetaData"]["text"]
    print(f"Адрес:       {found_address}")
    print(f"Координаты:  {lon}, {lat}")

    # Шаг 2: по координатам найти район (kind=district)
    members = geocode(f"{lon},{lat}", kind="district")
    if not members:
        print("Район не определён.")
        sys.exit(1)

    district_obj = members[0]["GeoObject"]
    district_name = district_obj["name"]
    district_full = district_obj["metaDataProperty"]["GeocoderMetaData"]["text"]

    print(f"Район:       {district_name}")
    print(f"Полный путь: {district_full}")


if __name__ == "__main__":
    main()
