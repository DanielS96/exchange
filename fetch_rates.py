import re
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# ========== НАСТРОЙКИ НАЦЕНКИ ==========
MARKUP_RUB_USDT = 3.0   # добавить X рублей к курсу RUB → USDT
MARKUP_USDT_RUB = 0   # добавить X рублей к курсу USDT → RUB
# ======================================

URL_RUB_USDT = "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html"
URL_USDT_RUB = "https://www.bestchange.ru/tether-trc20-to-cash-ruble-in-msk.html"
CSS_RATE = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"

def get_weighted_rate(url: str) -> float | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    elements = soup.select(CSS_RATE)
    
    if not elements:
        print(f"Элемент не найден на {url}")
        return None

    text = elements[0].get_text(strip=True)
    m = re.search(r"([\d.,]+)", text)
    if not m:
        return None

    rate_str = m.group(1).replace(",", ".")
    
    try:
        return float(rate_str)
    except ValueError:
        return None

def main():
    rates = {}
    
    # Загружаем старые курсы на случай ошибки
    try:
        with open("rate.json", "r", encoding="utf-8") as f:
            old_rates = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        old_rates = {}

    # Получаем RUB → USDT и добавляем наценку
    rub_usdt = get_weighted_rate(URL_RUB_USDT)
    if rub_usdt is not None:
        rates["rub_usdt_msk"] = rub_usdt + MARKUP_RUB_USDT
        print(f"RUB→USDT: {rub_usdt} + {MARKUP_RUB_USDT} = {rates['rub_usdt_msk']}")
    elif "rub_usdt_msk" in old_rates:
        rates["rub_usdt_msk"] = old_rates["rub_usdt_msk"]
        print(f"Использую старый RUB→USDT: {rates['rub_usdt_msk']}")

    # Получаем USDT → RUB и добавляем наценку
    usdt_rub = get_weighted_rate(URL_USDT_RUB)
    if usdt_rub is not None:
        rates["usdt_rub_msk"] = usdt_rub + MARKUP_USDT_RUB
        print(f"USDT→RUB: {usdt_rub} + {MARKUP_USDT_RUB} = {rates['usdt_rub_msk']}")
    elif "usdt_rub_msk" in old_rates:
        rates["usdt_rub_msk"] = old_rates["usdt_rub_msk"]
        print(f"Использую старый USDT→RUB: {rates['usdt_rub_msk']}")

    rates["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open("rate.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

    print("✅ Готово!")

if __name__ == "__main__":
    main()
