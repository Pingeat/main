# utils/time_utils.py
import pytz
from datetime import datetime

# Define the timezone once at the top of the module
IST = pytz.timezone('Asia/Kolkata')

def get_current_ist():
    """Return current time in Indian Standard Time"""
    return datetime.now(IST)

def format_ist_datetime(dt=None, format_str="%Y-%m-%d %H:%M:%S"):
    """Format a datetime object in IST format"""
    if dt is None:
        dt = get_current_ist()
    else:
        # Convert to IST if it's not already timezone-aware
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt).astimezone(IST)
        else:
            dt = dt.astimezone(IST)
    
    return dt.strftime(format_str)

def is_business_hours():
    """Check if current time is within business hours (9 AM to 9 PM IST)"""
    now = get_current_ist()
    return 9 <= now.hour < 21
