# services/order_service.py

import csv
import os
from datetime import datetime
from pytz import timezone

from config.settings import ORDERS_CSV

# Global cart (simulate state)
user_cart = {}

def log_order_to_csv(order_data):
    print("[ORDER SERVICE] Logging order to CSV...")
    file_exists = os.path.isfile(ORDERS_CSV)
    with open(ORDERS_CSV, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=order_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(order_data)
    print("[ORDER SERVICE] Order logged successfully.")


# These were missing earlier — now added!
def send_cart_reminder_once():
    print("[REMINDER] Running cart reminder + cleanup...")


def send_open_reminders():
    print("[REMINDER] Running morning open reminders...")

# Make sure to expose both functions
__all__ = ['send_cart_reminder_once', 'send_open_reminders']