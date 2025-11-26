"""Утилиты для работы с текстом"""


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезает текст до указанной длины

    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Что добавить в конце

    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def escape_html(text: str) -> str:
    """
    Экранирует HTML-теги в тексте

    Args:
        text: Исходный текст

    Returns:
        Текст с экранированными HTML-тегами
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def escape_markdown(text: str) -> str:
    """
    Экранирует Markdown-символы

    Args:
        text: Исходный текст

    Returns:
        Текст с экранированными Markdown-символами
    """
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)
