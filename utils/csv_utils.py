# utils/csv_utils.py

import os
import csv

from config.settings import (
    ORDERS_CSV,
    FEEDBACK_CSV,
    USER_LOG_CSV,
    OFF_HOUR_USERS_CSV,
    PROMO_LOG_CSV
)

def initialize_csv_files():
    if not os.path.exists(ORDERS_CSV):
        with open(ORDERS_CSV, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Order ID", "Customer Number", "Order Time", "Branch", "Address", "Latitude", "Longitude",
                "Summary", "Total", "Payment Mode", "Paid", "Status"
            ])

    if not os.path.exists(FEEDBACK_CSV):
        with open(FEEDBACK_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Customer Number", "Order ID", "Rating", "Comment", "Timestamp"])

    if not os.path.exists(USER_LOG_CSV):
        with open(USER_LOG_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Customer Number", "Timestamp", "Step", "Info"])

    if not os.path.exists(OFF_HOUR_USERS_CSV):
        with open(OFF_HOUR_USERS_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Phone Number", "Date"])

    if not os.path.exists(PROMO_LOG_CSV):
        with open(PROMO_LOG_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Phone Number", "Promo Name", "Date Sent"])

initialize_csv_files()