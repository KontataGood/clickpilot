def hotkeys_conflict(
    point_hotkey: str,
    toggle_hotkey: str,
) -> bool:
    """Проверяет, назначена ли одна клавиша на оба действия."""
    return point_hotkey == toggle_hotkey