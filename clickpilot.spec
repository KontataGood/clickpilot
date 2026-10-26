
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

a = Analysis(
    ["run_clickpilot.py"],
    pathex=["src"],
    binaries=[],
    datas=[("assets/clickpilot.ico", "assets")],
    hiddenimports=[],
    hookspath=["hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtPdf",
        "PySide6.QtVirtualKeyboard",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
    ],
    noarchive=False,
)

# Удаляем только ненужные плагины из списка бинарных зависимостей.
unneeded_plugins = (
    "qtvirtualkeyboardplugin.dll",
    "qpdf.dll",
    "qtiff.dll",
    "qdirect2d.dll",
    "qoffscreen.dll",
    "qminimal.dll",
    "qtuiotouchplugin.dll",
    "qsvgicon.dll",
)

a.binaries = [
    entry for entry in a.binaries
    if not any(entry[0].lower().endswith(name.lower())
               for name in unneeded_plugins)
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ClickPilot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/clickpilot.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="ClickPilot",
)
