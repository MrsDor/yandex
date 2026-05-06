import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import requests
from distance import lonlat_distance

GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"
GEOCODER_KEY = "8013b162-6b42-4997-9691-77b7074026e0"

WALKING_SPEED_KMH = 5.0


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
    print(f"  Найдено: {found}")
    return lon, lat


def format_time(minutes: float) -> str:
    h = int(minutes) // 60
    m = int(minutes) % 60
    if h:
        return f"{h} ч {m} мин"
    return f"{m} мин"


def main():
    print("=== Расстояние от дома до школы ===\n")

    home_addr = input("Введите адрес дома: ").strip()
    school_addr = input("Введите адрес школы: ").strip()

    print("\nГеокодирую дом…")
    home = geocode(home_addr)
    if home is None:
        sys.exit(1)

    print("Геокодирую школу…")
    school = geocode(school_addr)
    if school is None:
        sys.exit(1)

    dist_m = lonlat_distance(home, school)
    dist_km = dist_m / 1000
    walk_min = (dist_km / WALKING_SPEED_KMH) * 60

    print(f"\nРасстояние: {dist_m:.0f} м ({dist_km:.2f} км)")
    print(f"Время пешком (~{WALKING_SPEED_KMH:.0f} км/ч): {format_time(walk_min)}")


if __name__ == "__main__":
    main()
