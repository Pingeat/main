import os
import csv
from datetime import datetime, timedelta
from pytz import timezone
import requests
from stateHandlers.redis_state import get_user_cart

# File paths
BASE_DIR = "/home/ec2-user/whatsapp-meta-bot"
USER_LOG_CSV = os.path.join(BASE_DIR, "user_activity_log.csv")
REMINDED_USERS_CSV = os.path.join(BASE_DIR, "reminded_users.csv")

# Meta WhatsApp API config
ACCESS_TOKEN = "EAAHjsQJx72sBO9ZByRXWONteoZBSA1ZAGgAj0TB1xrY95P5LhZAVZAw6Q931i11tx61MeF1aETJn253ZBPuvWEhsif2hQUEAZC5ZBZBB4Uj7Nhf9gterpvSCAamY5J2DSK8ZC6k1ZCXMiMYejJaz6ZCSQr6N80fBsrb2GZBKMKrEHG04gGYy0CUyXuXzD"
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/625896810607603/messages"

# Ensure files exist
if not os.path.exists(USER_LOG_CSV):
    with open(USER_LOG_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Customer Number", "Timestamp", "Step", "Info"])

if not os.path.exists(REMINDED_USERS_CSV):
    with open(REMINDED_USERS_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Customer Number", "Date"])

def today_ist_str():
    return datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d")

def get_reminded_today():
    today = today_ist_str()
    reminded = set()
    with open(REMINDED_USERS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Date"] == today:
                reminded.add(row["Customer Number"])
    return reminded

def send_text_message(to, message):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print(f"✅ Reminder sent to {to}: {r.status_code}")

def send_cart_reminders_if_inactive():
    ist = timezone("Asia/Kolkata")
    now = datetime.now(ist)
    reminded = get_reminded_today()
    last_log = {}

    with open(USER_LOG_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            phone = row["Customer Number"]
            step = row["Step"]
            ts_str = row["Timestamp"]
            if step in ["catalog_shown", "cart ordered"]:
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").astimezone(ist)
                    if phone not in last_log or ts > last_log[phone]:
                        last_log[phone] = ts
                except:
                    continue

    # Send reminder if last interaction was > 30 minutes ago
    to_remind = []
    for phone, ts in last_log.items():
        if phone in reminded:
            continue
        if now - ts > timedelta(minutes=30):
            to_remind.append(phone)

    if not to_remind:
        print("ℹ️ No users to remind.")
        return

    with open(REMINDED_USERS_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        for phone in to_remind:
            cart_items = get_user_cart(phone)  # You need to implement this
            if not cart_items:
                print(f"📭 {phone} has an empty cart.")
                continue  # Skip sending reminder

            cart_str = "\n".join(cart_items) if isinstance(cart_items, list) else str(cart_items)
            print(f"🔔 Reminding {phone} with cart:\n{cart_str}\n")

            send_text_message(phone, "🛒 You were checking out our menu earlier. Don’t miss out! Complete your order now 🍧")
            writer.writerow([phone, today_ist_str()])

            
if __name__ == "__main__":
    send_cart_reminders_if_inactive()
