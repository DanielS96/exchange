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

def get_weighted_rate(url: str, name: str) -> float | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        print(f"  Запрос к {name}...")
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ❌ Ошибка запроса: {e}")
        return None
    
    soup = BeautifulSoup(resp.text, "html.parser")
    elements = soup.select(CSS_RATE)
    if not elements:
        print(f"  ❌ Элемент не найден на странице")
        return None
    
    text = elements[0].get_text(strip=True)
    print(f"  Найден текст: {text}")
    
    m = re.search(r"([\d.,]+)", text)
    if not m:
        print(f"  ❌ Число не найдено")
        return None
    
    rate_str = m.group(1).replace(",", ".")
    try:
        rate = float(rate_str)
        print(f"  ✅ Курс: {rate}")
        return rate
    except:
        print(f"  ❌ Ошибка преобразования: {rate_str}")
        return None

def main():
    print("=" * 50)
    print("Запуск fetch_rates.py")
    print("=" * 50)
    
    # 1. Получаем оба курса
    print("\n1. Получаем курс RUB→USDT...")
    rub_usdt = get_weighted_rate(URL_RUB_USDT, "RUB→USDT")
    
    print("\n2. Получаем курс USDT→RUB...")
    usdt_rub = get_weighted_rate(URL_USDT_RUB, "USDT→RUB")
    
    if rub_usdt is None and usdt_rub is None:
        print("\n❌ Не удалось получить ни одного курса! Выход.")
        return
    
    # 2. Загружаем существующую историю
    print("\n3. Загружаем history.json...")
    history = {
        "rub_usdt_history": [],  # история курса RUB→USDT
        "usdt_rub_history": []   # история курса USDT→RUB
    }
    
    if os.path.exists("history.json"):
        try:
            with open("history.json", "r", encoding="utf-8") as f:
                loaded = json.load(f)
                history["rub_usdt_history"] = loaded.get("rub_usdt_history", [])
                history["usdt_rub_history"] = loaded.get("usdt_rub_history", [])
            print(f"   Загружено: RUB→USDT: {len(history['rub_usdt_history'])} записей, USDT→RUB: {len(history['usdt_rub_history'])} записей")
        except Exception as e:
            print(f"   Ошибка чтения: {e}, создаём новый файл")
            history = {"rub_usdt_history": [], "usdt_rub_history": []}
    else:
        print("   Файл history.json не существует, создаём новый")
    
    # 3. Добавляем новые записи
    now = datetime.now(timezone.utc).isoformat()
    
    if rub_usdt is not None:
        print("\n4. Добавляем запись в RUB→USDT историю...")
        history["rub_usdt_history"].append({
            "time": now,
            "rate": rub_usdt
        })
        # Обрезаем историю
        if len(history["rub_usdt_history"]) > MAX_HISTORY_POINTS:
            history["rub_usdt_history"] = history["rub_usdt_history"][-MAX_HISTORY_POINTS:]
        print(f"   Теперь RUB→USDT записей: {len(history['rub_usdt_history'])}")
    
    if usdt_rub is not None:
        print("\n5. Добавляем запись в USDT→RUB историю...")
        history["usdt_rub_history"].append({
            "time": now,
            "rate": usdt_rub
        })
        # Обрезаем историю
        if len(history["usdt_rub_history"]) > MAX_HISTORY_POINTS:
            history["usdt_rub_history"] = history["usdt_rub_history"][-MAX_HISTORY_POINTS:]
        print(f"   Теперь USDT→RUB записей: {len(history['usdt_rub_history'])}")
    
    history["last_update"] = now
    
    # 4. Сохраняем history.json
    print("\n6. Сохраняем history.json...")
    try:
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("   ✅ history.json сохранён")
        file_size = os.path.getsize("history.json")
        print(f"   Размер файла: {file_size} байт")
    except Exception as e:
        print(f"   ❌ Ошибка сохранения history.json: {e}")
    
    # 5. Сохраняем rate.json с обоими курсами
    print("\n7. Сохраняем rate.json...")
    
    # Загружаем старые курсы для fallback
    old_rates = {}
    if os.path.exists("rate.json"):
        try:
            with open("rate.json", "r", encoding="utf-8") as f:
                old_rates = json.load(f)
        except:
            pass
    
    rate_data = {
        "updated_at": now
    }
    
    if rub_usdt is not None:
        rate_data["rub_usdt_msk"] = rub_usdt
    elif "rub_usdt_msk" in old_rates:
        rate_data["rub_usdt_msk"] = old_rates["rub_usdt_msk"]
        print(f"   ⚠️ Использую старый RUB→USDT: {old_rates['rub_usdt_msk']}")
    
    if usdt_rub is not None:
        rate_data["usdt_rub_msk"] = usdt_rub
    elif "usdt_rub_msk" in old_rates:
        rate_data["usdt_rub_msk"] = old_rates["usdt_rub_msk"]
        print(f"   ⚠️ Использую старый USDT→RUB: {old_rates['usdt_rub_msk']}")
    
    try:
        with open("rate.json", "w", encoding="utf-8") as f:
            json.dump(rate_data, f, ensure_ascii=False, indent=2)
        print("   ✅ rate.json сохранён")
    except Exception as e:
        print(f"   ❌ Ошибка сохранения rate.json: {e}")
    
    # 6. Финальная проверка
    print("\n" + "=" * 50)
    print("ПРОВЕРКА:")
    print(f"  - rate.json: rub_usdt_msk = {rate_data.get('rub_usdt_msk', 'N/A')}")
    print(f"  - rate.json: usdt_rub_msk = {rate_data.get('usdt_rub_msk', 'N/A')}")
    print(f"  - RUB→USDT история: {len(history.get('rub_usdt_history', []))} записей")
    print(f"  - USDT→RUB история: {len(history.get('usdt_rub_history', []))} записей")
    print("=" * 50)
    print("✅ Готово!")

if __name__ == "__main__":
    main()
