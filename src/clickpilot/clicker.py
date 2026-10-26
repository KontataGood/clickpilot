
import pyautogui

from PySide6.QtCore import QObject, QTimer, Signal, Slot


class Clicker(QObject):
    """Управляет повторяющимися кликами мыши."""

    status_changed = Signal(bool)
    click_performed = Signal()
    error_occurred = Signal(str)

    MIN_INTERVAL_MS = 1
    MAX_INTERVAL_MS = 86_400_000  # 24 часа

    def __init__(self) -> None:
        super().__init__()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._click)

        self._x: int | None = None
        self._y: int | None = None
        self._interval_ms = 5000
        self._click_type = "left"
        self._running = False

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def interval_ms(self) -> int:
        return self._interval_ms

    @staticmethod
    def to_milliseconds(value: float, unit: str) -> int:
        """Преобразует интервал в миллисекунды."""
        multipliers = {
            "ms": 1,
            "s": 1000,
            "min": 60_000,
        }

        if unit not in multipliers:
            raise ValueError(
                "Единица интервала должна быть ms, s или min."
            )

        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Интервал должен быть числом.") from exc

        if not 0 < numeric_value < float("inf"):
            raise ValueError("Интервал должен быть положительным числом.")

        interval_ms = round(numeric_value * multipliers[unit])

        if not (
            Clicker.MIN_INTERVAL_MS
            <= interval_ms
            <= Clicker.MAX_INTERVAL_MS
        ):
            raise ValueError(
                "Интервал должен быть от 1 мс до 24 часов."
            )

        return interval_ms

    def configure(
        self,
        x: int | None,
        y: int | None,
        interval: float,
        click_type: str,
        unit: str = "s",
    ) -> None:
        if self._running:
            self.stop()

        interval_ms = self.to_milliseconds(interval, unit)

        self._x = x
        self._y = y
        self._interval_ms = interval_ms
        self._click_type = click_type

        self._timer.setInterval(self._interval_ms)

    @Slot()
    def start(self) -> None:
        if self._x is None or self._y is None:
            self.error_occurred.emit("Сначала выбери точку клика.")
            return

        if self._running:
            return

        self._running = True
        self._timer.start(self._interval_ms)
        self.status_changed.emit(True)

    @Slot()
    def stop(self) -> None:
        if not self._running:
            return

        self._timer.stop()
        self._running = False
        self.status_changed.emit(False)

    @Slot()
    def _click(self) -> None:
        if not self._running:
            return

        try:
            if self._click_type == "double":
                pyautogui.doubleClick(x=self._x, y=self._y)
            else:
                pyautogui.click(
                    x=self._x,
                    y=self._y,
                    button=self._click_type,
                )

            self.click_performed.emit()

        except Exception as exc:
            self.stop()
            self.error_occurred.emit(f"Клики остановлены: {exc}")
