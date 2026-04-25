import os
import sys

import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QStatusBar, QMainWindow,
    QCheckBox, QComboBox
)


STATIC_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
STATIC_API_URL = "https://static-maps.yandex.ru/v1"

GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"
GEOCODER_API_URL = "https://geocode-maps.yandex.ru/1.x/"

MAP_FILE = "map.png"

DEFAULT_LL = "37.617617,55.755864"
DEFAULT_SPN = 0.05

SPN_MIN = 0.001
SPN_MAX = 90.0
ZOOM_FACTOR = 1.5

LON_MIN = -180.0
LON_MAX = 180.0
LAT_MIN = -85.0
LAT_MAX = 85.0

THEME_LIGHT = "light"
THEME_DARK = "dark"


MAP_TYPES: list[tuple[str, str]] = [
    ("Схема", "map"),
    ("Навигация", "roadmap"),
    ("Спутник", "satellite"),
    ("Гибрид", "hybrid"),
]


def geocode(query: str) -> tuple[float, float] | None:
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
    data = response.json()
    try:
        members = data["response"]["GeoObjectCollection"]["featureMember"]
        if not members:
            return None
        pos = members[0]["GeoObject"]["Point"]["pos"]
        lon, lat = map(float, pos.split())
        return lon, lat
    except (KeyError, IndexError, ValueError):
        return None


def fetch_map(
    ll: str,
    spn: float,
    theme: str = THEME_LIGHT,
    map_type: str = "map",
    pt: str | None = None,
) -> bytes | None:
    params = {
        "ll": ll,
        "spn": f"{spn},{spn}",
        "apikey": STATIC_API_KEY,
        "theme": theme,
        "type": map_type,
    }
    if pt:
        params["pt"] = pt
    response = requests.get(STATIC_API_URL, params=params)
    if response:
        return response.content
    print(f"Ошибка запроса: {response.status_code} {response.reason}")
    return None


class MapWindow(QMainWindow):
    def __init__(self, ll: str = DEFAULT_LL, spn: float = DEFAULT_SPN):
        super().__init__()
        lon, lat = map(float, ll.split(","))
        self.lon = lon
        self.lat = lat
        self.spn = spn
        self.theme = THEME_LIGHT
        self.map_type = MAP_TYPES[0][1]
        self.marker: tuple[float, float] | None = None  # сохраняется при любых изменениях
        self.map_file = MAP_FILE
        self.setWindowTitle("Карта — Yandex Static Maps API")
        self.setMinimumSize(650, 620)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()
        self._load_map()

    def _ll_str(self) -> str:
        return f"{self.lon},{self.lat}"

    def _pt_str(self) -> str | None:
        if self.marker is None:
            return None
        return f"{self.marker[0]},{self.marker[1]},pm2rdm"

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите адрес или название объекта…")
        self.search_edit.returnPressed.connect(self._on_search)
        search_row.addWidget(self.search_edit)
        search_btn = QPushButton("Искать")
        search_btn.clicked.connect(self._on_search)
        search_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)


        controls = QHBoxLayout()
        controls.addWidget(QLabel("Координаты (lon,lat):"))
        self.ll_edit = QLineEdit(self._ll_str())
        self.ll_edit.setPlaceholderText("37.617617,55.755864")
        controls.addWidget(self.ll_edit)

        controls.addWidget(QLabel("Масштаб (spn):"))
        self.spn_edit = QLineEdit(str(self.spn))
        self.spn_edit.setPlaceholderText("0.05")
        controls.addWidget(self.spn_edit)

        btn = QPushButton("Показать")
        btn.clicked.connect(self._on_show)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        controls.addWidget(btn)
        layout.addLayout(controls)

        view_row = QHBoxLayout()

        self.theme_checkbox = QCheckBox("Тёмная тема")
        self.theme_checkbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.theme_checkbox.stateChanged.connect(self._on_theme_changed)
        view_row.addWidget(self.theme_checkbox)

        view_row.addWidget(QLabel("Вид карты:"))
        self.type_combo = QComboBox()
        self.type_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for label, _ in MAP_TYPES:
            self.type_combo.addItem(label)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        view_row.addWidget(self.type_combo)

        view_row.addStretch()
        layout.addLayout(view_row)

        self.map_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.map_label.setMinimumSize(600, 450)
        self.map_label.setStyleSheet("background: #222;")
        layout.addWidget(self.map_label)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def _load_map(self):
        self.status.showMessage("Загрузка карты…")
        QApplication.processEvents()

        data = fetch_map(self._ll_str(), self.spn, self.theme, self.map_type, self._pt_str())
        if data is None:
            self.status.showMessage("Ошибка: не удалось получить карту.")
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
        self.ll_edit.setText(self._ll_str())
        self.spn_edit.setText(str(self.spn))
        theme_label = "тёмная" if self.theme == THEME_DARK else "светлая"
        type_label = MAP_TYPES[self.type_combo.currentIndex()][0]
        marker_info = f"   Метка: {self.marker[0]:.5f},{self.marker[1]:.5f}" if self.marker else ""
        self.status.showMessage(
            f"Центр: {self._ll_str()}   Масштаб: {self.spn}   "
            f"Тема: {theme_label}   Вид: {type_label}{marker_info}"
        )

    def _on_search(self):
        query = self.search_edit.text().strip()
        if not query:
            return
        self.status.showMessage(f"Поиск: «{query}»…")
        QApplication.processEvents()

        coords = geocode(query)
        if coords is None:
            self.status.showMessage(f"Объект «{query}» не найден.")
            return

        self.lon, self.lat = coords
        self.marker = coords
        self._load_map()
        self.setFocus()

    def _on_theme_changed(self, state: int):
        self.theme = THEME_DARK if state == Qt.CheckState.Checked.value else THEME_LIGHT
        self._load_map()
        self.setFocus()

    def _on_type_changed(self, index: int):
        self.map_type = MAP_TYPES[index][1]
        self._load_map()
        self.setFocus()

    def _on_show(self):
        try:
            lon, lat = map(float, self.ll_edit.text().strip().split(","))
            self.lon = max(LON_MIN, min(LON_MAX, lon))
            self.lat = max(LAT_MIN, min(LAT_MAX, lat))
        except ValueError:
            pass
        try:
            val = float(self.spn_edit.text().strip())
            self.spn = max(SPN_MIN, min(SPN_MAX, val))
        except ValueError:
            pass
        self._load_map()
        self.setFocus()

    def keyPressEvent(self, event):
        key = event.key()
        step = self.spn
        if key == Qt.Key.Key_PageUp:
            self.spn = max(SPN_MIN, self.spn / ZOOM_FACTOR)
            self._load_map()
        elif key == Qt.Key.Key_PageDown:
            self.spn = min(SPN_MAX, self.spn * ZOOM_FACTOR)
            self._load_map()
        elif key == Qt.Key.Key_Up:
            self.lat = min(LAT_MAX, self.lat + step)
            self._load_map()
        elif key == Qt.Key.Key_Down:
            self.lat = max(LAT_MIN, self.lat - step)
            self._load_map()
        elif key == Qt.Key.Key_Right:
            self.lon = min(LON_MAX, self.lon + step)
            self._load_map()
        elif key == Qt.Key.Key_Left:
            self.lon = max(LON_MIN, self.lon - step)
            self._load_map()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if os.path.exists(self.map_file):
            os.remove(self.map_file)
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MapWindow(ll=DEFAULT_LL, spn=DEFAULT_SPN)
    window.show()
    window.setFocus()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
