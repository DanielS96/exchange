import os
import re
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URL_RUB_USDT = "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html"
URL_USDT_RUB = "https://www.bestchange.ru/tether-trc20-to-cash-ruble-in-msk.html"
CSS_RATE = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"

def get_weighted_rate(url: str) -> float | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка запроса к {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    elements = soup.select(CSS_RATE)
    
    if not elements:
        print(f"Элемент не найден на {url}")
        return None

    text = elements[0].get_text(strip=True)
    print(f"Текст элемента для {url}: {text}")

    # Извлекаем число (поддерживаем оба формата)
    m = re.search(r"([\d.,]+)", text)
    if not m:
        print(f"Число не найдено в {text}")
        return None

    rate_str = m.group(1).replace(",", ".")
    
    try:
        rate = float(rate_str)
        if rate <= 0:
            raise ValueError("Курс должен быть положительным")
        return rate
    except ValueError as e:
        print(f"Ошибка преобразования {rate_str}: {e}")
        return None

def main():
    rates = {}
    
    # Загружаем существующие курсы для fallback
    try:
        with open("rate.json", "r", encoding="utf-8") as f:
            old_rates = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        old_rates = {}

    # Получаем RUB → USDT
    rub_usdt = get_weighted_rate(URL_RUB_USDT)
    if rub_usdt is not None:
        rates["rub_usdt_msk"] = rub_usdt
        print(f"✅ rub_usdt_msk = {rub_usdt}")
    elif "rub_usdt_msk" in old_rates:
        rates["rub_usdt_msk"] = old_rates["rub_usdt_msk"]
        print(f"⚠️ Использую старый курс rub_usdt_msk = {old_rates['rub_usdt_msk']}")

    # Получаем USDT → RUB
    usdt_rub = get_weighted_rate(URL_USDT_RUB)
    if usdt_rub is not None:
        rates["usdt_rub_msk"] = usdt_rub
        print(f"✅ usdt_rub_msk = {usdt_rub}")
    elif "usdt_rub_msk" in old_rates:
        rates["usdt_rub_msk"] = old_rates["usdt_rub_msk"]
        print(f"⚠️ Использую старый курс usdt_rub_msk = {old_rates['usdt_rub_msk']}")

    rates["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Сохраняем результат
    with open("rate.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

    print(f"\n✅ rate.json обновлён: {json.dumps(rates, ensure_ascii=False, indent=2)}")
    
    # Проверяем, что оба курса получены
    if len(rates) < 3:  # минус updated_at
        print("⚠️ Внимание: не все курсы были обновлены!")

if __name__ == "__main__":
    main()
