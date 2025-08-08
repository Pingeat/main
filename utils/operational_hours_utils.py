# utils/operational_hours_utils.py

from datetime import datetime, time
from pytz import timezone  # ✅ Correct import
from config.settings import CLOSE_TIME, OPEN_TIME
from services.whatsapp_service import send_text_message
from utils.time_utils import get_current_ist


def is_store_open():
    """Check if current time is within business hours"""
    ist = timezone('Asia/Kolkata')
    now = get_current_ist().time()
    
    # Store open hours (adjust as needed)
    open_time = time(OPEN_TIME, 0)     # 9:00 AM IST
    close_time = time(CLOSE_TIME, 0)   # 10:00 PM IST
    print(open_time)
    print(close_time)
    print(now)
    
    return open_time <= now <= close_time


def handle_off_hour_message(sender):
    """Store user who messaged during off-hours"""
    if not is_store_open():
        from stateHandlers.redis_state import add_off_hour_user
        add_off_hour_user(sender)
        send_text_message(sender, f"🕒 We're currently closed. Please come back between {OPEN_TIME} AM and {11} PM IST.")