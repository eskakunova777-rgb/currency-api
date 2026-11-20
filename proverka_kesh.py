"""Проверка критерия: конвертация из кэша и из свежего ответа совпадает.

Для каждой пары делается свежий запрос, ответ сохраняется в currency_rate.json,
потом читается из файла, и результат конвертации сравнивается.
"""

import sys

import storage
from api_client import CurrencyAPIError, get_currency_rates
from converter import convert

PAIRS = [(100, "USD", "RUB"), (100, "EUR", "GBP")]


def main() -> int:
    ok = True
    for amount, src, dst in PAIRS:
        try:
            fresh = get_currency_rates(src)
        except CurrencyAPIError as error:
            print(f"Ошибка: {error}")
            return 1
        storage.put_cached(src, fresh)
        cached, age = storage.get_cached(src)
        a = convert(amount, src, dst, fresh)
        b = convert(amount, src, dst, cached)
        same = a == b
        ok &= same
        print(f"{amount} {src} -> {dst}: свежий ответ {a:.4f}, из кэша {b:.4f}  "
              f"{'совпадает' if same else 'РАЗНИЦА'}")
    print("Итог:", "всё совпадает" if ok else "есть расхождения")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
