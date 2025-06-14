# utils/payment_utils.py

import requests
import logging
from config.credentials import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_payment_link(to, total, order_id):
    """
    Generates a Razorpay payment link for a customer.
    
    Args:
        to (str): WhatsApp number of the customer
        total (float): Total amount to be paid
        order_id (str): Unique order ID
    
    Returns:
        str: Shortened Razorpay payment link or None if failed
    """
    url = "https://api.razorpay.com/v1/payment_links" 
    
    # Ensure total is a positive number
    if total <= 0:
        logger.error("Invalid total amount: %s", total)
        return None

    payload = {
        "amount": int(total * 100),  # Convert to paise
        "currency": "INR",
        "accept_partial": False,
        "reference_id": order_id,
        "description": "Fruit Custard Order",
        "customer": {
            "name": "Customer",
            "contact": f"+91{to[-10:]}"
        },
        "notify": {
            "sms": True,
            "email": False
        },
        "reminder_enable": True,
        "callback_url": "https://yourdomain.com/razorpay-webhook", 
        "callback_method": "get"
    }

    try:
        response = requests.post(
            url,
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        short_url = data.get("short_url")
        
        if short_url:
            logger.info("Payment link generated: %s", short_url)
        else:
            logger.error("Failed to generate payment link: %s", data.get("error", "No short URL returned"))
        
        return short_url
    except requests.exceptions.RequestException as e:
        logger.exception("Error generating Razorpay link: %s", str(e))
        return None