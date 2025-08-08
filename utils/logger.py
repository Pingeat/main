# utils/logger.py

import csv
from datetime import datetime
from pytz import timezone
from config.settings import USER_LOG_CSV
from utils.time_utils import get_current_ist

def log_user_activity(phone, step, info=""):
    ist = timezone('Asia/Kolkata')
    timestamp = get_current_ist().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[LOGGER] {phone}: {step} - {info}")
    with open(USER_LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([phone, timestamp, step, info])