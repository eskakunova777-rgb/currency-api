"""Работа с файлом-кэшем currency_rate.json."""

import json
import os
import time

CACHE_FILE = "currency_rate.json"
MAX_AGE_SECONDS = 24 * 60 * 60  # 24 часа


def save_to_file(data: dict, path: str = CACHE_FILE) -> None:
    # У json.dump нет аргумента encoding: кодировку задаём в open().
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def read_from_file(path: str = CACHE_FILE) -> dict:
    """Читает JSON. Если файла нет или он испорчен, возвращает пустой dict."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def get_cached(base: str, path: str = CACHE_FILE, max_age: int = MAX_AGE_SECONDS):
    """Ответ API для base из кэша и его возраст в секундах, или (None, None).

    Устаревшую запись тоже возвращает: вызывающий сам решает, годится ли она.
    """
    entry = read_from_file(path).get(base)
    if not entry or "saved_at_unix" not in entry or "response" not in entry:
        return None, None
    age = time.time() - entry["saved_at_unix"]
    return entry["response"], age


def put_cached(base: str, response: dict, path: str = CACHE_FILE) -> None:
    """Сохраняет ответ для base, не трогая записи других базовых валют."""
    cache = read_from_file(path)
    cache[base] = {
        "saved_at_unix": int(time.time()),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "response": response,
    }
    save_to_file(cache, path)


def is_fresh(age, max_age: int = MAX_AGE_SECONDS) -> bool:
    return age is not None and 0 <= age < max_age
