
"""Fluent Design-inspired theme for ClickPilot."""

COLORS = {
    "background": "#1C1C1C",
    "surface": "#252526",
    "surface_hover": "#303033",
    "surface_pressed": "#3A3A3D",
    "border": "#3B3B3B",
    "text": "#F5F5F5",
    "text_secondary": "#A0A0A0",
    "accent": "#60CDFF",
    "accent_hover": "#82D9FF",
    "accent_pressed": "#39B8F2",
    "success": "#6CCB5F",
    "danger": "#F1707B",
    "disabled": "#666666",
}

APP_STYLE = f"""
QMainWindow {{
    background-color: {COLORS["background"]};
    color: {COLORS["text"]};
}}

QWidget {{
    color: {COLORS["text"]};
    font-family: "Segoe UI";
    font-size: 13px;
}}

QLabel#title {{
    font-size: 28px;
    font-weight: 600;
    color: {COLORS["text"]};
}}

QLabel#subtitle,
QLabel#hint {{
    color: {COLORS["text_secondary"]};
}}

QLabel#sectionTitle {{
    color: {COLORS["accent"]};
    font-size: 11px;
    font-weight: 700;
    padding-top: 5px;
}}

QLabel#pointLabel,
QLabel#statusLabel {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 11px;
}}

QComboBox,
QDoubleSpinBox {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px;
    min-height: 20px;
    selection-background-color: {COLORS["accent"]};
}}

QComboBox:hover,
QDoubleSpinBox:hover {{
    border-color: {COLORS["accent"]};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["surface"]};
    selection-background-color: #344B5A;
    border: 1px solid {COLORS["border"]};
    outline: none;
}}

QPushButton {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 9px 14px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLORS["surface_hover"]};
    border-color: #555555;
}}

QPushButton:pressed {{
    background-color: {COLORS["surface_pressed"]};
}}

QPushButton:disabled {{
    color: {COLORS["disabled"]};
    background-color: {COLORS["surface"]};
    border-color: {COLORS["border"]};
}}

QPushButton#startButton {{
    background-color: {COLORS["accent"]};
    color: #111111;
    border: none;
    font-weight: 600;
}}

QPushButton#startButton:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton#startButton:pressed {{
    background-color: {COLORS["accent_pressed"]};
}}

QPushButton#stopButton {{
    background-color: #3A2528;
    color: {COLORS["danger"]};
    border: 1px solid #654047;
}}

QPlainTextEdit#logView {{
    background-color: #181818;
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px;
    color: #D4D4D4;
    font-family: Consolas;
    font-size: 12px;
}}

QScrollArea {{
    border: none;
    background-color: {COLORS["background"]};
}}

QScrollBar:vertical {{
    background-color: {COLORS["background"]};
    width: 10px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background-color: #555555;
    border-radius: 4px;
    min-height: 25px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #777777;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QFrame#sidebar {{
    background-color: #202020;
    border: 1px solid #353535;
    border-radius: 10px;
}}

QLabel#brand {{
    font-size: 21px;
    font-weight: 600;
    padding: 8px;
}}

QPushButton#navButton {{
    text-align: left;
    padding: 11px 12px;
    border: 1px solid transparent;
    border-radius: 6px;
    background-color: transparent;
    font-weight: 400;
}}

QPushButton#navButton:hover {{
    background-color: #303030;
}}

QPushButton#navButton:checked {{
    background-color: #293C48;
    border: 1px solid #38566A;
    color: #60CDFF;
    font-weight: 600;
}}
"""
