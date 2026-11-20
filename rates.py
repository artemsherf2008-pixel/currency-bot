"""
Курсы валют -> Telegram.
Запускается по расписанию на GitHub Actions (см. файл rates.yml).
Данные: open.er-api.com (ExchangeRate-API). Источник обновляет курсы раз в сутки.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# ---------- Настройки (можно менять) ----------

# В какой валюте показывать цену. Например, "RUB" даёт строки вида "1 USD = 95.12 RUB".
# Можно поставить "USD", "EUR", "KZT" и т.д.
BASE = "RUB"

# Какие валюты показывать (коды из трёх букв)
CURRENCIES = [
    "USD", "EUR", "GBP", "CHF", "JPY", "CNY", "TRY",
    "AED", "KZT", "INR", "BRL", "CAD", "AUD", "PLN",
]

# True = сообщения приходят без звука, False = со звуком
SILENT = True

FLAGS = {
    "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "CHF": "🇨🇭", "JPY": "🇯🇵",
    "CNY": "🇨🇳", "TRY": "🇹🇷", "AED": "🇦🇪", "KZT": "🇰🇿", "INR": "🇮🇳",
    "BRL": "🇧🇷", "CAD": "🇨🇦", "AUD": "🇦🇺", "PLN": "🇵🇱",
}

# ---------- Секреты (берутся из настроек GitHub, в коде их нет) ----------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TOKEN or not CHAT_ID:
    sys.exit("Не заданы TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID. Добавь их в Secrets репозитория.")


def fetch_rates() -> dict:
    url = f"https://open.er-api.com/v6/latest/{BASE}"
    request = urllib.request.Request(url, headers={"User-Agent": "currency-telegram-bot"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as e:
        sys.exit(f"Сервис курсов вернул ошибку {e.code}")
    except urllib.error.URLError as e:
        sys.exit(f"Не удалось связаться с сервисом курсов: {e.reason}")

    if data.get("result") != "success":
        sys.exit(f"Сервис курсов ответил с ошибкой: {data.get('error-type', 'неизвестно')}")
    return data


def fmt(value: float) -> str:
    if value >= 1:
        return f"{value:,.2f}".replace(",", " ")
    return f"{value:.4f}"


def build_message(data: dict) -> str:
    rates = data.get("rates") or data.get("conversion_rates") or {}
    lines = [f"💱 Курсы валют (к {BASE})", ""]

    for code in CURRENCIES:
        if code == BASE:
            continue
        rate = rates.get(code)
        if not rate:
            continue
        flag = FLAGS.get(code, "💱")
        # Сервис отдаёт «сколько единиц валюты за 1 BASE», нам нужно наоборот
        lines.append(f"{flag} 1 {code} = {fmt(1 / rate)} {BASE}")

    updated = data.get("time_last_update_utc", "неизвестно")
    lines += ["", f"Источник обновил данные: {updated}", "Источник: exchangerate-api.com"]
    return "\n".join(lines)


def send(text: str) -> None:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_notification": "true" if SILENT else "false",
    }
    request = urllib.request.Request(url, data=urllib.parse.urlencode(payload).encode())
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"Telegram вернул ошибку {e.code}: {e.read().decode(errors='ignore')}")
    except urllib.error.URLError as e:
        sys.exit(f"Не удалось связаться с Telegram: {e.reason}")


if __name__ == "__main__":
    send(build_message(fetch_rates()))
    print("Сообщение отправлено.")
