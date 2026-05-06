import os
import sys

import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

STATIC_API_URL = "https://static-maps.yandex.ru/1.x/"
STATIC_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
GEOCODER_API_URL = "https://geocode-maps.yandex.ru/1.x/"
GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"
MAP_FILE = "map.png"

# Широта Финского залива — безопасная зона открытой воды
GULF_LAT = 59.930


def geocode(query: str) -> tuple[float, float]:
    """Возвращает (lon, lat) объекта через Geocoder API."""
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": query,
        "format": "json",
        "results": 1,
    }
    response = requests.get(GEOCODER_API_URL, params=params)
    if not response:
        print(f"Ошибка геокодера: {response.status_code} {response.reason}")
        sys.exit(1)
    members = response.json()["response"]["GeoObjectCollection"]["featureMember"]
    if not members:
        print(f"Не найдено: {query}")
        sys.exit(1)
    lon, lat = map(float, members[0]["GeoObject"]["Point"]["pos"].split())
    return lon, lat


def build_route(start: tuple[float, float], end: tuple[float, float]) -> list[tuple[float, float]]:
    """
    Строит водный маршрут от start до end через Финский залив:
    - из точки старта прямо на север до открытой воды (GULF_LAT)
    - по заливу на восток
    - из залива прямо на юг к точке финиша
    """
    s_lon, s_lat = start
    e_lon, e_lat = end
    mid_lat = GULF_LAT
    return [
        (s_lon, s_lat),          # причал Петергофа
        (s_lon, mid_lat),        # по морскому каналу строго на север
        (e_lon, mid_lat),        # по заливу строго на восток
        (e_lon, e_lat),          # вдоль набережной строго на юг к Эрмитажу
    ]


def build_polyline(points: list[tuple[float, float]]) -> str:
    coords = ",".join(f"{lon},{lat}" for lon, lat in points)
    return f"c:0000FFFF,w:5,{coords}"


def fetch_map(route: list[tuple[float, float]]) -> bytes | None:
    pl = build_polyline(route)
    start, end = route[0], route[-1]
    pt = f"{start[0]},{start[1]},pm2grm~{end[0]},{end[1]},pm2rdm"

    center_lon = (start[0] + end[0]) / 2
    center_lat = (start[1] + end[1]) / 2
    spn_lon = round(abs(end[0] - start[0]) * 1.3, 3)
    spn_lat = round(abs(GULF_LAT - min(start[1], end[1])) * 2.2, 3)

    params = {
        "ll": f"{center_lon},{center_lat}",
        "spn": f"{spn_lon},{spn_lat}",
        "apikey": STATIC_API_KEY,
        "l": "map",
        "pl": pl,
        "pt": pt,
    }
    response = requests.get(STATIC_API_URL, params=params)
    if response:
        return response.content
    print(f"Ошибка: {response.status_code} {response.reason}")
    return None


class MapWindow(QWidget):
    def __init__(self, route: list[tuple[float, float]]):
        super().__init__()
        self.map_file = MAP_FILE
        self.route = route
        self.setWindowTitle("Маршрут судна «Петергоф — Эрмитаж»")
        self._build_ui()
        self._load_map()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.map_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.map_label.setMinimumSize(900, 400)
        self.map_label.setStyleSheet("background: #222;")
        layout.addWidget(self.map_label)

        info = QLabel(
            "Маршрут судна на подводных крыльях: Петергоф → Эрмитаж\n"
            "Зелёная метка — Петергоф (отправление)   |   Красная метка — Эрмитаж (прибытие)"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("padding: 6px; font-size: 13px;")
        layout.addWidget(info)

    def _load_map(self):
        data = fetch_map(self.route)
        if data is None:
            self.map_label.setText("Не удалось загрузить карту.")
            return
        with open(self.map_file, "wb") as f:
            f.write(data)
        pixmap = QPixmap(self.map_file)
        self.map_label.setPixmap(
            pixmap.scaled(
                self.map_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def closeEvent(self, event):
        if os.path.exists(self.map_file):
            os.remove(self.map_file)
        event.accept()


def main():
    print("Геокодирую причал Петергофа…")
    start = geocode("Петергоф морской причал")
    print(f"  Петергоф: {start}")

    print("Геокодирую причал у Эрмитажа…")
    end = geocode("Санкт-Петербург Дворцовая набережная причал")
    print(f"  Эрмитаж:  {end}")

    route = build_route(start, end)

    app = QApplication(sys.argv)
    window = MapWindow(route)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
