# config/settings.py

ORDERS_CSV = "orders.csv"
FEEDBACK_CSV = "feedback.csv"
USER_LOG_CSV = "user_activity_log.csv"
OFF_HOUR_USERS_CSV = "offhour_users.csv"
PROMO_LOG_CSV = "promo_sent_log.csv"

KITCHEN_NUMBERS = ["9640112005","8074301029","8885112242"]
OPEN_TIME = 9
CLOSE_TIME = 23
DISTANCE = 3


# Product Catalog
from pathlib import Path
import json

# Load products from JSON file
CART_PRODUCTS = json.loads((Path(__file__).parent.parent / "data" / "products.json").read_text())
party_orders_link = "https://wa.me/918688641919?text=I%20am%20looking%20for%20a%20bulk%20order"
BRANCHES =["kondapur", "madhapur","manikonda","nizampet","nanakramguda"]
DATES = ["8th August","9th August"]


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

BRANCH_CONTACTS = {
    "kondapur": ["916302588275"],
    "madhapur": ["917075442898"],
    "manikonda": ["919392016847"],
    "nizampet": ["916303241076"],
    "nanakramguda": ["916303237242"]

}


OTHER_NUMBERS = ["919640112005","8885112242", "918074301029"]
ADMIN_NUMBERS = ["919640112005","8885112242", "918074301029"]