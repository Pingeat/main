# utils/payment_utils.py

import requests
from config.credentials import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

def generate_payment_link(to, total, order_id):
    url = "https://api.razorpay.com/v1/payment_links" 
    payload = {
        "amount": total * 100,
        "currency": "INR",
        "reference_id": order_id,
        "description": "Fruit Custard Order",
        "customer": {
            "name": "Customer",
            "contact": f"+91{to[-10:]}"
        },
        "callback_url": "https://yourdomain.com/callback", 
        "callback_method": "get"
    }
    response = requests.post(url, auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET), json=payload)
    return response.json().get("short_url")