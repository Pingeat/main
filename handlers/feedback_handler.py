


# from threading import Timer
# from services.whatsapp_service import send_feedback_template


# def save_feedback(phone_number, rating):
#     from datetime import datetime
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     order_id = user_cart.get(phone_number, {}).get("order_id", "")
#     comment = ""  # No comment in quick replies, only rating

#     with open("feedback.csv", mode="a", newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)
#         writer.writerow([phone_number, order_id, rating, comment, timestamp])


# def schedule_feedback(to_number):
#     def delayed_feedback():
#         send_feedback_template(to_number)
#     Timer(1800, delayed_feedback).start() 









# handlers/feedback_handler.py
from threading import Timer
from datetime import datetime
from pytz import timezone
import csv
import os
import json
from services.whatsapp_service import send_feedback_template
from stateHandlers.redis_state import add_scheduled_feedback, delete_scheduled_feedfack, get_pending_order, get_pending_orders_for_user, get_scheduled_feedback, set_user_state

# Feedback tracking key
FEEDBACK_SCHEDULED_KEY = "feedback_scheduled:{}"  # phone -> order_id

def save_feedback(phone_number, rating):
    """Save feedback to CSV with proper order context"""
    print(f"[FEEDBACK] Saving feedback from {phone_number}")
    
    # Get scheduled order ID from Redis
    scheduled = get_scheduled_feedback(phone_number)
    order_id = scheduled.decode() if scheduled else None
    
    # Fallback: try to find any recent order
    if not order_id:
        pending_orders = get_pending_orders_for_user(phone_number)
        if pending_orders:
            order_id = next(iter(pending_orders.keys()))
    
    # Get current IST timestamp
    ist = timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
    
    # Create feedback CSV if it doesn't exist
    feedback_file = "feedback.csv"
    file_exists = os.path.isfile(feedback_file)
    
    # Save to CSV
    with open(feedback_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Phone", "Order ID", "Rating", "Comment", "Timestamp"])
        writer.writerow([phone_number, order_id or "", rating, "", timestamp])
    
    # Clean up Redis
    delete_scheduled_feedfack(phone_number)
    
    print(f"[FEEDBACK] Feedback saved for {phone_number}, rating: {rating}")


def schedule_feedback(to_number, order_id=None):
    """Schedule feedback request 30 minutes after order delivery"""
    if not order_id:
        print(f"[ERROR] Cannot schedule feedback - missing order ID")
        return

    def delayed_feedback():
        # Verify order still exists and is delivered
        order_data = get_pending_order(order_id)
        if not order_data or order_data.get("status") != "Delivered":
            print(f"[FEEDBACK] Order {order_id} not delivered. Skipping feedback.")
            return
            
        print(f"[FEEDBACK] Sending feedback request to {to_number}")
        try:
            send_feedback_template(to_number)
            # Store scheduled feedback for reference
            add_scheduled_feedback(to_number, order_id)
            # redis_client.setex(FEEDBACK_SCHEDULED_KEY.format(to_number), 86400, order_id)
        except Exception as e:
            print(f"[ERROR] Failed to send feedback to {to_number}: {e}")

    # Schedule for 30 minutes
    Timer(1800, delayed_feedback).start()
    print(f"[FEEDBACK] Scheduled feedback for {to_number} (30 minutes)")