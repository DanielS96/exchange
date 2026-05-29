import os
import re
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# URL для RUB → USDT (Москва)
URL_RUB_USDT = "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html"
# URL для USDT → RUB (Москва)
URL_USDT_RUB = "https://www.bestchange.ru/tether-trc20-to-cash-ruble-in-msk.html"

# CSS-селектор для средневзвешенного курса (один и тот же для обеих страниц)
CSS_RATE = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"

def get_weighted_rate(url: str) -> float | None:
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
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка запроса к {url}: {e}")
        return None

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    elements = soup.select(CSS_RATE)
    if not elements:
        print(f"Элемент по CSS-селектору не найден на {url}")
        with open(f"debug_{url.replace('https://', '').replace('/', '_')}.html", "w", encoding="utf-8") as f:
            f.write(html)
        return None

    text = elements[0].get_text(strip=True)
    print(f"Текст элемента для {url}: {text}")

    # Извлекаем число: "77.240772" или "77,240772"
    m = re.search(r"([\d.,]+)", text)
    if not m:
        print(f"Число не найдено в тексте элемента для {url}")
        return None

    rate_str = m.group(1).replace(",", ".")
    try:
        rate = float(rate_str)
    except ValueError:
        print(f"Не удалось преобразовать в float: {rate_str} для {url}")
        return None

    print(f"Найден средневзвешенный курс для {url}: {rate}")
    return rate

def main():
    rates = {}

    # RUB → USDT
    rub_usdt = get_weighted_rate(URL_RUB_USDT)
    if rub_usdt is not None and rub_usdt > 0:
        rates["rub_usdt_msk"] = rub_usdt
        print(f"rub_usdt_msk = {rub_usdt}")
    else:
        print("Не удалось получить rub_usdt_msk")

    # USDT → RUB
    usdt_rub = get_weighted_rate(URL_USDT_RUB)
    if usdt_rub is not None and usdt_rub > 0:
        rates["usdt_rub_msk"] = usdt_rub
        print(f"usdt_rub_msk = {usdt_rub}")
    else:
        print("Не удалось получить usdt_rub_msk")

    rates["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open("rate.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

    print("rate.json обновлён:")
    print(json.dumps(rates, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
