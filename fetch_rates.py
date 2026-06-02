import re
import json
from datetime import datetime, timezone
from collections import deque

import requests
from bs4 import BeautifulSoup

# ========== НАСТРОЙКИ (без наценок) ==========
# Здесь больше нет MARKUP_* переменных
# ============================================

URL_RUB_USDT = "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html"
URL_USDT_RUB = "https://www.bestchange.ru/tether-trc20-to-cash-ruble-in-msk.html"
CSS_RATE = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"

# Максимальное количество точек на графике (24 = 2 часа при обновлении каждые 5 минут)
MAX_HISTORY_POINTS = 24

def load_history():
    """Загружает историю курсов из файла"""
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
            if "rub_usdt_history" in history:
                history["rub_usdt_history"] = history["rub_usdt_history"][-MAX_HISTORY_POINTS:]
            return history
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "rub_usdt_history": [],
            "last_update": None
        }

def save_history(history):
    """Сохраняет историю курсов в файл"""
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

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
    print("=" * 50)
    print("Начинаем парсинг базовых курсов обмена...")
    print("=" * 50)
    
    rates = {}
    
    # Загружаем предыдущие курсы для fallback
    try:
        with open("rate.json", "r", encoding="utf-8") as f:
            old_rates = json.load(f)
            print("✓ Загружены предыдущие курсы")
    except (FileNotFoundError, json.JSONDecodeError):
        old_rates = {}
        print("! Предыдущие курсы не найдены")
    
    # Загружаем историю
    history = load_history()
    
    # Получаем базовый RUB → USDT (без наценки)
    rub_usdt = get_weighted_rate(URL_RUB_USDT)
    if rub_usdt is not None:
        rates["rub_usdt_msk"] = rub_usdt
        print(f"✓ Базовый RUB→USDT: {rub_usdt}")
        
        # Добавляем в историю
        now = datetime.now(timezone.utc).isoformat()
        history["rub_usdt_history"].append({
            "time": now,
            "rate": rub_usdt
        })
        if len(history["rub_usdt_history"]) > MAX_HISTORY_POINTS:
            history["rub_usdt_history"] = history["rub_usdt_history"][-MAX_HISTORY_POINTS:]
        history["last_update"] = now
        
    elif "rub_usdt_msk" in old_rates:
        rates["rub_usdt_msk"] = old_rates["rub_usdt_msk"]
        print(f"⚠ Использую старый RUB→USDT: {old_rates['rub_usdt_msk']}")

    # Получаем базовый USDT → RUB (без наценки)
    usdt_rub = get_weighted_rate(URL_USDT_RUB)
    if usdt_rub is not None:
        rates["usdt_rub_msk"] = usdt_rub
        print(f"✓ Базовый USDT→RUB: {usdt_rub}")
    elif "usdt_rub_msk" in old_rates:
        rates["usdt_rub_msk"] = old_rates["usdt_rub_msk"]
        print(f"⚠ Использую старый USDT→RUB: {old_rates['usdt_rub_msk']}")

    rates["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Сохраняем текущие курсы
    with open("rate.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)
    
    # Сохраняем историю
    save_history(history)

    print("\n" + "=" * 50)
    print("Базовые курсы сохранены в rate.json:")
    print(json.dumps(rates, ensure_ascii=False, indent=2))
    print("\nИстория сохранена в history.json (без наценок)")
    print("=" * 50)

if __name__ == "__main__":
    main()
