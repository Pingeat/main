# config/settings.py

ORDERS_CSV = "orders.csv"
FEEDBACK_CSV = "feedback.csv"
USER_LOG_CSV = "user_activity_log.csv"
OFF_HOUR_USERS_CSV = "offhour_users.csv"
PROMO_LOG_CSV = "promo_sent_log.csv"

KITCHEN_NUMBERS = ["9640112005","8074301029","8885112242"]
OPEN_TIME = 9
CLOSE_TIME = 22
DISTANCE = 3


# Product Catalog
from pathlib import Path
import json

# Load products from JSON file
CART_PRODUCTS = json.loads((Path(__file__).parent.parent / "data" / "products.json").read_text())



BRANCH_DISCOUNTS = {
    "kondapur": 0,
    "madhapur": 0,
    "manikonda": 0,
    "nizampet": 0,
    "nanakramguda": 0
}

BRANCH_STATUS = {
    "kondapur": True,
    "madhapur": True,
    "manikonda": True,
    "nizampet": True,
    "nanakramguda": True
}
BRANCH_BLOCKED_USERS = {
    "kondapur": set(),
    "madhapur": set(),
    "manikonda": set(),
    "nizampet": set(),
    "nanakramguda": set()
}



ADMIN_NUMBERS = ["918074301029","9640112005","8885112242"]