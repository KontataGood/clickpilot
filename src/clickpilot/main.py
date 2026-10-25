
import sys

import pyautogui
from pynput import keyboard

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import load_config, save_config
from .clicker import Clicker


class MainWindow(QMainWindow):
    point_selected = Signal(int, int)
    toggle_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("ClickPilot")
        self.setMinimumWidth(420)

        self.config = load_config()
        self.selecting_point = False
        self.last_key = None

        self.clicker = Clicker()
        self.clicker.status_changed.connect(self.on_status_changed)
        self.clicker.click_performed.connect(self.on_click_performed)
        self.clicker.error_occurred.connect(self.show_error)

        self.point_selected.connect(self.on_point_selected)
        self.toggle_requested.connect(self.toggle_clicking)

        self.build_ui()
        self.load_settings_into_ui()
        self.update_status(self.clicker.is_running)

        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_global_key_press,
            on_release=self.on_global_key_release,
        )
        self.keyboard_listener.start()

    def build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        title = QLabel("ClickPilot")
        title.setStyleSheet("font-size: 26px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Автоматические клики с сохранением настроек"
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.point_label = QLabel("Точка клика: не выбрана")
        self.point_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.select_button = QPushButton("Выбрать точку (F5)")
        self.select_button.clicked.connect(self.begin_point_selection)

        layout.addWidget(self.point_label)
        layout.addWidget(self.select_button)

        form = QFormLayout()

        self.interval_input = QDoubleSpinBox()
        self.interval_input.setRange(0.1, 3600)
        self.interval_input.setSingleStep(0.5)
        self.interval_input.setSuffix(" сек.")
        form.addRow("Интервал:", self.interval_input)

        self.click_type_input = QComboBox()
        self.click_type_input.addItem("Левый клик", "left")
        self.click_type_input.addItem("Правый клик", "right")
        self.click_type_input.addItem("Двойной клик", "double")
        form.addRow("Тип клика:", self.click_type_input)

        layout.addLayout(form)

        self.interval_input.valueChanged.connect(self.save_settings)
        self.click_type_input.currentIndexChanged.connect(
            self.save_settings
        )

        self.status_label = QLabel()
        self.counter_label = QLabel("Выполнено кликов: 0")
        self.click_count = 0

        layout.addWidget(self.status_label)
        layout.addWidget(self.counter_label)

        buttons = QHBoxLayout()

        self.start_button = QPushButton("Старт (F6)")
        self.start_button.clicked.connect(self.start_clicking)

        self.stop_button = QPushButton("Стоп (F6)")
        self.stop_button.clicked.connect(self.stop_clicking)

        buttons.addWidget(self.start_button)
        buttons.addWidget(self.stop_button)
        layout.addLayout(buttons)

        hint = QLabel(
            "F5 — выбрать точку после наведения мыши.\n"
            "F6 — запустить или остановить макрос.\n"
            "Настройки сохраняются автоматически."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.setCentralWidget(root)

    def load_settings_into_ui(self) -> None:
        x = self.config.get("x")
        y = self.config.get("y")

        if isinstance(x, int) and isinstance(y, int):
            self.point_label.setText(
                f"Точка клика: X={x}, Y={y}"
            )

        interval = self.config.get("interval", 5.0)
        try:
            self.interval_input.setValue(float(interval))
        except (TypeError, ValueError):
            self.interval_input.setValue(5.0)

        click_type = self.config.get("click_type", "left")
        index = self.click_type_input.findData(click_type)
        self.click_type_input.setCurrentIndex(
            index if index >= 0 else 0
        )

        self.apply_clicker_config()

    def save_settings(self, *_args) -> None:
        self.config["interval"] = self.interval_input.value()
        self.config["click_type"] = (
            self.click_type_input.currentData()
        )

        save_config(self.config)
        self.apply_clicker_config()

    def apply_clicker_config(self) -> None:
        self.clicker.configure(
            x=self.config.get("x"),
            y=self.config.get("y"),
            interval=float(self.config.get("interval", 5.0)),
            click_type=self.config.get("click_type", "left"),
        )

    @Slot()
    def begin_point_selection(self) -> None:
        self.selecting_point = True
        self.point_label.setText(
            "Наведи мышь на нужное место и нажми F5"
        )
        self.select_button.setText("Ожидание F5...")
        self.activateWindow()

    def on_global_key_press(self, key) -> None:
        if key == self.last_key:
            return

        self.last_key = key

        if key == keyboard.Key.f5 and self.selecting_point:
            x, y = pyautogui.position()
            self.point_selected.emit(x, y)

        elif key == keyboard.Key.f6:
            self.toggle_requested.emit()

    def on_global_key_release(self, key) -> None:
        if key == self.last_key:
            self.last_key = None

    @Slot(int, int)
    def on_point_selected(self, x: int, y: int) -> None:
        self.selecting_point = False
        self.config["x"] = x
        self.config["y"] = y

        self.point_label.setText(
            f"Точка клика: X={x}, Y={y}"
        )
        self.select_button.setText("Выбрать другую точку (F5)")

        self.save_settings()
        self.update_status(self.clicker.is_running)

    @Slot()
    def toggle_clicking(self) -> None:
        if self.clicker.is_running:
            self.stop_clicking()
        else:
            self.start_clicking()

    @Slot()
    def start_clicking(self) -> None:
        self.save_settings()
        self.clicker.start()

    @Slot()
    def stop_clicking(self) -> None:
        self.clicker.stop()

    @Slot(bool)
    def on_status_changed(self, running: bool) -> None:
        self.update_status(running)

    def update_status(self, running: bool) -> None:
        if running:
            self.status_label.setText("Статус: работает")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Статус: остановлен")
            self.status_label.setStyleSheet("color: gray;")

        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)

    @Slot()
    def on_click_performed(self) -> None:
        self.click_count += 1
        self.counter_label.setText(
            f"Выполнено кликов: {self.click_count}"
        )

    @Slot(str)
    def show_error(self, message: str) -> None:
        QMessageBox.warning(self, "ClickPilot", message)
        self.update_status(self.clicker.is_running)

    def closeEvent(self, event) -> None:
        self.clicker.stop()
        self.keyboard_listener.stop()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
