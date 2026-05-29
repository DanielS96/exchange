import os
import re
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URL = "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html"

# CSS-селектор для средневзвешенного курса
CSS_RATE = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"

def get_weighted_rate() -> float | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка запроса к BestChange: {e}")
        return None

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    elements = soup.select(CSS_RATE)
    if not elements:
        print("Элемент по CSS-селектору не найден")
        with open("debug_bestchange.html", "w", encoding="utf-8") as f:
            f.write(html)
        return None

    text = elements[0].get_text(strip=True)
    print(f"Текст элемента: {text}")

    # Извлекаем число: "77.240772" или "77,240772"
    m = re.search(r"([\d.,]+)", text)
    if not m:
        print("Число не найдено в тексте элемента")
        return None

    rate_str = m.group(1).replace(",", ".")
    try:
        rate = float(rate_str)
    except ValueError:
        print(f"Не удалось преобразовать в float: {rate_str}")
        return None

    print(f"Найден средневзвешенный курс: {rate}")
    return rate

def main():
    rates = {}

    rub_usdt = get_weighted_rate()
    if rub_usdt is not None and rub_usdt > 0:
        rates["rub_usdt_msk"] = rub_usdt
        rates["usdt_rub_msk"] = 1 / rub_usdt
        print(f"rub_usdt_msk = {rub_usdt}, usdt_rub_msk = {1 / rub_usdt}")
    else:
        print("Не удалось получить курс, поля не будут добавлены")

    rates["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open("rate.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

    print("rate.json обновлён:")
    print(json.dumps(rates, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
