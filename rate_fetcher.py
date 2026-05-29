import os
import re
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# Только Москва
URLS = {
    "rub_usdt_msk": "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html",
    "usdt_rub_msk": "https://www.bestchange.ru/tether-trc20-to-cash-ruble-in-msk.html",
}

def get_weighted_rate(url: str) -> float | None:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        html = requests.get(url, headers=headers, timeout=10).text
    except Exception as e:
        print(f"Ошибка запроса к {url}: {e}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    rate = None
    for el in soup.find_all(string=re.compile(r"Средневзвешенный курс обмена:")):
        text = el.strip()
        m = re.search(r"Средневзвешенный курс обмена:\s*([\d.,]+)", text)
        if m:
            rate_str = m.group(1).replace(",", ".")
            rate = float(rate_str)
            break

    return rate

def main():
    rates = {}

    rub_usdt = get_weighted_rate(URLS["rub_usdt_msk"])
    if rub_usdt is not None:
        rates["rub_usdt_msk"] = rub_usdt
        rates["usdt_rub_msk"] = 1 / rub_usdt

    rates["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open("rate.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

    print("rate.json обновлён:")
    print(json.dumps(rates, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
