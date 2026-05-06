import sys
import math
sys.stdout.reconfigure(encoding="utf-8")

import requests

GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"
GEOCODER_KEY = "8013b162-6b42-4997-9691-77b7074026e0"

OSTANKINO_COORDS = (37.6116, 55.8197)
TOWER_HEIGHT = 525


def geocode(address: str) -> tuple[float, float] | None:
    params = {
        "apikey": GEOCODER_KEY,
        "geocode": address,
        "format": "json",
        "results": 1,
    }
    response = requests.get(GEOCODER_URL, params=params)
    if not response:
        print(f"Ошибка геокодера: {response.status_code} {response.reason}")
        return None
    members = response.json()["response"]["GeoObjectCollection"]["featureMember"]
    if not members:
        print(f"Адрес не найден: {address}")
        return None
    lon, lat = map(float, members[0]["GeoObject"]["Point"]["pos"].split())
    found = members[0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"]
    print(f"Найдено: {found}")
    return lon, lat


def main():
    address = input("Введите населённый пункт или адрес: ").strip()

    coords = geocode(address)
    if coords is None:
        sys.exit(1)

    lon, lat = coords
    t_lon, t_lat = OSTANKINO_COORDS

    avg_lat = math.radians((lat + t_lat) / 2)
    dx = abs(lon - t_lon) * 111 * math.cos(avg_lat)
    dy = abs(lat - t_lat) * 111
    l = math.sqrt(dx ** 2 + dy ** 2)

    sqrt_h2 = l / 3.6 - math.sqrt(TOWER_HEIGHT)
    h2 = 0.0 if sqrt_h2 <= 0 else sqrt_h2 ** 2

    print(f"\nРасстояние до Останкинской башни: {l:.1f} км")
    if h2 == 0:
        print("Приёмная антенна не требует подъёма (точка в зоне прямой видимости).")
    else:
        print(f"Минимальная высота приёмной антенны: {h2:.1f} м")


if __name__ == "__main__":
    main()
