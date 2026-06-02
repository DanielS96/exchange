import re
import json
import os
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
        print(f"  Запрос к {url[:50]}...")
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ОШИБКА запроса: {e}")
        return None
    
    soup = BeautifulSoup(resp.text, "html.parser")
    elements = soup.select(CSS_RATE)
    if not elements:
        print(f"  Элемент не найден на странице")
        return None
    
    text = elements[0].get_text(strip=True)
    print(f"  Найден текст: {text}")
    
    m = re.search(r"([\d.,]+)", text)
    if not m:
        print(f"  Число не найдено")
        return None
    
    rate_str = m.group(1).replace(",", ".")
    try:
        rate = float(rate_str)
        print(f"  Курс: {rate}")
        return rate
    except:
        print(f"  Ошибка преобразования: {rate_str}")
        return None

def main():
    print("=" * 50)
    print("Запуск fetch_rates.py")
    print("=" * 50)
    
    # 1. Получаем курс
    print("\n1. Получаем курс RUB→USDT...")
    rub_usdt = get_weighted_rate(URL_RUB_USDT)
    if rub_usdt is None:
        print("❌ Не удалось получить курс! Выход.")
        return
    
    print(f"\n✅ Текущий курс: {rub_usdt}")
    
    # 2. Загружаем существующую историю
    print("\n2. Загружаем history.json...")
    history = {"rub_usdt_history": []}
    
    if os.path.exists("history.json"):
        try:
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
            print(f"   Загружено {len(history.get('rub_usdt_history', []))} записей")
        except Exception as e:
            print(f"   Ошибка чтения: {e}, создаём новый файл")
            history = {"rub_usdt_history": []}
    else:
        print("   Файл history.json не существует, создаём новый")
    
    # 3. Добавляем новую запись
    print("\n3. Добавляем новую запись...")
    new_entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "rate": rub_usdt
    }
    history["rub_usdt_history"].append(new_entry)
    
    # 4. Обрезаем историю
    before = len(history["rub_usdt_history"])
    if len(history["rub_usdt_history"]) > MAX_HISTORY_POINTS:
        history["rub_usdt_history"] = history["rub_usdt_history"][-MAX_HISTORY_POINTS:]
    after = len(history["rub_usdt_history"])
    print(f"   Было: {before}, стало: {after} записей")
    
    history["last_update"] = new_entry["time"]
    
    # 5. Сохраняем history.json
    print("\n4. Сохраняем history.json...")
    try:
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("   ✅ history.json сохранён")
        
        # Проверяем, что записалось
        file_size = os.path.getsize("history.json")
        print(f"   Размер файла: {file_size} байт")
    except Exception as e:
        print(f"   ❌ Ошибка сохранения history.json: {e}")
    
    # 6. Сохраняем rate.json
    print("\n5. Сохраняем rate.json...")
    try:
        with open("rate.json", "w", encoding="utf-8") as f:
            json.dump({
                "rub_usdt_msk": rub_usdt,
                "usdt_rub_msk": 0,
                "updated_at": new_entry["time"]
            }, f, ensure_ascii=False, indent=2)
        print("   ✅ rate.json сохранён")
    except Exception as e:
        print(f"   ❌ Ошибка сохранения rate.json: {e}")
    
    # 7. Финальная проверка
    print("\n" + "=" * 50)
    print("ПРОВЕРКА:")
    print(f"  - history.json существует: {os.path.exists('history.json')}")
    print(f"  - Записей в истории: {len(history['rub_usdt_history'])}")
    if len(history['rub_usdt_history']) > 0:
        print(f"  - Последняя запись: {history['rub_usdt_history'][-1]}")
    print("=" * 50)
    print("✅ Готово!")

if __name__ == "__main__":
    main()
