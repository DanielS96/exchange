import os
import re
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URL = "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html"

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

    # Ищем точную фразу: "Средневзвешенный курс обмена: 77.240772"
    rate = None
    for el in soup.find_all(string=re.compile(r"Средневзвешенный курс обмена:")):
        text = el.strip()
        # пример: "Средневзвешенный курс обмена: 77.240772"
        m = re.search(r"Средневзвешенный курс обмена:\s*([\d.,]+)", text)
        if m:
            rate_str = m.group(1).replace(",", ".")
            rate = float(rate_str)
            print(f"Найден средневзвешенный курс: {rate}")
            break

    if rate is None:
        print("Средневзвешенный курс не найден в странице")
        # для отладки сохранит страницу
        with open("debug_bestchange.html", "w", encoding="utf-8") as f:
            f.write(html)

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
