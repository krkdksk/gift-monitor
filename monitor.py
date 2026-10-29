import os
import json
import requests
from datetime import datetime
from TelegramGifts import TelegramGifts

# ========== НАСТРОЙКИ ==========
WATCH_LIST = [
    "Plush Pepe",
    "Durov's Cap",
    "Snoop Dogg",
    "Liberty Figure",
    "Vice Cream",
    "Chill Flame",
    "Lol Pop",
]

THRESHOLD = 3.0  # уведомление если изменение больше 3%
# ===============================

STATE_FILE = "state.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def send_msg(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("Нет BOT_TOKEN или CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=15)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def main():
    print(f"=== Проверка {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    gifts = TelegramGifts()
    state = load_state()
    messages = []

    for name in WATCH_LIST:
        try:
            info = gifts.get_gift(name)
            if not info:
                print(f"[!] Не найден: {name}")
                continue

            prices = info.get("prices", {})
            current = prices.get("floor_price_ton")
            
            if current is None:
                print(f"[!] Нет цены у {name}")
                continue

            current = float(current)
            prev = state.get(name, {}).get("floor")

            change = 0.0
            if prev is not None and prev > 0:
                change = ((current - prev) / prev) * 100

            state[name] = {
                "floor": current,
                "tgmrkt": prices.get("tgmrkt_price_ton"),
                "getgems": prices.get("getgems_price_ton"),
                "time": datetime.now().isoformat()
            }

            arrow = "→"
            if change > 0.5:
                arrow = "↑"
            elif change < -0.5:
                arrow = "↓"

            print(f"{name:22} | {current:8.2f} TON  {arrow} {change:+6.2f}%")

            if abs(change) >= THRESHOLD and prev is not None:
                direction = "📈 РОСТ" if change > 0 else "📉 ПАДЕНИЕ"
                messages.append(
                    f"<b>{name}</b>\n"
                    f"{direction} <b>{change:+.1f}%</b>\n"
                    f"{prev:.2f} → <b>{current:.2f} TON</b>"
                )

        except Exception as e:
            print(f"[!] Ошибка {name}: {e}")

    save_state(state)

    if messages:
        full_text = "🎁 <b>Изменение цен на подарки</b>\n\n" + "\n\n".join(messages)
        send_msg(full_text)
        print("→ Уведомление отправлено")
    else:
        print("Изменений нет")

if __name__ == "__main__":
    main()
