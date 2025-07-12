# utils/operational_hours_utils.py

from datetime import datetime, time
from pytz import timezone  # ✅ Correct import
from services.whatsapp_service import send_text_message


def is_store_open():
    """Check if current time is within business hours"""
    ist = timezone('Asia/Kolkata')
    now = datetime.now(ist).time()
    
    # Store open hours (adjust as needed)
    open_time = time(9, 0)     # 9:00 AM IST
    close_time = time(23, 0)   # 10:00 PM IST
    
    return open_time <= now <= close_time


def handle_off_hour_message(sender):
    """Store user who messaged during off-hours"""
    if not is_store_open():
        from stateHandlers.redis_state import add_off_hour_user
        add_off_hour_user(sender)
        send_text_message(sender, "🕒 We're currently closed. Please come back between 9:00 AM and 10:00 PM IST.")