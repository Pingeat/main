import json
import re
import os
import requests
from flask import Flask, request
from geopy.distance import geodesic
import googlemaps
import uuid
import pytz
from datetime import datetime, timedelta, time ,date
import csv
from pytz import timezone
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import threading
from threading import Timer
app = Flask(__name__)

# Meta Credentials
ACCESS_TOKEN = "EAATaFWgHXb0BO8ucf8KUDZBZAM1GDHvoWisAup5FcFGa7RBxVTzr4itefw03XBOdZBBDfJHpl3VgnB7M0dmbGCJaokzRQnbDBftkIUTuyb5TQfIuwF726GMgRaLeSUfpi8i5s0zy3Q6FTlTqc3qqoxozGq7GxSkh1B8fweFFTuj5ZABFZClK0ztf6ZCqm9FH9Vo1l4x1KaDZBitZBWmZA3XHkhS9sjHWqnz4lMAsZD"

PHONE_NUMBER_ID = "648035701730540"
VERIFY_TOKEN = "pine_eat123"
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

# Google Maps API
gmaps = googlemaps.Client(key="AIzaSyCuUz9N78WZAT1N38ffIDkbySI3_0zkZgE")
ORDERS_CSV = "orders.csv"
if not os.path.exists(ORDERS_CSV):
    with open(ORDERS_CSV, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Order ID", "Customer Number", "Order Time", "Branch", "Address", "Latitude", "Longitude",
            "Summary", "Total", "Payment Mode", "Paid", "Status"
        ])
# Branch Info
FEEDBACK_CSV = "feedback.csv"
if not os.path.exists(FEEDBACK_CSV):
    with open(FEEDBACK_CSV, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Customer Number", "Order ID", "Rating", "Comment", "Timestamp"])
PROMO_LOG_CSV = "promo_sent_log.csv"
if not os.path.exists(PROMO_LOG_CSV):
    with open(PROMO_LOG_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Phone Number", "Promo Name", "Date Sent"])

USER_LOG_CSV = "user_activity_log.csv"
if not os.path.exists(USER_LOG_CSV):
    with open(USER_LOG_CSV, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Customer Number", "Timestamp", "Step", "Info"])
OFF_HOUR_USERS_CSV = "offhour_users.csv"

if not os.path.exists(OFF_HOUR_USERS_CSV):
    with open(OFF_HOUR_USERS_CSV, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Phone Number", "Date"])
BRANCHES = {
    "Kondapur": (17.47019976442252, 78.35272372527311),
    "Madhapur": (17.452121157758043, 78.39433952527278),
    "Manikonda": (17.403904212354316, 78.39079508109451),
    "Nizampet": (17.502920525682562, 78.38792555189266),
    "Nanakramguda": (17.428344716608002, 78.33321245767164)
}

BRANCH_LINKS = {
    "Kondapur": "https://maps.app.goo.gl/E26sm634cKJmxktH6",
    "Madhapur": "https://maps.app.goo.gl/x5AHBgoh3gMbhUobA",
    "Manikonda": "https://maps.app.goo.gl/FkCU71kfvKY2vrgw9",
    "Nizampet": "https://maps.app.goo.gl/4sfipqkgwdjHLFDe6",
    "Nanakramguda": "https://maps.app.goo.gl/tQrS9Bpg524kpXadA"
}
BRANCH_DISCOUNTS = {
    "kondapur": 0,
    "madhapur": 0,
    "manikonda": 0,
    "nizampet": 0,
    "nanakramguda": 0
}


BRANCH_CONTACTS = {
    "Kondapur": "918885112242",
    "Madhapur": "917075442898",
    "Manikonda": "919441112671",
    "Nizampet": "6303241076",
    "Nanakramguda": "6303237242"
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
RAZORPAY_KEY_ID = "rzp_live_jtGMQ5k5QGHxFg"
RAZORPAY_KEY_SECRET = "FEMHAO4zeUFnAiKZPLe44NRN"
CART_PRODUCTS = {
    "d6t8psx9pj": {"name": "Watermelon juice (200ml)", "price": 80},
    "e96hotbrrk": {"name": "Mini Dry fruit loaded Fruit Custard Party pack of 9", "price": 1125},
    "epw4m28e9h": {"name": "Ice Pops (orange) Pack of 3", "price": 110},
    "h4mp4plkzc": {"name": "Apricot Delight", "price": 180},
    "itpyabj48o": {"name": "Vanilla Choco Chip Milk Shake", "price": 140},
    "lnhbm0ehx6": {"name": "Flavoured Oatmeal (strawberry) (Mini) 200gms", "price": 180},
    "o6q3i0rr8l": {"name": "Mango Custard ice cream 320 gms", "price": 160},
    "p0n0vdrw1o": {"name": "Apricot Delight Pack of 6", "price": 1140},
    "qfltyzlwug": {"name": "Velvety Yogurt Exotic Bowl", "price": 169},
    "tes7p8mfoq": {"name": "Peanut Butter Almond Oat Meal (Regular) 320 gms", "price": 190},
    "u3br5gha5j": {"name": "Flavoured Oatmeal (strawberry) (Regular) 320 gms", "price": 220},
    "u4ib6dq70z": {"name": "Peanut Butter Almond Oat Meal (Mini) 200gms", "price": 165},
    "vfgefdp635": {"name": "Watermelon Bowl With In-house Seasoning", "price": 130},
    "x38sma5k1u": {"name": "Ice Pops (khus)", "price": 40},
    "xxrnoiq4vb": {"name": "Ice Pops (blueberry)", "price": 40},
    "25veup0sh3": {"name": "Dry Fruit Loaded Fruit Custard Family Pack", "price": 470},
    "5uxk2s844f": {"name": "Lays Grilled Sandwich And Apricot Delight", "price": 300},
    "bdrmb8zzn6": {"name": "Only ABC Cold Pressed Juice pack of 12", "price": 2160},
    "cdbpeeepnu": {"name": "Reg Exotic Fruit Custard Party pack of 6", "price": 1080},
    "gev34pdrky": {"name": "Kulfi (falooda) Pack of 3", "price": 225},
    "gfry76hl69": {"name": "Ice Pops (orange) Pack of 6", "price": 180},
    "ihabkdxqi1": {"name": "Plain Oat Shake", "price": 130},
    "knajj4zzjb": {"name": "Velvety Yogurt Tropical Bowl", "price": 169},
    "l7e8g7sgqv": {"name": "Kulfi (rabdi) Pack of 6", "price": 400},
    "lk853dvzr2": {"name": "Strawberry Delight", "price": 180},
    "o33sdwwe1a": {"name": "Melony Mix Bowl (250gm)", "price": 119},
    "rwomk3bsai": {"name": "Strawberry delight Pack of 6", "price": 1140},
    "th6k9g6xpc": {"name": "Fruit Custard Jumbo Pack", "price": 800},
    "umqwusp9j8": {"name": "Kulfi (falooda) Pack of 6", "price": 400},
    "zc2tgagcat": {"name": "Dry Fruit Loaded Fruit Custard Jumbo Pack", "price": 920},
    "2cx3eh3owc": {"name": "Fruit Pop Oat Shake", "price": 180},
    "4689vavywz": {"name": "Veg Classic Sandwich And Fruit Custard Mini", "price": 220},
    "78v9l1s68a": {"name": "Snickers Milk Shake", "price": 175},
    "8mql5cwl5d": {"name": "Ice Pops (mango)", "price": 40},
    "8owbt3yw4k": {"name": "Only Pineapple (300ml)", "price": 199},
    "9s5x0sgnge": {"name": "Mixed Dry Fruit Oat Shake", "price": 200},
    "j87k34ewdq": {"name": "Blueberry delight Pack of 9", "price": 1665},
    "jw4eervpno": {"name": "Ice Pops (litchi) Pack of 6", "price": 180},
    "lihvfypfsd": {"name": "Nutty Custard Ice Cream 320 gms", "price": 140},
    "ltywl4ukfp": {"name": "Mango delight Pack of 9", "price": 1665},
    "o36z1zzg0b": {"name": "Only Muskmelon (300ml)", "price": 179},
    "t16bmhu225": {"name": "Ice Pops (litchi)", "price": 40},
    "vivph2c06y": {"name": "Lemon Delight", "price": 180},
    "zh5jysafl0": {"name": "Exotic Fruit Oatmeal (Regular) 320 gms", "price": 230},
    "12ucbvthmg": {"name": "Fruit And Nut Oatmeal (Regular) 320 gms", "price": 230},
    "4hya66uz82": {"name": "Pineapple Bowl With In-house Seasoning", "price": 130},
    "d5z3swd3ax": {"name": "Only Pineapple Cold Pressed Juice pack of 12", "price": 2160},
    "hbjt7vmbcc": {"name": "Flavoured Oatmeal (blueberry) (Mini) 200gms", "price": 180},
    "hf0y1iys5z": {"name": "Kulfi (rabdi) Pack of 3", "price": 225},
    "jberl4egar": {"name": "Strawberry delight Pack of 9", "price": 1665},
    "k781owtuz1": {"name": "Mini Exotic Fruit Custard Party pack of 6", "price": 900},
    "mrrmr9az6o": {"name": "Only ABC Cold Pressed Juice pack of 6", "price": 1140},
    "sdj4lxso5o": {"name": "Exotic Fruit Custard Family Pack", "price": 450},
    "w8fdfwtjf1": {"name": "Dry Fruit Loaded Oatmeal (Regular) 320 gms", "price": 210},
    "whlw4bng3f": {"name": "Kulfi (sitafal)", "price": 80},
    "wuhdm2k38f": {"name": "Ice Pops (khus) Pack of 6", "price": 180},
    "y0dyye8x5e": {"name": "Exotic Fruit Custard Jumbo Pack", "price": 820},
    "ykj82xsqsr": {"name": "Watermelon Bowl (250gm)", "price": 89},
    "zfzrgbudhb": {"name": "Fruit Pop Oatmeal (Regular) 320 gms", "price": 190},
    "2s85wta86m": {"name": "Peanut Butter Almond Oat Shake", "price": 180},
    "3qp88yzjik": {"name": "All combo delight box Pack of 6", "price": 1140},
    "8og5doc6h8": {"name": "Classic Fruit Custard Family Pack", "price": 420},
    "9kmhjhbksi": {"name": "Strawberry delight Pack of 12", "price": 2160},
    "a9293wzsj2": {"name": "Flavoured Oat Shake (blueberry)", "price": 170},
    "aznsqf32mh": {"name": "Exotic Fruit Oatmeal (Mini) 200gms", "price": 210},
    "hitdk27ljd": {"name": "Exotic fruit custard mini (200 gms)", "price": 150},
    "mp3f1514lw": {"name": "Ice Pops (blueberry) Pack of 3", "price": 110},
    "t1kvjc4hwa": {"name": "Only Watermelon (300ml)", "price": 169},
    "t4585pu56e": {"name": "Banana Date Milkshake 300ml", "price": 199},
    "to4wu3pxmg": {"name": "Ice Pops (mango) Pack of 6", "price": 180},
    "tzvw41yie3": {"name": "Classic Fruit Custard Jumbo Pack", "price": 870},
    "xxewgtdqhw": {"name": "Lemon delight Pack of 9", "price": 1665},
    "yl6gj33ap4": {"name": "Fruit And Nut Oatmeal (Mini) 200gms", "price": 190},
    "zpnr3bos4e": {"name": "Dry Fruit Loaded Custard Bowl 320 gms", "price": 180},
    "2a4oqwos71": {"name": "Only Orange (300ml)", "price": 199},
    "77i76pl51n": {"name": "All combo delight box Pack of 9", "price": 1665},
    "7nj883rvpn": {"name": "Plain Oatmeal (Mini) 200gms", "price": 130},
    "8hknec1qb1": {"name": "Classic Fruit Bowl (250gm)", "price": 149},
    "9mra3y6tf2": {"name": "Ice Pops (blueberry) Pack of 6", "price": 180},
    "d01kfnn5pk": {"name": "Only Watermelon (200ml)", "price": 89},
    "fdtc6qrnom": {"name": "Nutty Custard Ice Cream 200 gms", "price": 125},
    "joj33wx95z": {"name": "Mini Fruit Custard Party pack of 6", "price": 720},
    "l4dodoasg2": {"name": "Muskmelon (250gm)", "price": 89},
    "sq8527sojq": {"name": "Mango delight Pack of 6", "price": 1140},
    "upgkzse5p9": {"name": "Lemon delight Pack of 6", "price": 1140},
    "vrwc3y7xk4": {"name": "Kulfi (mango) Pack of 6", "price": 400},
    "wmlxqphh7d": {"name": "ONLY ABC juice (200ml)", "price": 119},
    "x3dbvez2po": {"name": "Fruit Custard Regular (320 gms)", "price": 150},
    "x8uhfo0psp": {"name": "Mini Dry fruit loaded Fruit Custard Party pack of 6", "price": 780},
    "3xjdktafu7": {"name": "ONLY pomegranate (300ml)", "price": 209},
    "486s3ca09j": {"name": "Dry Fruit Loaded Oatmeal (Mini) 200gms", "price": 180},
    "5y37wnqw16": {"name": "Alphonso Mango Loaded Oatmeal (Regular)320 gms", "price": 230},
    "c5qphx91t7": {"name": "Fruit And Nut Oat Shake", "price": 190},
    "fiemkps8wp": {"name": "Exotic Fruit Bowl (250gm)", "price": 199},
    "jcodu49xd6": {"name": "Fruit Custard With Ice Cream 200 gms", "price": 140},
    "kgllut7iud": {"name": "Kulfi (rabdi)", "price": 80},
    "l569p1zqnm": {"name": "Choco Banana Date Milkshake 200ml", "price": 159},
    "mkfk56hhd1": {"name": "Classic Fruit Custard 200 gms", "price": 140},
    "tidjkafgwc": {"name": "Blueberry Delight", "price": 180},
    "uuyqppjpkh": {"name": "Oreo Milk Shake And Veg Classic Sandwich", "price": 220},
    "xmg12kw3tm": {"name": "Veg classic sandwich", "price": 130},
    "yx99llesmu": {"name": "Only Pineapple Cold Pressed Juice pack of 8", "price": 1480},
    "z6hsxd8rqe": {"name": "Choco Walnut Date oatmeal mini (200 gms)", "price": 170},
    "zqq6nlmbum": {"name": "Banana Date Milkshake 200ml", "price": 149},
    "1vaa5pnm3q": {"name": "Dry Fruit Loaded Custard Bowl 200 gms", "price": 150},
    "71s90lhj49": {"name": "Banana Milkshake 200ml", "price": 129},
    "7fzuvqmyuw": {"name": "Choco banana oatmeal Regular (320 gms)", "price": 200},
    "8zzqnjtc55": {"name": "Fruit Custard With Ice Cream 320 gms", "price": 170},
    "bfme21ugl8": {"name": "Only Orange Cold Pressed Juice pack of 8", "price": 1480},
    "cl09f3np9i": {"name": "Reg Dry fruit loaded Fruit Custard Party pack of 6", "price": 1020},
    "ig7p3u4z87": {"name": "Oreo Milk Shake", "price": 130},
    "sn07q6svbt": {"name": "Choco banana Oatshake (200ml)", "price": 150},
    "tbm1nub1bt": {"name": "Kulfi (sitafal) Pack of 6", "price": 400},
    "u0nykwxomb": {"name": "ONLY pomegranate (200ml)", "price": 129},
    "u77haau894": {"name": "Lemon delight Pack of 12", "price": 2160},
    "vv4k31g8h1": {"name": "Avocado Milkshake 200ml", "price": 149},
    "xd29s7lq67": {"name": "Nutella Brownie Milk Shake", "price": 180},
    "xtz9i7cwe6": {"name": "Dark Chocolate sandwich", "price": 155},
    "yflkxfroj9": {"name": "Mini Exotic Fruit Custard Party pack of 9", "price": 1305},
    "0rzbquqzp5": {"name": "All combo delight box Pack of 12", "price": 2160},
    "0xmibvnbm8": {"name": "Only ABC Cold Pressed Juice pack of 8", "price": 1480},
    "0z1bbrnlww": {"name": "Reg Dry fruit loaded Fruit Custard Party pack of 12", "price": 1920},
    "1themn2guc": {"name": "Classic Fruit Custard 320 gms", "price": 170},
    "2d52v5prl8": {"name": "Exotic fruit custard Regular (320 gms)", "price": 180},
    "2tgihrjsex": {"name": "Ice Pops (orange)", "price": 40},
    "4r62e0fsee": {"name": "Choco Banana Date Milkshake 300ml", "price": 209},
    "6acj93502p": {"name": "Only Pineapple Cold Pressed Juice pack of 6", "price": 1140},
    "c0mhw60110": {"name": "Papaya (250gm)", "price": 99},
    "hn626kjink": {"name": "Kitkat Milk Shake", "price": 160},
    "jc27bjdu5x": {"name": "Banana Milkshake 300ml", "price": 169},
    "ld4rv5xznd": {"name": "Blueberry delight Pack of 6", "price": 1140},
    "r5vl54hf54": {"name": "Plain Oatmeal (Regular) 320 gms", "price": 180},
    "t01hwe5kzm": {"name": "Avocado Milkshake 300ml", "price": 199},
    "y41nvi8tou": {"name": "Reg Fruit Custard Party pack of 12", "price": 1680},
    "09ju2d1lcd": {"name": "Blueberry delight Pack of 12", "price": 2160},
    "7unazvrcts": {"name": "Reg Exotic Fruit Custard Party pack of 12", "price": 2040},
    "bgzo09erts": {"name": "Fruit Custard Mini (200 gms)", "price": 120},
    "byeqv941gx": {"name": "Flavoured Oat Shake (strawberry)", "price": 170},
    "eorkz2rwun": {"name": "Choco banana oatmeal mini (200 gms)", "price": 150},
    "fa23x697wc": {"name": "Lemon Honey Exotic Bowl", "price": 149},
    "hnyc3cci8c": {"name": "Lemon Honey Tropical Bowl", "price": 149},
    "lt25muno78": {"name": "Only Orange (200ml)", "price": 119},
    "lwtyl17xe1": {"name": "Kulfi (sitafal) Pack of 3", "price": 225},
    "lxcvzpwlt5": {"name": "Choco Walnut Date oatmeal Regular (320 gms)", "price": 230},
    "mkp2spxrxc": {"name": "Kulfi (mango) Pack of 3", "price": 225},
    "smj4ep1m7k": {"name": "Only Pineapple (200ml)", "price": 119},
    "vs52l0oe19": {"name": "Mini Fruit Custard Party pack of 9", "price": 1035},
    "vv87dbnjg5": {"name": "Only Muskmelon (200ml)", "price": 109},
    "xifo751de6": {"name": "Ice Pops (mango) Pack of 3", "price": 110},
    "01p7segtly": {"name": "Only Orange Cold Pressed Juice pack of 12", "price": 2160},
    "33t41zm1q4": {"name": "Alphonso Oatshake", "price": 220},
    "5dx35kd54a": {"name": "Ice Pops (cola)", "price": 40},
    "5hkkniy9n9": {"name": "Only Orange Cold Pressed Juice pack of 6", "price": 1140},
    "8npd890dhm": {"name": "Fruit Pop Oatmeal (Mini) 200gms", "price": 165},
    "9ltr4gfu69": {"name": "Ice Pops (litchi) Pack of 3", "price": 110},
    "d4ntl809gj": {"name": "Ice Pops (cola) Pack of 6", "price": 180},
    "fbrbibtpas": {"name": "Apricot Delight Pack of 12", "price": 2160},
    "gzflfdjf27": {"name": "Fruit Custard Family Pack (600 gms)", "price": 400},
    "ljaf7767cu": {"name": "Ice Pops (khus) Pack of 3", "price": 110},
    "lmxd75c0iz": {"name": "Choco Loaded Brownie", "price": 130},
    "qmfcxq1mh7": {"name": "Apricot Delight Pack of 9", "price": 1665},
    "u87nizhzn0": {"name": "ONLY ABC juice (300ml)", "price": 199},
    "vbxf92t9jx": {"name": "Mango delight Pack of 12", "price": 2160},
    "wakjywaod9": {"name": "Flavoured Oatmeal (blueberry) (Regular) 320 gms", "price": 220},
    "29eayslnan": {"name": "Kulfi (mango)", "price": 80},
    "61ntywnsqq": {"name": "Pineapple (250gm)", "price": 99},
    "6cheekv111": {"name": "Lays grilled sandwich", "price": 150},
    "7l5e6j0660": {"name": "Mango Custard ice cream 200 gms", "price": 135},
    "h9pzzwwljd": {"name": "Alphonso Mango Loaded Oatmeal (Mini) 200gms", "price": 210},
    "t43q2vesev": {"name": "Ice Pops (cola) Pack of 3", "price": 110},
    "y1pg71g4dh": {"name": "Reg Fruit Custard Party pack of 6", "price": 900},
    "zw4j4j0p8q": {"name": "Mango Delight", "price": 180}
}

user_cart = {}
user_feedback_state = {}
user_states = {}

KITCHEN_NUMBERS = ["917671011599"]
def generate_order_id():
    return f"ORD-{uuid.uuid4().hex[:6].upper()}"
# Send a regular text message
def log_user_activity(phone, step, info=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(USER_LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([phone, timestamp, step, info])
def get_current_ist_time():
    ist = timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

def is_operational_hours():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).time()
    return time(9, 0) <= now <= time(23, 45)
def store_off_hour_user(phone_number):
    with open(OFF_HOUR_USERS_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([phone_number, str(date.today())])
import requests

ACCESS_TOKEN = "EAAHjsQJx72sBO9ZByRXWONteoZBSA1ZAGgAj0TB1xrY95P5LhZAVZAw6Q931i11tx61MeF1aETJn253ZBPuvWEhsif2hQUEAZC5ZBZBB4Uj7Nhf9gterpvSCAamY5J2DSK8ZC6k1ZCXMiMYejJaz6ZCSQr6N80fBsrb2GZBKMKrEHG04gGYy0CUyXuXzD"
PHONE_NUMBER_ID = "625896810607603"

def send_pay_online_template(phone_number, payment_link):
    """
    Sends WhatsApp button using 'pays_online' template.
    Razorpay link format: https://rzp.io/rzp/{{1}}
    So we must extract only the token: 'q3PfGjX0'
    """
    # Extract only the token part from Razorpay link
    if payment_link.startswith("https://rzp.io/rzp/"):
        token = payment_link.split("/")[-1]
    else:
        token = payment_link  # fallback in case it's already trimmed

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "pays_online",  # ✅ your correct template name
            "language": { "code": "en_US" },
            "components": [
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": 0,
                    "parameters": [
                        { "type": "text", "text": token }  # ✅ send only the token like 'q3PfGjX0'
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent Razorpay payment button:", response.status_code, response.text)
    return response
def clean_message_text(text, max_len=250):
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"[^\x20-\x7E₹]+", "", text)  # allow only safe ASCII + ₹
    return text.strip()[:max_len]
import requests
import json


def send_catalog_set(phone, retailer_product_id):
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": "set_cat",  # ✅ Your approved template name
            "language": { "code": "en_US" },
            "components": [
                {
                    "type": "button",
                    "sub_type": "CATALOG",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "action",
                            "action": {
                                "thumbnail_product_retailer_id": retailer_product_id  # e.g., "tidjkafgwc"
                            }
                        }
                    ]
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
    print("📦 Sent catalog set:", response.status_code, response.text)
def send_marketing_promo1(phone_number, message_text):
    cleaned_message = clean_message_text(message_text)
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "promo_mark",  # Your correct template name
            "language": { "code": "en_US" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": cleaned_message }
                    ]
                }
                # ❌ No need to send header if it's static
                # ❌ No need to send footer component if it's static
            ]
        }
    }

    print("📦 Payload:", json.dumps(payload, indent=2))
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent promo message:", response.status_code, response.text)

def send_marketing_promo2(phone_number, message_text):
    cleaned_message = clean_message_text(message_text)
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "promo_marketing_p",
            "language": { "code": "en_US" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": cleaned_message }
                    ]
                }
            ]
        }
    }
    print("📦 Payload:", json.dumps(payload, indent=2))
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent promo message:", response.status_code, response.text)
def send_marketing_promo(phone_number, message_text):
    cleaned_message = clean_message_text(message_text)
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "promo_marketing",
            "language": { "code": "en_US" },
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {
                                "link": "https://thefruitcustard.com/auto.png"
                            }
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": cleaned_message }
                    ]
                }
            ]
        }
    }

    print("📦 Payload:", json.dumps(payload, indent=2))
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent promo message:", response.status_code, response.text)



def send_kitchen_branch_alert_template(
    phone_number, order_type, order_id, customer, order_time,
    item_summary, total, branch, address, location_url
):
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "kitchen_branch_alert",
            "language": { "code": "en_US" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": order_type },
                        { "type": "text", "text": order_id },
                        { "type": "text", "text": customer },
                        { "type": "text", "text": order_time },
                        { "type": "text", "text": item_summary },
                        { "type": "text", "text": str(total) },
                        { "type": "text", "text": branch },
                        { "type": "text", "text": address },
                        { "type": "text", "text": location_url }
                    ]
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent kitchen/branch alert:", response.status_code, response.text)

def save_feedback(phone_number, rating):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_id = user_cart.get(phone_number, {}).get("order_id", "")
    comment = ""  # No comment in quick replies, only rating

    with open("feedback.csv", mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([phone_number, order_id, rating, comment, timestamp])

def schedule_feedback(to_number):
    def delayed_feedback():
        send_feedback_template(to_number)
    Timer(1800, delayed_feedback).start() 
def send_feedback_template(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "feedback_2",  # your actual template name
            "language": { "code": "en_US" }
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent feedback quick reply template:", response.status_code, response.text)


def send_open_reminders():
    print("⏰ Running morning reminder scheduler...")

    today = str(datetime.now(timezone('Asia/Kolkata')).date())
    sent_to = set()
    new_rows = []

    if not os.path.exists(OFF_HOUR_USERS_CSV):
        return

    with open(OFF_HOUR_USERS_CSV, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Date"] == today:
                phone = row["Phone Number"]
                if phone not in sent_to:
                    send_text_message(phone, "🌞 Good morning! We’re now open and ready to take your orders. 🍧")
                    sent_to.add(phone)
            else:
                # Keep entries not belonging to today
                new_rows.append(row)

    # Overwrite file with only today/future entries
    with open(OFF_HOUR_USERS_CSV, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Phone Number", "Date"])
        writer.writeheader()
        writer.writerows(new_rows)
def send_cart_reminder_once():
    print("⏰ Running cart reminder + cleanup scheduler...")

    ist = timezone('Asia/Kolkata')
    now = datetime.now(ist)
    to_delete = []

    for phone, cart in list(user_cart.items()):
        last_time_raw = cart.get("last_interaction_time")
        reminder_sent = cart.get("reminder_sent", False)
        address = cart.get("address")

        if last_time_raw:
            try:
                if isinstance(last_time_raw, datetime):
                    last_time = last_time_raw
                else:
                    last_time = datetime.strptime(last_time_raw, "%Y-%m-%d %H:%M:%S")
                    last_time = ist.localize(last_time)
            except Exception as e:
                print("⚠️ Error parsing last interaction time:", e)
                continue

            # 🗑️ Cart cleanup after 1 day
            if now - last_time > timedelta(days=1):
                print(f"🗑️ Deleting abandoned cart for {phone}")
                to_delete.append(phone)

            # 🛒 Send reminder if no address and reminder not sent
            elif now - last_time > timedelta(minutes=5) and cart.get("summary") and not address and not reminder_sent:
                send_text_message(phone, "🛒 Just a reminder! You still have items in your cart. Complete your order with delivery or takeaway. 😊")
                user_cart[phone]["reminder_sent"] = True

    for phone in to_delete:
        del user_cart[phone]

def send_cart_reminder(sender):
    cart = user_cart.get(sender, {})
    if not cart or not cart.get("items"):
        return  # No items in cart, no reminder needed

    reminder_message = "🛒 You still have items in your cart! Don’t forget to complete your order!"

    # Add details of items in the cart (optional)
    for item in cart.get("items", []):
        item_id = item["item_id"]
        qty = item["qty"]
        item_name = CART_PRODUCTS.get(item_id, {}).get("name", "Unknown Item")
        reminder_message += f"\n{item_name} x{qty}"

    reminder_message += "\nComplete your order now! 😊"

    # Generate payment link (if not already done)
    order_id = cart.get("order_id")
    total = cart.get("total", 0)
    payment_link = generate_payment_link(sender, total, order_id)

    reminder_message += f"\n🔗 Pay Now: {payment_link}"

    # Send reminder message to the user
    send_text_message(sender, reminder_message)
def generate_payment_link(to, total, order_id):
    cart = user_cart.get(to, {})
    existing_payment_link = cart.get("payment_link")
    last_final_total = cart.get("final_total")

    # ✅ Regenerate if total changed or link missing
    if existing_payment_link and last_final_total == total:
        print(f"🔁 Reusing existing payment link: {existing_payment_link}")
        return existing_payment_link

    url = "https://api.razorpay.com/v1/payment_links"
    payload = {
        "amount": total * 100,  # in paise
        "currency": "INR",
        "accept_partial": False,
        "reference_id": order_id,
        "description": "Fruit Custard Order",
        "customer": {
            "name": "Fruit Custard Customer",
            "contact": f"+91{to[-10:]}",
            "email": f"{order_id.lower()}@fruitcustard.com"
        },
        "notify": {
            "sms": True,
            "email": False
        },
        "reminder_enable": True,
        "callback_url": "https://5942-13-51-167-208.ngrok-free.app/orders.csv",
        "callback_method": "get"
    }

    response = requests.post(url, auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET), json=payload)
    data = response.json()
    payment_link = data.get("short_url")
    
    user_cart[to]["payment_link"] = payment_link
    user_cart[to]["final_total"] = total  # ✅ store new total to compare next time

    print("🔗 Razorpay new link:", payment_link)
    return payment_link


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
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("✅ Sent text:", response.status_code, response.text)

# Send greeting template

def send_greeting_template(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "fruitcustard_greeting",
            "language": { "code": "en_US" }
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent greeting template:", response.status_code, response.text)

# Send catalog template
def notify_customer_status_update(to, order_id, status):
    message = (
        f"📦 Update on your order *{order_id}*:\n"
        f"Your order is now marked as *{status}*.\n"
        f"Thank you for choosing Fruit Custard! 🍧"
    )
    send_text_message(to, message)

def log_order_to_csv(order_id, customer_number, order_time, branch, address,latitude, longitude, summary, total, payment_mode, paid, status):
    file_exists = os.path.isfile(ORDERS_CSV)
    latitude = user_cart.get(customer_number, {}).get("latitude", "")
    longitude = user_cart.get(customer_number, {}).get("longitude", "")
    with open(ORDERS_CSV, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Order ID", "Customer Number", "Order Time", "Branch", "Address", "Latitude", "Longitude", 
            "Summary", "Total", "Payment Mode", "Paid", "Status"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Order ID": order_id,
            "Customer Number": customer_number,
            "Order Time": order_time,
            "Branch": branch,
            "Address": address,
            "Latitude": latitude,
            "Longitude": longitude,
            "Summary": summary,
            "Total": total,
            "Payment Mode": payment_mode,
            "Paid": paid,
            "Status": status
        })

def update_order_status(order_id, new_status):
    updated = False
    order_id = order_id.strip().upper()

    temp_rows = []
    found = False

    with open(ORDERS_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print("Checking against:", row["Order ID"].strip().upper())  # DEBUG
            if row["Order ID"].strip().upper() == order_id:
                found = True
                row["Status"] = new_status
                customer = row["Customer Number"]
                message = f"📦 Your order *{order_id}* status is now *{new_status}*."
                send_text_message(customer, message)
            temp_rows.append(row)

    if not found:
        print("❌ Order not found in CSV")

    # Overwrite file
    with open(ORDERS_CSV, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=temp_rows[0].keys())
        writer.writeheader()
        writer.writerows(temp_rows)

    return found
def confirm_order(to, branch, order_id, payment_mode, paid=False):
    cart = user_cart.get(to, {})
    summary = cart.get("summary", "No items found.")
    total = cart.get("total", 0)

    # ✅ Discount logic
    branch_key = branch.lower()
    discount_percent = BRANCH_DISCOUNTS.get(branch_key, 0)
    discount_amount = (total * discount_percent) // 100
    final_total = total - discount_amount
    user_cart[to]["final_total"] = final_total  # Store for Razorpay use

    # ✅ Add discount info to summary
    if discount_percent > 0:
        summary += f"\n\n💸 *{discount_percent}% Discount Applied*: -₹{discount_amount}"
    summary += f"\n💰 *Total Payable*: ₹{final_total}"

    address = cart.get("address", "N/A")
    latitude = cart.get("latitude", "")
    longitude = cart.get("longitude", "")
    contact = BRANCH_CONTACTS[branch]
    branch_location_link = BRANCH_LINKS[branch]
    customer_location_link = f"https://www.google.com/maps?q={latitude},{longitude}" if latitude and longitude else "N/A"
    order_time = get_current_ist_time()
    customer_number = to

    status_line = "✅ Payment received." if paid else "💵 Payment Mode: Cash on Delivery"

    # ✅ Sanitize summary and address
    item_summary_clean = summary.replace("\n", " | ").replace("\t", " ").replace("  ", " ").replace("*", "").strip()[:250]
    address_clean = address.replace("\n", " ").replace("\t", " ").replace("  ", " ").strip()[:250]

    # ✅ Log to CSV
    log_order_to_csv(
        order_id=order_id,
        customer_number=customer_number,
        order_time=order_time,
        branch=branch,
        address=address,
        latitude=latitude,
        longitude=longitude,
        summary=summary,
        total=final_total,
        payment_mode=payment_mode,
        paid=paid,
        status="Pending"
    )

    # ✅ Message to customer
    customer_msg = (
        f"🧾 *Order Confirmed!*\n"
        f"🆔 Order ID: {order_id}\n\n"
        f"{summary}\n"
        f"{status_line}\n"
        f"🕒 Time: {order_time}\n\n"
        f"🏪 Branch: {branch}\n"
        f"📍 {branch_location_link}\n"
        f"📞 Contact us if any changes: {contact}"
        f"👨‍🍳 Your food is getting ready! We’ll deliver it to you as soon as possible. 🚚💨"
    )
    send_text_message(to, customer_msg)

    # ✅ Alert to branch contact
    send_kitchen_branch_alert_template(
        phone_number=contact,
        order_type=payment_mode,
        order_id=order_id,
        customer=customer_number,
        order_time=order_time,
        item_summary=item_summary_clean,
        total=final_total,
        branch=branch,
        address=address_clean,
        location_url=customer_location_link
    )

    # ✅ Alert to kitchen team(s)
    for kitchen in KITCHEN_NUMBERS:
        send_kitchen_branch_alert_template(
            phone_number=kitchen,
            order_type=payment_mode,
            order_id=order_id,
            customer=customer_number,
            order_time=order_time,
            item_summary=item_summary_clean,
            total=final_total,
            branch=branch,
            address=address_clean,
            location_url=customer_location_link
        )

    user_cart[to]["reminder_sent"] = True
    log_user_activity(to, "order confirmed")


    


def send_delivery_takeaway_template(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "delivery_takeaway",
            "language": { "code": "en_US" }
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent delivery/takeaway template:", response.status_code, response.text)
def send_payment_option_template(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "pay_now",  # ✅ corrected to match your real template name
            "language": { "code": "en_US" }
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent payment option template:", response.status_code, response.text)

def send_full_catalog(to):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "catalog_message",
            "body": {
                "text": "🍧 Explore our full Fruit Custard menu!"
            },
            "action": {
                "name": "catalog_message",  # ✅ REQUIRED
                "catalog_id": "1050974620414013"  # ✅ Your actual catalog ID
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📦 Sent full catalog message:", response.status_code, response.text)

def handle_location(sender, latitude, longitude):
    user_coords = (float(latitude), float(longitude))
    print(f"📍 Location received: {user_coords}")

    for branch, coords in BRANCHES.items():    
        distance_km = geodesic(user_coords, coords).km
        if distance_km <= 2:
            branch_key = branch.lower()

            # ✅ Check if branch is closed
            if not BRANCH_STATUS.get(branch_key, True):
                send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed. We’ll notify you when it reopens.")
                BRANCH_BLOCKED_USERS[branch_key].add(sender)
                log_user_activity(sender, f"branch_closed_attempt: {branch}")
                return

            print(f"✅ User is within {distance_km:.2f} km of {branch}")
            send_text_message(sender, f"🎉 We can deliver to you from our {branch} branch!\n📍 {BRANCH_LINKS[branch]}")

            user_cart[sender] = user_cart.get(sender, {})
            user_cart[sender]["branch"] = branch
            user_cart[sender]["latitude"] = latitude
            user_cart[sender]["longitude"] = longitude
            discount = BRANCH_DISCOUNTS.get(branch.lower(), 0)
            if discount > 0:
                send_text_message(sender, f"🎉 *Congratulations!* You’ve unlocked a *{discount}% discount*. It will be auto-applied at checkout. 🎁")

            send_delivery_takeaway_template(sender)

            user_states[sender] = {"step": "catalog_shown", "branch": branch}
            log_user_activity(sender, "catalog_shown")
            return

    send_text_message(sender, "❌ Sorry, we currently don’t deliver to your area. Stay tuned as we expand!")
    user_states[sender] = {"step": "start"}





@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    try:
        payload = request.get_data(as_text=True)
        data = request.get_json()

        print("📥 Webhook payload received:", data)

        if data.get("event") == "payment_link.paid":
            payment_data = data.get("payload", {}).get("payment_link", {}).get("entity", {})
            whatsapp_number = payment_data.get("customer", {}).get("contact")
            order_id = payment_data.get("reference_id")

            if whatsapp_number and order_id:
                phone = f"91{whatsapp_number[-10:]}"
                cart_data = user_cart.get(phone)
                if cart_data:
                    confirm_order(
                        to=phone,
                        branch=cart_data["branch"],
                        order_id=cart_data["order_id"],
                        payment_mode="Online",
                        paid=True
                    )
                    user_cart[phone].pop("payment_link", None)
                    user_cart[phone].pop("final_total", None)
                    return "✅ Order confirmed", 200
        return "Ignored", 200
    except Exception as e:
        print("🚨 Webhook error:", e)
        return "Error", 500

@app.route("/download-user-log")
def download_user_log():
    from flask import send_file
    return send_file("user_activity_log.csv", as_attachment=True)
@app.route("/payment-success", methods=["GET"])
def payment_success():
    # In real scenario, validate signature from Razorpay
    whatsapp_number = request.args.get("whatsapp")
    order_id = request.args.get("order_id")

    if whatsapp_number and order_id:
        data = user_cart.get(whatsapp_number)
        if data:
            confirm_order(
                to=whatsapp_number,
                branch=data["branch"],
                order_id=data["order_id"],
                payment_mode="Online",
                paid=True
            )
            user_cart[whatsapp_number].pop("payment_link", None)
            user_cart[whatsapp_number].pop("final_total", None)

    return "Payment confirmed", 200

# Main webhook route
# Main webhook route

@app.route("/webhook", methods=["POST"])
def webhook():
    import csv

    ORDERS_CSV = "orders.csv"  # Ensure this exists or is created by order logger

    data = request.get_json()
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                if not messages:
                    continue

                msg = messages[0]
                sender = msg.get("from")
                text = msg.get("text", {}).get("body", "").strip().lower()
                button_text = msg.get("button", {}).get("text", "").strip().lower()
                now_str = get_current_ist_time()
                if sender not in user_cart:
                    user_cart[sender] = {}
                user_cart[sender]["last_interaction_time"] = now_str
                send_cart_reminder_once()
                latitude = msg.get("location", {}).get("latitude")
                longitude = msg.get("location", {}).get("longitude")

                print("📩 From:", sender)
                print("💬 Text:", text)
                print("🔘 Button:", button_text)
                if not is_operational_hours():
                    send_text_message(sender, "⏰ We are currently closed. Please come back between 9:00 AM and 11:45 PM IST.")
                    store_off_hour_user(sender)
                    return "Closed hours", 200
                if any(text.startswith(cmd) for cmd in ["open", "close"]):
                	parts = text.split()
                	if len(parts) == 2:
                		action, branch_name = parts
                		branch_key = branch_name.strip().lower()
                		if branch_key not in BRANCH_STATUS:
                			send_text_message(sender, f"⚠️ Unknown branch: {branch_name}. Valid options: kondapur, madhapur, manikonda, nizampet, nanakramguda")
                			return "OK", 200
                		if action == "open":
                			BRANCH_STATUS[branch_key] = True
                			send_text_message(sender, f"✅ Branch *{branch_name.title()}* is now *open* for delivery.")
                			for user in BRANCH_BLOCKED_USERS[branch_key]:
                				send_text_message(user, f"📣 Our *{branch_name.title()}* branch is now open! You can place your order again. 🎉")
                			BRANCH_BLOCKED_USERS[branch_key].clear()
                		elif action == "close":
                			BRANCH_STATUS[branch_key] = False
                			send_text_message(sender, f"🚫 Branch *{branch_name.title()}* is now *closed* for delivery.")
                		return "OK", 200
                	else:
                		send_text_message(sender, "❗ To open/close a branch, use:\nopen madhapur\nclose kondapur")
                		return "OK", 200


                # 🎯 MARKETING: message customer "<text>" item_set=SetName to=number1,number2
                if text.startswith("message customer"):
                    match = re.search(r'to=(.*?)\s+message_text="(.*?)"(?:\s+item_set=(\S+))?', text)
                    if match:
                        to_value = match.group(1).strip()
                        message_text = match.group(2).strip()
                        item_set = match.group(3).strip() if match.group(3) else "none"
                        item_set = item_set.replace('"', '').strip()
                        print(f"Extracted item_set: {item_set}")
                        if to_value in ["log", "all"]:
                            unique_numbers = set()
                            try:
                                with open(USER_LOG_CSV, newline='') as f:
                                    reader = csv.DictReader(f)
                                    for row in reader:
                                        num = row["Customer Number"].strip()
                                        if num.isdigit() and len(num) >= 10:
                                            unique_numbers.add(num)
                            except Exception as e:
                                print("🚨 Error reading log CSV:", e)
                                send_text_message(sender, "❌ Failed to read customer numbers from log.")
                                return "OK", 200
                            for number in unique_numbers:
                                send_marketing_promo(number, message_text)
                                if item_set.lower() != "none":
                                    send_catalog_set(number, item_set)
                            send_text_message(sender, f"✅ Promo sent to {len(unique_numbers)} unique customers from log.")
                        else:
                            numbers = [n.strip() for n in to_value.split(",") if n.strip()]
                            for number in numbers:
                                send_marketing_promo(number, message_text)
                                if item_set.lower() != "none":
                                    send_catalog_set(number, item_set)
                            send_text_message(sender, f"✅ Promo message sent to {len(numbers)} customer(s).")
                    else:
                        send_text_message(sender, "❗ Invalid format. Use:\nmessage customer to=... message_text=\"your message here\"")
                    return "OK", 200
                   

     


                # ✅ Handle order status updates
                status_keywords = ["ready", "preparing", "ontheway", "delivered", "cancelled"]
                if any(text.startswith(k) for k in status_keywords):
                    parts = text.split()
                    if len(parts) == 2:
                        new_status, order_id = parts
                        order_id = order_id.strip().upper()
                        new_status_clean = new_status.strip().capitalize()
                        if new_status_clean.lower() == "ontheway":
                            new_status_clean = "On the Way"
                            
                        updated = False
                        updated_rows = []


                        # Read and update CSV
                        with open(ORDERS_CSV, "r", newline='', encoding="utf-8") as infile:
                            reader = csv.DictReader(infile)
                            for row in reader:
                                if row["Order ID"].strip().upper() == order_id:
                                    row["Status"] = new_status
                                    updated = True

                                    customer_number = row["Customer Number"].strip()
                                    if customer_number:
                                        send_text_message(customer_number, f"📦 Your order *{order_id}* is now *{new_status_clean}*.")
                                        if new_status_clean.lower() == "delivered":
                                            schedule_feedback(customer_number)
                                            

                                updated_rows.append(row)


                                    

                        if updated:
                            with open(ORDERS_CSV, "w", newline='', encoding="utf-8") as outfile:
                                fieldnames = list(updated_rows[0].keys())
                                writer = csv.DictWriter(outfile, fieldnames=updated_rows[0].keys())
                                writer.writeheader()
                                for row in updated_rows:
                                    clean_row = {key: row.get(key, "") for key in fieldnames}
                                    writer.writerow(clean_row)
                            
                            
                            send_text_message(sender, f"✅ Order *{order_id}* marked as *{new_status_clean}*.")

                            
                        else:
                            send_text_message(sender, f"⚠️ Order ID *{order_id}* not found.")
                    else:
                        send_text_message(sender, "❗ To update order status, use:\nready ORD-XXXXXX")
                    return "OK", 200


      

                # Handle live location
                if latitude and longitude:
                    handle_location(sender, latitude, longitude)
                    log_user_activity(sender, "location")
                    return "OK", 200

                # Handle typed address if waiting for location
                if user_states.get(sender, {}).get("step") == "awaiting_location" and text:
                    try:
                        geocode = gmaps.geocode(text)
                        if geocode:
                            location = geocode[0]["geometry"]["location"]
                            latitude = location["lat"]
                            longitude = location["lng"]
                            print(f"📍 Address '{text}' resolved to: ({latitude}, {longitude})")
                            handle_location(sender, latitude, longitude)
                        else:
                            send_text_message(sender, "❌ Couldn’t find that location. Please try again.")
                            user_states[sender] = {"step": "start"}
                    except Exception as e:
                        print("🚨 Geocode error:", e)
                        send_text_message(sender, "⚠️ Error finding your area. Please try again.")
                        user_states[sender] = {"step": "start"}
                    return "OK", 200
                quick_reply_ratings = {"5- outstanding": "5", "4- excellent": "4", "3 – good": "3", "2 – average": "2", "1 – poor": "1"}
                if button_text in quick_reply_ratings:
                    rating_value = quick_reply_ratings[button_text]
                    save_feedback(sender, rating_value)
                    send_text_message(sender, "🙏 Thanks for your feedback!")
                    return "OK", 200
                # Address after Pay Now / COD
                if user_states.get(sender, {}).get("step") == "awaiting_address":
                    address = text
                    action = user_states[sender]["action"]
                    branch = user_cart.get(sender, {}).get("branch", "Kondapur")
                    order_id = user_cart[sender].get("order_id")
                    if not order_id:
                        order_id = generate_order_id()
                        user_cart[sender]["order_id"] = order_id
                    user_cart[sender]["address"] = address

                    if action == "cod (cash on delivery)":
                        confirm_order(sender, branch, order_id, payment_mode="COD", paid=False)
                    elif action == "pay now":
                        total = user_cart[sender].get("total", 0)
                        order_id = user_cart[sender].get("order_id")
                        if not order_id:
                            order_id = generate_order_id()
                            user_cart[sender]["order_id"] = order_id
                        branch = user_cart.get(sender, {}).get("branch", "Kondapur")
                        branch_key = branch.lower()
                        discount_percent = BRANCH_DISCOUNTS.get(branch_key, 0)
                        discount_amount = (total * discount_percent) // 100
                        final_total = total - discount_amount
                        user_cart[sender]["final_total"] = final_total
                        discount_message = ""
                        if discount_percent > 0:
                            discount_message = f"🎉 You're getting *{discount_percent}% OFF*! That's ₹{discount_amount} saved.\n"
                        send_text_message(sender, f"{discount_message}⏳ Generating your payment link... Please wait a moment.")
                        payment_link = generate_payment_link(sender, final_total, order_id)
                        #send_text_message(sender, f"💳 Please complete your payment:\n🔗 {payment_link}")
                        user_cart[sender].update({
                            "order_id": order_id,
                            "branch": branch,
                            "payment_link": payment_link
                        })
                        send_pay_online_template(sender, payment_link)
                    
                    user_states[sender] = {"step": "start"}
                    return "OK", 200
                if "discount" in text:
                    parts = text.split()
                    if len(parts) == 3:
                        branch_name, keyword, value = parts
                        branch_key = branch_name.strip().lower()
                        if branch_key in BRANCH_DISCOUNTS and keyword == "discount":
                            try:
                                BRANCH_DISCOUNTS[branch_key] = int(value)
                                send_text_message(sender, f"✅ Discount for *{branch_name.title()}* branch set to {value}%.")
                            except:
                                send_text_message(sender, "❗ Invalid discount value. Use a number.")
                        else:
                            send_text_message(sender, "❗ Unknown branch or format.")
                    else:
                        send_text_message(sender, "❗ Use format: `kondapur discount 10` or `madhapur discount 0`")
                    return "OK", 200


                # Greeting
                if text in ["hi", "hello", "hey", "menu"]:
                    send_greeting_template(sender)

                    log_user_activity(sender, "greeting")

                elif button_text == "order now":
                    send_full_catalog(sender)
                    log_user_activity(sender, "catalog sent")
                    return "OK", 200

                elif button_text == "subscriptions":
                    send_text_message(sender, "📦 For subscriptions, message us here: https://wa.me/918688641919?text=I%20am%20looking%20for%20juices%2C%20oatmeals%20or%20fruit%20bowl%20subscription")

                elif button_text == "party orders":
                    send_text_message(sender, "🎉 For party orders, message us here: https://wa.me/918688641919?text=I%20am%20looking%20for%20a%20bulk%20order")

                elif button_text == "delivery":
                    send_payment_option_template(sender)
                    return "OK", 200

                elif button_text in ["cod (cash on delivery)", "pay now"]:
                    user_states[sender] = {
                        "step": "awaiting_address",
                        "action": button_text
                    }
                    send_text_message(sender, "🏠 Please enter your full delivery address:")
                    return "OK", 200

                elif button_text == "takeaway":
                    branch = user_cart.get(sender, {}).get("branch", "Kondapur")
                    order_id = user_cart[sender].get("order_id")
                    if not order_id:
                        order_id = generate_order_id()
                        user_cart[sender]["order_id"] = order_id
                    cart = user_cart.get(sender, {})
                    summary = cart.get("summary", "No items found.")
                    total = cart.get("total", 0)

                    
                    user_cart[sender]["branch"] = branch
                    user_cart[sender]["address"] = "Takeaway"

                    confirm_order(sender, branch, order_id, payment_mode="Takeaway", paid=False)
                    user_states[sender] = {"step": "start"}
                    return "OK", 200

                elif msg.get("type") == "order":
                    order_info = msg.get("order", {})
                    log_user_activity(sender, "cart ordered")
                    product_items = order_info.get("product_items", [])

                    total = 0
                    items_list = []

                    for item in product_items:
                        prod_id = item.get("product_retailer_id")
                        qty = item.get("quantity", 1)

                        if prod_id in CART_PRODUCTS:
                            product = CART_PRODUCTS[prod_id]
                            name = product["name"]
                            price = product["price"]
                            subtotal = price * qty
                            total += subtotal
                            items_list.append(f"{name} x{qty} = ₹{subtotal}")

                    summary = "\n".join(items_list)
                    user_cart[sender] = user_cart.get(sender, {})
                    user_cart[sender].update({
                        "summary": summary,
                        "total": total,
                        "order_id": generate_order_id() 
                    })

                    print(f"🛒 Cart from {sender}:\n{summary}\n💰 Total: ₹{total}")
                    branch = user_cart.get(sender, {}).get("branch", "").lower()
                    discount = BRANCH_DISCOUNTS.get(branch, 0)
                    if discount > 0:
                        send_text_message(sender, f"🎉 *Congratulations!* You’ve unlocked a *{discount}% discount*. It will be auto-applied at checkout. 🎁")

                    send_text_message(sender, "📍 Please *share your Current location* to check delivery availability.")
                    user_states[sender] = {"step": "awaiting_location"}
                    return "OK", 200

    except Exception as e:
        print("🚨 Error:", e)
    return "OK", 200
@app.route("/download-feedback")
def download_feedback():
    from flask import send_file
    return send_file("feedback.csv", as_attachment=True)


@app.route("/download-orders")
def download_orders():
    from flask import send_file
    return send_file("orders.csv", as_attachment=True)
# Meta Webhook Verification
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == "ping_eat123":
        return challenge, 200
    return "Verification failed", 403
def start_scheduler():
    scheduler = BackgroundScheduler(timezone='Asia/Kolkata')

    # Morning Open Reminder (daily at 9:00 AM IST)
    scheduler.add_job(send_open_reminders, 'cron', hour=9, minute=0)

    # Cart Reminder + Auto-Cleanup (every 10 minutes)
    scheduler.add_job(send_cart_reminder_once, 'interval', minutes=10)

    scheduler.start()
    print("✅ Scheduler started and running...")

if __name__ == "__main__":
    start_scheduler()
    
    app.run(host="0.0.0.0", port=10000)