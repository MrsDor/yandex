import os
import sys
import random
import tkinter as tk
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import requests
from PIL import Image, ImageTk

from spn_utils import get_spn

GEOCODER_API_SERVER = "https://geocode-maps.yandex.ru/1.x/"
GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"
MAP_API_SERVER = "https://static-maps.yandex.ru/v1"
MAP_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"

# Фиксированный масштаб фрагмента 
FRAGMENT_SPN = 0.03  

CITIES = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Челябинск",
    "Самара",
    "Омск",
    "Ростов-на-Дону",
    "Уфа",
    "Красноярск",
    "Пермь",
    "Воронеж",
    "Волгоград",
]


def geocode_city(city: str) -> dict | None:
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": city,
        "format": "json",
        "kind": "locality",
        "results": 1,
    }
    response = requests.get(GEOCODER_API_SERVER, params=params)
    if not response:
        return None
    members = response.json()["response"]["GeoObjectCollection"]["featureMember"]
    return members[0]["GeoObject"] if members else None


def get_city_map(toponym: dict) -> Image.Image | None:
    lon, lat = toponym["Point"]["pos"].split()
    spn_lon, spn_lat = get_spn(toponym)

    # Смещаем центр случайно в пределах города, масштаб фиксированно мелкий
    offset_lon = random.uniform(-spn_lon * 0.3, spn_lon * 0.3)
    offset_lat = random.uniform(-spn_lat * 0.3, spn_lat * 0.3)
    shifted_lon = float(lon) + offset_lon
    shifted_lat = float(lat) + offset_lat

    params = {
        "ll": f"{shifted_lon},{shifted_lat}",
        "spn": f"{FRAGMENT_SPN},{FRAGMENT_SPN}",
        "apikey": MAP_API_KEY,
    }
    response = requests.get(MAP_API_SERVER, params=params)
    if not response:
        print(f"  Ошибка карты: {response.status_code}")
        return None
    return Image.open(BytesIO(response.content))


class SlideShowWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Угадай-ка город")
        self.root.resizable(False, False)
        self.label = tk.Label(self.root)
        self.label.pack()
        self._tk_image = None

    def show(self, image: Image.Image, prompt: str) -> None:
        self.root.title(f"Угадай-ка город — {prompt}")
        self._tk_image = ImageTk.PhotoImage(image)
        self.label.config(image=self._tk_image)
        self.root.update()
        self.root.deiconify()

    def close(self) -> None:
        self.root.withdraw()

    def destroy(self) -> None:
        self.root.destroy()


def run_game(cities: list[str]) -> None:
    order = cities[:]
    random.shuffle(order)

    score = 0
    total = len(order)

    print("=" * 50)
    print("  УГАДАЙ-КА ГОРОД")
    print("  Угадайте город по фрагменту карты.")
    print("  Введите 'пропустить' или Enter, чтобы пропустить.")
    print("  Введите 'выход' для завершения.")
    print("=" * 50)

    window = SlideShowWindow()

    for idx, city in enumerate(order, 1):
        print(f"\nГород {idx}/{total}. Загружаю карту...")

        toponym = geocode_city(city)
        if toponym is None:
            print(f"  Не удалось найти город: {city}, пропускаю.")
            continue

        image = get_city_map(toponym)
        if image is None:
            continue

        window.show(image, f"город {idx} из {total}")

        answer = input("Ваш ответ: ").strip()

        if answer.lower() == "выход":
            print("Игра прервана.")
            break

        if answer.lower() in ("", "пропустить"):
            print(f"  Правильный ответ: {city}")
            continue

        if answer.lower() == city.lower():
            print("  Верно!")
            score += 1
        else:
            print(f"  Неверно. Правильный ответ: {city}")

    window.destroy()

    print("\n" + "=" * 50)
    print(f"Игра окончена! Результат: {score} из {total}")
    print("=" * 50)


if __name__ == "__main__":
    run_game(CITIES)
