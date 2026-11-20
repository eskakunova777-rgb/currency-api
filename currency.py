"""Базовый уровень одним файлом: исправленный currency.py.

Средний уровень разнесён по модулям: api_client.py, storage.py, converter.py, cli.py.
Формат currency_rate.json у них общий.
"""

import json
import os
import time

import requests

CACHE_FILE = "currency_rate.json"
MAX_AGE = 24 * 60 * 60
SHOW = ("RUB", "EUR", "GBP")


def get_currency_rates(base: str) -> dict:
    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.Timeout:
        raise RuntimeError("Сервер курсов не ответил за 10 секунд.") from None
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Нет связи с сервером курсов, проверьте интернет.") from None
    if response.status_code != 200:
        raise RuntimeError(f"Сервер ответил кодом {response.status_code} вместо 200.")
    data = response.json()
    if data.get("result") != "success":
        raise RuntimeError(f"Валюта {base} не поддерживается ({data.get('error-type')}).")
    return data


def save_to_file(data: dict, path: str = CACHE_FILE) -> None:
    # encoding задаётся в open(), у json.dump такого аргумента нет
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def read_from_file(path: str = CACHE_FILE) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def get_rates_cached(base: str):
    cache = read_from_file()
    entry = cache.get(base)
    if entry and time.time() - entry["saved_at_unix"] < MAX_AGE:
        return entry["response"], "кэш"
    data = get_currency_rates(base)
    cache[base] = {
        "saved_at_unix": int(time.time()),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "response": data,
    }
    save_to_file(cache)
    return data, "сеть"


if __name__ == "__main__":
    base = input("Базовая валюта (например USD): ").strip().upper() or "USD"
    if len(base) != 3 or not base.isalpha() or not base.isascii():
        print("Ошибка: код валюты это три латинские буквы, например USD.")
    else:
        try:
            data, source = get_rates_cached(base)
        except RuntimeError as error:
            print(f"Ошибка: {error}")
        else:
            print(f"Базовая валюта: {data['base_code']} (источник: {source})")
            print(f"Обновлено: {data['time_last_update_utc']}")
            for code in SHOW:
                if code != base:
                    print(f"  1 {base} = {data['rates'][code]:.4f} {code}")
