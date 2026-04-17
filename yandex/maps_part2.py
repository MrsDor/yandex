import os
import sys

import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QStatusBar, QMainWindow
)

STATIC_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
STATIC_API_URL = "https://static-maps.yandex.ru/v1"
MAP_FILE = "map.png"

DEFAULT_LL = "37.617617,55.755864"
DEFAULT_SPN = 0.05

SPN_MIN = 0.001
SPN_MAX = 90.0
ZOOM_FACTOR = 1.5


def fetch_map(ll: str, spn: float) -> bytes | None:
    params = {
        "ll": ll,
        "spn": f"{spn},{spn}",
        "apikey": STATIC_API_KEY,
    }
    response = requests.get(STATIC_API_URL, params=params)
    if response:
        return response.content
    print(f"Ошибка запроса: {response.status_code} {response.reason}")
    return None


class MapWindow(QMainWindow):
    def __init__(self, ll: str = DEFAULT_LL, spn: float = DEFAULT_SPN):
        super().__init__()
        self.ll = ll
        self.spn = spn
        self.map_file = MAP_FILE
        self.setWindowTitle("Карта — Yandex Static Maps API")
        self.setMinimumSize(650, 550)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()
        self._load_map()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Координаты (lon,lat):"))
        self.ll_edit = QLineEdit(self.ll)
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

        self.map_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.map_label.setMinimumSize(600, 450)
        self.map_label.setStyleSheet("background: #222;")
        layout.addWidget(self.map_label)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def _load_map(self):
        self.status.showMessage("Загрузка карты…")
        QApplication.processEvents()

        data = fetch_map(self.ll, self.spn)
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
        self.spn_edit.setText(str(self.spn))
        self.status.showMessage(f"Центр: {self.ll}   Масштаб: {self.spn}")

    def _on_show(self):
        self.ll = self.ll_edit.text().strip()
        try:
            val = float(self.spn_edit.text().strip())
            self.spn = max(SPN_MIN, min(SPN_MAX, val))
        except ValueError:
            pass
        self._load_map()
        self.setFocus()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_PageUp:
            self.spn = max(SPN_MIN, self.spn / ZOOM_FACTOR)
            self._load_map()
        elif key == Qt.Key.Key_PageDown:
            self.spn = min(SPN_MAX, self.spn * ZOOM_FACTOR)
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
