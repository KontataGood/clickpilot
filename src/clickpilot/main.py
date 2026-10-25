
import sys
from datetime import datetime

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
    QPlainTextEdit,
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
        self.setMinimumSize(540, 620)

        self.config = load_config()
        self.selecting_point = False
        self.last_key = None
        self.click_count = 0

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

        self.log_event("Приложение запущено")
        self.log_event("Настройки загружены")

    def build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("ClickPilot")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel(
            "Автоматические клики мышью с сохранением настроек"
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addWidget(self.make_section_title("ТОЧКА КЛИКА"))

        self.point_label = QLabel("Точка не выбрана")
        self.point_label.setObjectName("pointLabel")
        self.point_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.point_label)

        self.select_button = QPushButton("Выбрать точку  ·  F5")
        self.select_button.clicked.connect(self.begin_point_selection)
        layout.addWidget(self.select_button)

        layout.addWidget(self.make_section_title("ПАРАМЕТРЫ"))

        form = QFormLayout()
        form.setSpacing(12)

        self.interval_input = QDoubleSpinBox()
        self.interval_input.setRange(0.1, 3600)
        self.interval_input.setSingleStep(0.5)
        self.interval_input.setDecimals(1)
        self.interval_input.setSuffix(" сек.")
        form.addRow("Интервал между кликами", self.interval_input)

        self.click_type_input = QComboBox()
        self.click_type_input.addItem("Левый клик", "left")
        self.click_type_input.addItem("Правый клик", "right")
        self.click_type_input.addItem("Двойной клик", "double")
        form.addRow("Тип действия", self.click_type_input)

        layout.addLayout(form)

        self.interval_input.valueChanged.connect(self.save_settings)
        self.click_type_input.currentIndexChanged.connect(
            self.save_settings
        )

        layout.addWidget(self.make_section_title("УПРАВЛЕНИЕ"))

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self.start_button = QPushButton("▶  Старт")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_clicking)

        self.stop_button = QPushButton("■  Стоп")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_clicking)

        buttons.addWidget(self.start_button)
        buttons.addWidget(self.stop_button)
        layout.addLayout(buttons)

        stats = QHBoxLayout()

        self.counter_label = QLabel("Кликов: 0")
        self.last_click_label = QLabel("Последний клик: —")

        stats.addWidget(self.counter_label)
        stats.addStretch()
        stats.addWidget(self.last_click_label)
        layout.addLayout(stats)

        layout.addWidget(self.make_section_title("ЖУРНАЛ РАБОТЫ"))

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(200)
        self.log_view.setPlaceholderText("События появятся здесь...")
        self.log_view.setMinimumHeight(130)
        layout.addWidget(self.log_view)

        hint = QLabel(
            "F5 — сохранить позицию курсора во время выбора точки.\n"
            "F6 — запустить или остановить макрос."
        )
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #15171c;
                color: #e8eaf0;
                font-size: 13px;
            }
            QLabel#title {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
            QLabel#subtitle, QLabel#hint {
                color: #969cab;
            }
            QLabel#pointLabel, QLabel#statusLabel {
                background-color: #20232b;
                border: 1px solid #303440;
                border-radius: 8px;
                padding: 11px;
            }
            QLabel#sectionTitle {
                color: #8f9cff;
                font-size: 11px;
                font-weight: 700;
                padding-top: 5px;
            }
            QComboBox, QDoubleSpinBox {
                background-color: #20232b;
                border: 1px solid #363b49;
                border-radius: 7px;
                padding: 8px;
                min-width: 110px;
            }
            QPushButton {
                background-color: #292d37;
                border: 1px solid #3a4050;
                border-radius: 8px;
                padding: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #363c49;
            }
            QPushButton:disabled {
                color: #6e7380;
                background-color: #20232b;
            }
            QPushButton#startButton {
                background-color: #5668e8;
                border: none;
                color: white;
            }
            QPushButton#startButton:hover {
                background-color: #6879f4;
            }
            QPushButton#stopButton {
                background-color: #342329;
                color: #ff929c;
                border: 1px solid #5b303b;
            }
            QPlainTextEdit#logView {
                background-color: #101216;
                border: 1px solid #303440;
                border-radius: 8px;
                padding: 8px;
                color: #b9c1d2;
                font-family: Consolas;
                font-size: 12px;
            }
        """)

    def make_section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def load_settings_into_ui(self) -> None:
        x = self.config.get("x")
        y = self.config.get("y")

        if (
            isinstance(x, int)
            and not isinstance(x, bool)
            and isinstance(y, int)
            and not isinstance(y, bool)
        ):
            self.point_label.setText(f"X = {x}    ·    Y = {y}")

        interval = self.config.get("interval", 5.0)
        try:
            self.interval_input.setValue(float(interval))
        except (TypeError, ValueError):
            self.interval_input.setValue(5.0)

        click_type = self.config.get("click_type", "left")
        index = self.click_type_input.findData(click_type)
        self.click_type_input.setCurrentIndex(index if index >= 0 else 0)

        self.apply_clicker_config()

    def save_settings(self, *_args) -> None:
        self.config["interval"] = self.interval_input.value()
        self.config["click_type"] = self.click_type_input.currentData()

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
        if self.clicker.is_running:
            self.log_event("Сначала останови макрос для смены точки")
            return

        self.selecting_point = True
        self.point_label.setText("Наведи курсор и нажми F5")
        self.select_button.setText("Ожидание F5...")
        self.log_event("Ожидание выбора точки")
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

        self.point_label.setText(f"X = {x}    ·    Y = {y}")
        self.select_button.setText("Выбрать другую точку  ·  F5")

        self.save_settings()
        self.log_event(f"Точка сохранена: X={x}, Y={y}")

    @Slot()
    def toggle_clicking(self) -> None:
        if self.clicker.is_running:
            self.stop_clicking()
        else:
            self.start_clicking()

    @Slot()
    def start_clicking(self) -> None:
        self.save_settings()
        was_running = self.clicker.is_running
        self.clicker.start()

        if not was_running and self.clicker.is_running:
            self.log_event("Макрос запущен")

    @Slot()
    def stop_clicking(self) -> None:
        was_running = self.clicker.is_running
        self.clicker.stop()

        if was_running:
            self.log_event("Макрос остановлен")

    @Slot(bool)
    def on_status_changed(self, running: bool) -> None:
        self.update_status(running)

    def update_status(self, running: bool) -> None:
        if running:
            self.status_label.setText("●  Работает")
            self.status_label.setStyleSheet(
                "color: #7ee0a1; background-color: #1b2c25;"
            )
        else:
            self.status_label.setText("●  Остановлен")
            self.status_label.setStyleSheet(
                "color: #a4a9b5; background-color: #20232b;"
            )

        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)

    @Slot()
    def on_click_performed(self) -> None:
        self.click_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.counter_label.setText(f"Кликов: {self.click_count}")
        self.last_click_label.setText(f"Последний клик: {timestamp}")
        self.log_event(f"Клик №{self.click_count} · {timestamp}")

    def log_event(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{timestamp}] {message}")

    @Slot(str)
    def show_error(self, message: str) -> None:
        self.log_event(f"Ошибка: {message}")
        QMessageBox.warning(self, "ClickPilot", message)
        self.update_status(self.clicker.is_running)

    def closeEvent(self, event) -> None:
        self.clicker.stop()
        self.keyboard_listener.stop()
        self.log_event("Приложение закрывается")
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
