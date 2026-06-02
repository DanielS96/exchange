import re
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URL_RUB_USDT = "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html"
URL_USDT_RUB = "https://www.bestchange.ru/tether-trc20-to-cash-ruble-in-msk.html"
CSS_RATE = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"

MAX_HISTORY_POINTS = 8640  # 30 дней

def get_weighted_rate(url: str) -> float | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
        return None
    text = elements[0].get_text(strip=True)
    m = re.search(r"([\d.,]+)", text)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))

def main():
    print("Начинаем парсинг...")
    
    # Получаем курс
    rub_usdt = get_weighted_rate(URL_RUB_USDT)
    if rub_usdt is None:
        print("Не удалось получить курс")
        return
    
    print(f"Текущий курс: {rub_usdt}")
    
    # Загружаем существующую историю
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
        print(f"Загружено {len(history.get('rub_usdt_history', []))} записей")
    except:
        history = {"rub_usdt_history": []}
        print("Создаём новую историю")
    
    # Добавляем новую запись
    new_entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "rate": rub_usdt
    }
    history["rub_usdt_history"].append(new_entry)
    
    # Оставляем только последние MAX_HISTORY_POINTS
    if len(history["rub_usdt_history"]) > MAX_HISTORY_POINTS:
        history["rub_usdt_history"] = history["rub_usdt_history"][-MAX_HISTORY_POINTS:]
    
    history["last_update"] = new_entry["time"]
    
    # Сохраняем
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"Сохранено! Всего записей: {len(history['rub_usdt_history'])}")
    
    # Сохраняем текущий курс в rate.json
    with open("rate.json", "w", encoding="utf-8") as f:
        json.dump({
            "rub_usdt_msk": rub_usdt,
            "usdt_rub_msk": 0,  # можно тоже получать, но для начала так
            "updated_at": new_entry["time"]
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
