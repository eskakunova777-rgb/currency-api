"""Логика: курсы из кэша или из сети, проверка кодов, конвертация."""

import storage
from api_client import CurrencyAPIError, get_currency_rates, normalize_code


def load_rates(base: str, force_refresh: bool = False, path: str = storage.CACHE_FILE):
    """Возвращает (ответ_API, источник). Источник: "кэш", "сеть" или "сохранённый кэш, сети нет".

    Свежий кэш (моложе 24 часов) читается из файла, иначе делается запрос.
    Если сети нет, но в файле есть старая запись, используется она с пометкой.
    """
    base = normalize_code(base)
    cached, age = storage.get_cached(base, path)
    if cached is not None and storage.is_fresh(age) and not force_refresh:
        return cached, "кэш"
    try:
        response = get_currency_rates(base)
    except CurrencyAPIError:
        if cached is not None:
            return cached, "сохранённый кэш, сети нет"
        raise
    storage.put_cached(base, response, path)
    return response, "сеть"


def validate_code(code: str, known_codes) -> str:
    """Проверяет код по списку ключей rates. Возвращает код в верхнем регистре."""
    code = normalize_code(code)
    if code not in known_codes:
        raise CurrencyAPIError(
            f"Валюты {code} нет в списке курсов ({len(known_codes)} кодов). "
            "Примеры: USD, EUR, RUB, GBP."
        )
    return code


def convert(amount: float, from_code: str, to_code: str, response: dict) -> float:
    """Переводит сумму по ответу API, где base_code == from_code. 4 знака после запятой."""
    if response.get("base_code") != from_code:
        raise CurrencyAPIError(
            f"Курсы загружены для {response.get('base_code')}, а нужны для {from_code}."
        )
    rate = response["rates"][validate_code(to_code, response["rates"])]
    return round(amount * rate, 4)


def parse_amount(text: str) -> float:
    try:
        amount = float(str(text).replace(",", ".").replace(" ", ""))
    except ValueError:
        raise CurrencyAPIError(f"«{text}» не число. Пример суммы: 100 или 12,5.") from None
    if amount < 0:
        raise CurrencyAPIError("Сумма не может быть отрицательной.")
    return amount
