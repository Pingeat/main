# services/whatsapp_service.py

import requests
from config.credentials import META_ACCESS_TOKEN, WHATSAPP_API_URL

def send_text_message(to, message):
    print(f"[WHATSAPP] Sending message to {to}: {message[:30]}...")
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
    print(f"[WHATSAPP] Message sent. Status code: {response.status_code}")