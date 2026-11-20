"""Мини-CLI: курсы RUB, EUR, GBP и конвертер валют.

Запуск без аргументов открывает меню. Можно и одной командой:
    python cli.py rates USD
    python cli.py convert 100 USD RUB
    python cli.py rates EUR --refresh
"""

import argparse
import sys

from api_client import CurrencyAPIError
from converter import convert, load_rates, parse_amount, validate_code

SHOW = ("RUB", "EUR", "GBP")


def show_rates(base: str, refresh: bool = False) -> None:
    data, source = load_rates(base, force_refresh=refresh)
    base = data["base_code"]
    print(f"\nБазовая валюта: {base}  (источник: {source})")
    print(f"Курсы обновлены сервисом: {data['time_last_update_utc']}")
    print(f"Следующее обновление:    {data['time_next_update_utc']}")
    if source == "сохранённый кэш, сети нет":
        print("Внимание: обновить курсы не удалось, показаны сохранённые ранее.")
    for code in SHOW:
        if code == base:
            continue
        print(f"  1 {base} = {data['rates'][code]:.4f} {code}")


def do_convert(amount_text: str, from_code: str, to_code: str, refresh: bool = False) -> None:
    amount = parse_amount(amount_text)
    data, source = load_rates(from_code, force_refresh=refresh)
    from_code = data["base_code"]
    to_code = validate_code(to_code, data["rates"])
    result = convert(amount, from_code, to_code, data)
    print(f"\n{amount:g} {from_code} = {result:.4f} {to_code}")
    print(f"Курс 1 {from_code} = {data['rates'][to_code]} {to_code}  (источник: {source})")


def menu() -> None:
    while True:
        print("\n1 - курсы RUB, EUR, GBP")
        print("2 - конвертер")
        print("3 - обновить курсы принудительно")
        print("0 - выход")
        choice = input("Выбор: ").strip()
        try:
            if choice == "1":
                show_rates(input("Базовая валюта (например USD): ") or "USD")
            elif choice == "2":
                from_code = input("Из валюты: ")
                to_code = input("В валюту: ")
                amount = input("Сумма: ")
                do_convert(amount, from_code, to_code)
            elif choice == "3":
                show_rates(input("Базовая валюта (например USD): ") or "USD", refresh=True)
            elif choice == "0":
                print("До свидания!")
                return
            else:
                print("Введите 1, 2, 3 или 0.")
        except CurrencyAPIError as error:
            print(f"Ошибка: {error}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Курсы валют и конвертер (open.er-api.com)")
    sub = parser.add_subparsers(dest="command")
    p_rates = sub.add_parser("rates", help="курсы RUB, EUR, GBP для базовой валюты")
    p_rates.add_argument("base", nargs="?", default="USD")
    p_rates.add_argument("--refresh", action="store_true", help="не брать из кэша")
    p_conv = sub.add_parser("convert", help="перевести сумму")
    p_conv.add_argument("amount")
    p_conv.add_argument("from_code")
    p_conv.add_argument("to_code")
    p_conv.add_argument("--refresh", action="store_true", help="не брать из кэша")
    args = parser.parse_args(argv)

    try:
        if args.command == "rates":
            show_rates(args.base, args.refresh)
        elif args.command == "convert":
            do_convert(args.amount, args.from_code, args.to_code, args.refresh)
        else:
            menu()
    except CurrencyAPIError as error:
        print(f"Ошибка: {error}")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nВыход.")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
