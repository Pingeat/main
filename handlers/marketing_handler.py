# handlers/message_handlers.py

import re
from stateHandlers.redis_state import get_all_carts
from services.whatsapp_service import send_marketing_promo, send_catalog_set, send_text_message

def handle_marketing_message(sender, text):
    """
    Handle marketing messages sent via admin commands
    Example: message customer to=all message_text="Special offer!" item_set=Desserts
    """
    # Extract parameters using regex
    match = re.search(r'to=(.*?)\s+message_text="(.*?)"(?:\s+item_set=(\S+))?', text)
    
    if not match:
        send_text_message(sender, "❗ Invalid format. Use:\nmessage customer to=... message_text=\"your message here\"")
        return False

    to_value = match.group(1).strip()
    message_text = match.group(2).strip()
    item_set = match.group(3).strip() if match.group(3) else "none"
    item_set = item_set.replace('"', '').strip()
    
    # Get recipients based on target
    if to_value in ["log", "all"]:
        # Get active customers from Redis
        carts = get_all_carts()
        recipients = set(carts.keys())
        
        if not recipients:
            send_text_message(sender, "❌ No active customers found in Redis carts")
            return False
            
        send_text_message(sender, f"📢 Sending promo to {len(recipients)} customers from cart data...")
    
    else:
        # Parse specific numbers
        recipients = [n.strip() for n in to_value.split(",") if n.strip()]
        if not recipients:
            send_text_message(sender, "❌ No valid phone numbers provided")
            return False
    
    # Send messages to all recipients
    successful = 0
    for recipient in recipients:
        try:
            # 🎯 Send marketing template
            send_marketing_promo(recipient, message_text)
            
            # 📦 Send catalog set if specified
            if item_set.lower() != "none":
                send_catalog_set(recipient, item_set)
                
            successful += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to send to {recipient}: {str(e)}")
            continue

    # ✅ Confirm delivery to admin
    send_text_message(sender, f"✅ Sent marketing message to {successful}/{len(recipients)} customers")
    return True