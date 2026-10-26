
import sys
from datetime import datetime

import pyautogui
from pynput import keyboard

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
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
    QFileDialog,
    QMenu,
    QStyle,
    QSystemTrayIcon,
    QInputDialog,
)

from .config import (
    load_config,
    save_config,
    save_profile,
    activate_profile,
    delete_profile,
)
from .clicker import Clicker
from .activity_log import ActivityLogger


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

        self.activity_logger = ActivityLogger()

        self.build_ui()
        self._allow_exit = False
        self.setup_tray()
        self.load_settings_into_ui()
        self.update_status(self.clicker.is_running)

        for entry in self.activity_logger.read_recent():
            self.log_view.appendPlainText(entry)

        self.log_event("Приложение запущено")
        self.log_event("Настройки загружены")

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

        layout.addWidget(self.make_section_title("ПРОФИЛЬ НАСТРОЕК"))

        profile_row = QHBoxLayout()

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(160)
        self.profile_combo.currentTextChanged.connect(
            self.on_profile_changed
        )
        profile_row.addWidget(self.profile_combo, 1)

        self.create_profile_button = QPushButton("Создать")
        self.create_profile_button.clicked.connect(
            self.create_profile
        )
        profile_row.addWidget(self.create_profile_button)

        self.rename_profile_button = QPushButton("Переименовать")
        self.rename_profile_button.clicked.connect(
            self.rename_profile
        )
        profile_row.addWidget(self.rename_profile_button)

        self.delete_profile_button = QPushButton("Удалить")
        self.delete_profile_button.clicked.connect(
            self.remove_profile
        )
        profile_row.addWidget(self.delete_profile_button)

        layout.addLayout(profile_row)


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
        self.interval_input.setRange(1, 86_400_000)
        self.interval_input.setSingleStep(100)
        self.interval_input.setDecimals(3)
        self.interval_input.setValue(5.0)

        self.interval_unit_input = QComboBox()
        self.interval_unit_input.addItem("Миллисекунды", "ms")
        self.interval_unit_input.addItem("Секунды", "s")
        self.interval_unit_input.addItem("Минуты", "min")

        interval_row = QHBoxLayout()
        interval_row.addWidget(self.interval_input, 2)
        interval_row.addWidget(self.interval_unit_input, 1)
        form.addRow("Интервал между кликами", interval_row)


        self.click_type_input = QComboBox()
        self.click_type_input.addItem("Левый клик", "left")
        self.click_type_input.addItem("Правый клик", "right")
        self.click_type_input.addItem("Двойной клик", "double")
        form.addRow("Тип действия", self.click_type_input)

        layout.addLayout(form)

        self.interval_input.valueChanged.connect(self.save_settings)
        self.interval_unit_input.currentIndexChanged.connect(
            self.save_settings
        )
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

        log_buttons = QHBoxLayout()

        self.export_log_button = QPushButton("Экспорт журнала")
        self.export_log_button.clicked.connect(self.export_log)

        self.clear_log_button = QPushButton("Очистить журнал")
        self.clear_log_button.clicked.connect(self.clear_log)

        log_buttons.addWidget(self.export_log_button)
        log_buttons.addWidget(self.clear_log_button)
        layout.addLayout(log_buttons)


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
        profiles = self.config.get("profiles", {})
        active = self.config.get("active_profile", "По умолчанию")

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(list(profiles.keys()))

        index = self.profile_combo.findText(active)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
        self.profile_combo.blockSignals(False)

        self.delete_profile_button.setEnabled(len(profiles) > 1)

        x = self.config.get("x")
        y = self.config.get("y")

        if (
            isinstance(x, int)
            and not isinstance(x, bool)
            and isinstance(y, int)
            and not isinstance(y, bool)
        ):
            self.point_label.setText(f"X = {x}    ·    Y = {y}")
        else:
            self.point_label.setText("Точка не выбрана")

        self.interval_input.blockSignals(True)
        self.click_type_input.blockSignals(True)

        try:
            self.interval_input.setValue(
                float(self.config.get("interval", 5.0))
            )
        except (TypeError, ValueError):
            self.interval_input.setValue(5.0)

        click_type = self.config.get("click_type", "left")
        index = self.click_type_input.findData(click_type)
        self.click_type_input.setCurrentIndex(index if index >= 0 else 0)

        self.interval_input.blockSignals(False)
        interval_unit = self.config.get("interval_unit", "s")
        unit_index = self.interval_unit_input.findData(interval_unit)
        self.interval_unit_input.setCurrentIndex(
            unit_index if unit_index >= 0 else 1
        )

        self.interval_unit_input.blockSignals(False)
        self.click_type_input.blockSignals(False)

        self.apply_clicker_config()

    def save_settings(self, *_args) -> None:
        self.config["interval"] = self.interval_input.value()
        self.config["click_type"] = self.click_type_input.currentData()

        profile_name = self.config.get(
            "active_profile", "По умолчанию"
        )
        self.config = save_profile(self.config, profile_name)

        save_config(self.config)
        self.delete_profile_button.setEnabled(
            len(self.config.get("profiles", {})) > 1
        )

        self.config["interval"] = self.interval_input.value()
        self.config["interval_unit"] = self.interval_unit_input.currentData()
        self.config["click_type"] = self.click_type_input.currentData()

        self.apply_clicker_config()


    @Slot(str)
    def on_profile_changed(self, profile_name: str) -> None:
        if not profile_name:
            return

        if profile_name == self.config.get("active_profile"):
            return

        if self.clicker.is_running:
            self.profile_combo.blockSignals(True)
            self.profile_combo.setCurrentText(
                self.config["active_profile"]
            )
            self.profile_combo.blockSignals(False)

            QMessageBox.information(
                self,
                "ClickPilot",
                "Останови автокликер перед переключением профиля.",
            )
            return

        try:
            self.config = activate_profile(self.config, profile_name)
            save_config(self.config)
            self.load_settings_into_ui()
            self.log_event(f"Активирован профиль: {profile_name}")
        except ValueError as exc:
            QMessageBox.warning(self, "ClickPilot", str(exc))
            self.load_settings_into_ui()

    @Slot()
    def create_profile(self) -> None:
        name, accepted = QInputDialog.getText(
            self,
            "Новый профиль",
            "Название профиля:",
        )

        if not accepted:
            return

        name = name.strip()
        if not name:
            QMessageBox.warning(
                self, "ClickPilot", "Название не может быть пустым."
            )
            return

        if name in self.config.get("profiles", {}):
            QMessageBox.warning(
                self, "ClickPilot", "Профиль с таким названием уже существует."
            )
            return

        if self.clicker.is_running:
            QMessageBox.information(
                self,
                "ClickPilot",
                "Останови автокликер перед созданием профиля.",
            )
            return

        self.config = save_profile(self.config, name)
        save_config(self.config)
        self.load_settings_into_ui()
        self.log_event(f"Создан профиль: {name}")

    @Slot()
    def rename_profile(self) -> None:
        old_name = self.config.get("active_profile", "По умолчанию")

        if self.clicker.is_running:
            QMessageBox.information(
                self,
                "ClickPilot",
                "Останови автокликер перед переименованием профиля.",
            )
            return

        new_name, accepted = QInputDialog.getText(
            self,
            "Переименовать профиль",
            "Новое название:",
            text=old_name,
        )

        if not accepted:
            return

        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(
                self, "ClickPilot", "Название не может быть пустым."
            )
            return

        if new_name != old_name and new_name in self.config["profiles"]:
            QMessageBox.warning(
                self, "ClickPilot", "Профиль с таким названием уже существует."
            )
            return

        if new_name == old_name:
            return

        self.config["profiles"][new_name] = (
            self.config["profiles"].pop(old_name)
        )
        self.config["active_profile"] = new_name

        save_config(self.config)
        self.load_settings_into_ui()
        self.log_event(f"Профиль переименован: {old_name} → {new_name}")

    @Slot()
    def remove_profile(self) -> None:
        name = self.config.get("active_profile", "По умолчанию")

        if self.clicker.is_running:
            QMessageBox.information(
                self,
                "ClickPilot",
                "Останови автокликер перед удалением профиля.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Удалить профиль",
            f"Удалить профиль «{name}»?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.config = delete_profile(self.config, name)
            save_config(self.config)
            self.load_settings_into_ui()
            self.log_event(f"Удалён профиль: {name}")
        except ValueError as exc:
            QMessageBox.warning(self, "ClickPilot", str(exc))


    def apply_clicker_config(self) -> None:
        self.clicker.configure(
            x=self.config.get("x"),
            y=self.config.get("y"),
            interval=float(self.config.get("interval", 5.0)),
            click_type=self.config.get("click_type", "left"),
            unit=self.config.get("interval_unit", "s"),
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
        self.update_tray_actions(running)

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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{timestamp} | {message}"

        self.activity_logger.log(message)
        self.log_view.appendPlainText(entry)

    @Slot(str)
    def show_error(self, message: str) -> None:
        self.log_event(f"Ошибка: {message}")
        QMessageBox.warning(self, "ClickPilot", message)
        self.update_status(self.clicker.is_running)

    def closeEvent(self, event) -> None:
        if not self._allow_exit and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.log_event("Окно скрыто в системный трей")
            return

        self.clicker.stop()
        self.keyboard_listener.stop()
        self.tray_icon.hide()
        self.log_event("Приложение закрывается")
        event.accept()


    @Slot()
    def export_log(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт журнала",
            "clickpilot-activity.txt",
            "Текстовые файлы (*.txt)",
        )

        if not destination:
            return

        try:
            self.activity_logger.export_log(destination)
            QMessageBox.information(
                self,
                "ClickPilot",
                "Журнал успешно экспортирован.",
            )
        except OSError as exc:
            self.show_error(f"Не удалось экспортировать журнал: {exc}")

    @Slot()
    def clear_log(self) -> None:
        answer = QMessageBox.question(
            self,
            "Очистить журнал",
            "Удалить сохранённую историю действий?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.activity_logger.clear_log()
            self.log_view.clear()
            self.log_event("Журнал очищен")
        except OSError as exc:
            self.show_error(f"Не удалось очистить журнал: {exc}")


    def setup_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)

        icon = QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )
        self.setWindowIcon(icon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("ClickPilot")

        menu = QMenu(self)

        self.show_action = QAction("Открыть ClickPilot", self)
        self.show_action.triggered.connect(self.show_window)
        menu.addAction(self.show_action)

        menu.addSeparator()

        self.tray_start_action = QAction("Запустить", self)
        self.tray_start_action.triggered.connect(self.start_clicking)
        menu.addAction(self.tray_start_action)

        self.tray_stop_action = QAction("Остановить", self)
        self.tray_stop_action.triggered.connect(self.stop_clicking)
        menu.addAction(self.tray_stop_action)

        menu.addSeparator()

        self.quit_action = QAction("Выход", self)
        self.quit_action.triggered.connect(self.quit_application)
        menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        self.update_tray_actions(self.clicker.is_running)

    @Slot()
    def show_window(self) -> None:
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    @Slot()
    def quit_application(self) -> None:
        self._allow_exit = True
        self.tray_icon.hide()
        self.clicker.stop()
        self.keyboard_listener.stop()
        QApplication.instance().quit()

    @Slot(QSystemTrayIcon.ActivationReason)
    def on_tray_activated(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def update_tray_actions(self, running: bool) -> None:
        self.tray_start_action.setEnabled(not running)
        self.tray_stop_action.setEnabled(running)




def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
