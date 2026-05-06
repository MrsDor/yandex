import os
import sys
import math

import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

STATIC_API_URL = "https://static-maps.yandex.ru/1.x/"
STATIC_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
MAP_FILE = "map.png"

POINTS = [
    (37.6173,  55.7558),
    (39.7015,  47.2357),
    (44.0075,  56.3269),
    (49.1221,  55.7887),
    (60.5975,  56.8519),
    (82.9346,  55.0302),
]

LABELS = [
    "Москва", "Ростов-на-Дону", "Нижний Новгород",
    "Казань", "Екатеринбург", "Новосибирск",
]


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def segment_lengths(points: list[tuple[float, float]]) -> list[float]:
    return [haversine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
            for i in range(len(points) - 1)]


def middle_point(points: list[tuple[float, float]]) -> tuple[float, float]:
    lengths = segment_lengths(points)
    total = sum(lengths)
    half = total / 2

    accumulated = 0.0
    for i, seg_len in enumerate(lengths):
        if accumulated + seg_len >= half:
            remaining = half - accumulated
            t = remaining / seg_len
            lon = points[i][0] + t * (points[i+1][0] - points[i][0])
            lat = points[i][1] + t * (points[i+1][1] - points[i][1])
            return lon, lat
        accumulated += seg_len

    return points[-1]


def build_polyline(points: list[tuple[float, float]]) -> str:
    coords = ",".join(f"{lon},{lat}" for lon, lat in points)
    return f"c:FF6600FF,w:4,{coords}"


def build_markers(points: list[tuple[float, float]], mid: tuple[float, float]) -> str:
    parts = [f"{lon},{lat},pm2blm" for lon, lat in points]
    parts.append(f"{mid[0]},{mid[1]},pm2rdm")
    return "~".join(parts)


def map_center_spn(points: list[tuple[float, float]]) -> tuple[str, str]:
    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    center_lon = (min(lons) + max(lons)) / 2
    center_lat = (min(lats) + max(lats)) / 2
    spn_lon = round((max(lons) - min(lons)) * 1.3, 3)
    spn_lat = round((max(lats) - min(lats)) * 1.3, 3)
    return f"{center_lon},{center_lat}", f"{spn_lon},{spn_lat}"


def fetch_map(points: list[tuple[float, float]], mid: tuple[float, float]) -> bytes | None:
    ll, spn = map_center_spn(points)
    params = {
        "ll": ll,
        "spn": spn,
        "apikey": STATIC_API_KEY,
        "l": "map",
        "pl": build_polyline(points),
        "pt": build_markers(points, mid),
    }
    response = requests.get(STATIC_API_URL, params=params)
    if response:
        return response.content
    print(f"Ошибка карты: {response.status_code} {response.reason}")
    return None


class MapWindow(QWidget):
    def __init__(self, points, mid, total_km):
        super().__init__()
        self.map_file = MAP_FILE
        self.setWindowTitle("Длина пути")
        self._build_ui(points, mid, total_km)
        self._load_map(points, mid)

    def _build_ui(self, points, mid, total_km):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.map_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.map_label.setMinimumSize(900, 420)
        self.map_label.setStyleSheet("background: #222;")
        layout.addWidget(self.map_label)

        segments = segment_lengths(points)
        seg_text = "  |  ".join(
            f"{LABELS[i]}–{LABELS[i+1]}: {segments[i]:.0f} км"
            for i in range(len(segments))
        )
        info = QLabel(
            f"Общая длина пути: {total_km:.1f} км\n"
            f"Середина пути: {mid[0]:.4f}, {mid[1]:.4f}  (красная метка)\n"
            f"{seg_text}"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("padding: 8px; font-size: 12px;")
        layout.addWidget(info)

    def _load_map(self, points, mid):
        data = fetch_map(points, mid)
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
    sys.stdout.reconfigure(encoding="utf-8")

    lengths = segment_lengths(POINTS)
    total = sum(lengths)
    mid = middle_point(POINTS)

    print("Отрезки пути:")
    for i, km in enumerate(lengths):
        print(f"  {LABELS[i]} → {LABELS[i+1]}: {km:.1f} км")
    print(f"Общая длина: {total:.1f} км")
    print(f"Середина пути: {mid[0]:.4f}, {mid[1]:.4f}")

    app = QApplication(sys.argv)
    window = MapWindow(POINTS, mid, total)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
