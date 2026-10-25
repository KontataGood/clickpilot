
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

excluded_plugins = {
    "qpdf.dll",
    "qtiff.dll",
    "qgif.dll",
    "qicns.dll",
    "qtga.dll",
    "qwbmp.dll",
    "qwebp.dll",
    "qsvg.dll",
    "qtvirtualkeyboardplugin.dll",
    "qtuiotouchplugin.dll",
    "qdirect2d.dll",
    "qoffscreen.dll",
    "qminimal.dll",
    "qsvgicon.dll",
}

binaries = [
    item
    for item in binaries
    if item[0].replace("/", "\\").split("\\")[-1].lower()
    not in excluded_plugins
]
