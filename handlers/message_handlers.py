# handlers/message_handlers.py

from services.whatsapp_service import send_text_message
from utils.logger import log_user_activity

def handle_incoming_message(data):
    print("[MESSAGE HANDLER] Received data:", data)
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

                log_user_activity(sender, "message_received", text)

                if "hi" in text or "hello" in text:
                    send_text_message(sender, "Welcome to Fruit Custard!")
    except Exception as e:
        print("[ERROR] Error handling message:", e)