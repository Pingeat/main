# services/whatsapp_service.py

import json
import re
import requests
from config.credentials import CATALOG_ID_FOR_MATCHED_ITEMS, META_ACCESS_TOKEN, WHATSAPP_API_URL, META_PHONE_NUMBER_ID
from config.settings import BRANCHES, DATES

def send_text_message(to, message):
    print(f"[WHATSAPP] Sending message to {to}")
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
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print(f"[WHATSAPP] Status: {response.status_code}")
    return response

def send_greeting_template(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "fruitcustard_greeting",
            "language": {"code": "en_US"}
        }
    }
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print(f"[WHATSAPP] Greeting sent: {response.status_code}")

def send_delivery_takeaway_template(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "delivery_takeaway",
            "language": {"code": "en_US"}
        }
    }
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print(f"[WHATSAPP] Delivery/Takeaway template sent: {response.status_code}")

def send_payment_option_template(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "pay_now",
            "language": {"code": "en_US"}
        }
    }
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print(f"[WHATSAPP] Payment option sent: {response.status_code}")


def send_pay_online_template(phone_number, payment_link):
    """
    Sends payment button via WhatsApp using 'pays_online' template.
    """
    token = payment_link.split("/")[-1] if payment_link.startswith("https://rzp.io/rzp/")  else payment_link

    url = f"https://graph.facebook.com/v19.0/{META_PHONE_NUMBER_ID}/messages" 
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "pays_online",
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": 0,
                    "parameters": [
                        {"type": "text", "text": token}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"[WHATSAPP] Payment link sent. Status: {response.status_code}")

def send_full_catalog(to):
    """
    Sends the full catalog message via WhatsApp.
    Assumes a pre-configured catalog ID.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "catalog_message",
            "body": {
                "text": "🍓 Explore our full Fruit Custard menu!"
            },
            "action": {
                "name": "catalog_message",
                "catalog_id": "1008650128092617"  
            },
        }
    }
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print(f"[WHATSAPP] Full catalog sent. Status: {response}")
    
def send_selected_catalog_items(to,selected_items):
    """
    Send only selected items from your catalog.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "product_list",
            "header": {
            "type": "text",
            "text": "Your Selected Items"
            },
            "body": {
                "text": "🍓 Here are some similar products!!"
            },
            "footer": {
            "text": "View details below"
            },
            "action": {
                "catalog_id": CATALOG_ID_FOR_MATCHED_ITEMS,
                "sections": [
                    {
                        "title": "Products",
                        "product_items": [
                            {"product_retailer_id": id}
                            for id in selected_items
                        ]
                    }
                ]
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print(f"[WHATSAPP] Sent selected items. Status: {response.status_code}, Response: {response.text}")
    
    
def send_rakhi_products(to):
    """
    Send only Rakhi products from catalog 
    """

    # product id's
    rakhi_product_ids = [
        "51jetppvov", "oici2ap1qd", 
        "5hfaymh61s", "8olxnu3afk",
        "aadudpumcb", "40llavglo4",
        "jykbu2a2ez", "9l89g0ezc9",
        "gvil23bxf8", "ygeeysblx2",
        "eyl9q23h7m", "mo1hlc617k",
        "p6kuuli1n6"
    ]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "product_list",
            "header": {
                "type": "text",
                "text": "Rakhi Special 🎁"
            },
            "body": {
                "text": "💖 Celebrate Raksha Bandhan with our handpicked Rakhis!"
            },
            "footer": {
                "text": "Tap to view and order"
            },
            "action": {
                "catalog_id": CATALOG_ID_FOR_MATCHED_ITEMS,  
                "sections": [
                    {
                        "title": "Rakhi Collection ❤️",
                        "product_items": [
                            {"product_retailer_id": pid}
                            for pid in rakhi_product_ids
                        ]
                    }
                ]
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print(f"[WHATSAPP] Sent Rakhi products. Status: {response.status_code}, Response: {response.text}")

   
def send_branch_selection_message(to):
    """Send branch selection message using interactive list template"""

    # Create sections for the list
    sections = [{
        "title": "Select Branch",
        "rows": [
            {"id": branch, "title": branch.title(), "description": ""} 
            for branch in BRANCHES
        ]
    }]
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "🏢 SELECT YOUR BRANCH"
            },
            "body": {
                "text": "Please select a branch close to your location:"
            },
            "footer": {
                "text": "Tap to select your branch"
            },
            "action": {
                "button": "Select Branch",
                "sections": sections
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Branch selection error: {response.text}")
        return response
    except Exception as e:
        print(f"Failed to send branch selection: {str(e)}")
        return None


def send_date_selection_message(to):
    """Send date selection message using interactive list template"""

    sections = [{
        "title": "Select date",
        "rows": [
            {
                "id": date,       
                "title": date,     
                "description": ""
            } 
            for date in DATES
        ]
    }]
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "🗓️ SELECT YOUR DELIVERY DATE"
            },
            "body": {
                "text": "Please select your delivery date:"
            },
            "footer": {
                "text": "Tap to select your date"
            },
            "action": {
                "button": "Select date",
                "sections": sections
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Date selection error: {response.text}")
        return response
    except Exception as e:
        print(f"Failed to send date selection: {str(e)}")
        return None



def send_kitchen_branch_alert_template(phone_number, order_type, order_id, customer, order_time, item_summary, total, branch, address, location_url): 
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
                        { "type": "text", "text": item_summary},
                        { "type": "text", "text": str(total) },
                        { "type": "text", "text": branch },
                        { "type": "text", "text": address },
                        { "type": "text", "text": location_url }
                    ]
                }
            ]
        }
    }
    print("[KITCHEN_PARAMETERS] : ",payload)

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent kitchen/branch alert:", response.status_code, response.text)

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
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    print("📤 Sent feedback quick reply template:", response.status_code, response.text)

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
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
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
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
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
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        print(f"[SEND] Marketing promo to {phone_number}: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Failed to send promo to {phone_number}: {str(e)}")
        return False

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
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
    print("📦 Sent catalog set:", response.status_code, response.text)

def clean_message_text(text, max_len=250):
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"[^\x20-\x7E₹]+", "", text)  # allow only safe ASCII + ₹
    return text.strip()[:max_len]
