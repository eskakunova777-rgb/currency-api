"""HTTP-часть: запрос курсов валют к open.er-api.com."""

import os
import re

import requests

# Адрес можно подменить переменной окружения (так проверяется ошибка сети).
BASE_URL = os.environ.get("CURRENCY_API_URL", "https://open.er-api.com/v6/latest")
TIMEOUT = float(os.environ.get("CURRENCY_API_TIMEOUT", "10"))

CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


class CurrencyAPIError(Exception):
    """Понятная ошибка для пользователя, без стектрейса."""


def normalize_code(code: str) -> str:
    """Приводит код к виду USD и проверяет, что это три латинские буквы."""
    code = (code or "").strip().upper()
    if not CODE_PATTERN.match(code):
        raise CurrencyAPIError(
            f"«{code or 'пусто'}» не похоже на код валюты: нужны три латинские буквы, например USD."
        )
    return code


def get_currency_rates(base: str) -> dict:
    """Возвращает полный ответ API (dict) для базовой валюты base."""
    base = normalize_code(base)
    url = f"{BASE_URL}/{base}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        raise CurrencyAPIError(
            f"Сервер курсов не ответил за {TIMEOUT:g} с. Попробуйте позже."
        ) from None
    except requests.exceptions.ConnectionError:
        raise CurrencyAPIError(
            "Нет связи с сервером курсов. Проверьте интернет и попробуйте снова."
        ) from None
    except requests.exceptions.RequestException as exc:
        raise CurrencyAPIError(f"Запрос не удался: {exc.__class__.__name__}.") from None

    if response.status_code != 200:
        raise CurrencyAPIError(
            f"Сервер ответил кодом {response.status_code} вместо 200 (адрес {url})."
        )

    try:
        data = response.json()
    except ValueError:
        raise CurrencyAPIError("Сервер прислал ответ не в формате JSON.") from None

    # Неизвестную валюту API отдаёт с кодом 200, но с result = "error".
    if data.get("result") != "success":
        error_type = data.get("error-type", "unknown")
        if error_type == "unsupported-code":
            raise CurrencyAPIError(f"Валюта {base} не поддерживается сервисом.")
        raise CurrencyAPIError(f"Сервис вернул ошибку: {error_type}.")

    if not isinstance(data.get("rates"), dict):
        raise CurrencyAPIError("В ответе нет таблицы курсов (поле rates).")
    return data
