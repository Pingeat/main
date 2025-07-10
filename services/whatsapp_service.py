# services/whatsapp_service.py

import requests
from config.credentials import META_ACCESS_TOKEN, WHATSAPP_API_URL, META_PHONE_NUMBER_ID

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
                "catalog_id": "1225552106016549",
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