# scheduler/background_jobs.py

from datetime import datetime, timedelta
import threading
import time
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from services.order_service import send_cart_reminder_once, send_open_reminders
from services.whatsapp_service import send_text_message
from stateHandlers.redis_state import delete_user_cart, get_pending_orders, remove_pending_order, update_pending_order_reminders

def start_scheduler():
    print("[SCHEDULER] Starting job scheduler...")
    scheduler = BackgroundScheduler(timezone='Asia/Kolkata')
    scheduler.add_job(send_open_reminders, 'cron', hour=9, minute=0)
    scheduler.add_job(send_cart_reminders, 'interval', minutes=10)
    # scheduler.add_job(check_pending_orders, 'interval', seconds=30)
    scheduler.start()
    print("[SCHEDULER] Scheduler started.")


def check_pending_orders():
    print("[SCHEDULER] Checking pending orders...")
    pending_orders = get_pending_orders()

    for order_id, order_data in pending_orders.items():
        status = order_data.get("status", "Pending")
        customer = order_data.get("customer")
        reminders_sent = order_data.get("reminders_sent", 0)

        # Skip if order is no longer Pending
        if status != "Pending":
            continue

        if reminders_sent < 6:  # 6 reminders over 3 minutes
            send_text_message(customer, f"⏳ Your order `{order_id}` is still pending. Please confirm with the branch.")
            update_pending_order_reminders(order_id, reminders_sent + 1)
        else:
            # After 3 minutes, cancel the order
            send_text_message(customer, f"❌ Your order `{order_id}` has been cancelled due to inactivity.")
            remove_pending_order(order_id)

def send_cart_reminders():
    """Send cart reminders to users with incomplete orders"""
    print("[SCHEDULER] Checking for cart reminders...")

    from stateHandlers.redis_state import get_all_carts
    carts = get_all_carts()
    print("[PRINTING send_cart_reminders] :", carts)
    
    if not carts:
        print("[SCHEDULER] No carts found.")
        return

    ist = timezone('Asia/Kolkata')
    now = datetime.now(ist)

    for phone, cart in carts.items():
        if not cart:  # Skip None or empty cart
            print(f"[INFO] Cart for {phone} is None. Skipping...")
            continue

        if not cart.get("summary"):
            continue

        if cart.get("reminder_sent", False):
            continue

        last_interaction_time_str = cart.get("last_interaction_time")
        if not last_interaction_time_str:
            print(f"[WARNING] Missing 'last_interaction_time' in cart for {phone}. Skipping reminder.")
            continue

        try:
            # Convert string time back to datetime
            last_time = datetime.strptime(last_interaction_time_str, "%Y-%m-%d %H:%M:%S")
            last_time = ist.localize(last_time)

            # Send reminder after 5 minutes
            if now - last_time > timedelta(minutes=5):
                send_cart_reminder_once(phone)

            # Delete after 24 hours
            if now - last_time > timedelta(days=1):
                from stateHandlers.redis_state import delete_user_cart
                delete_user_cart(phone)
                print(f"[CART] Deleted abandoned cart for {phone}")

        except Exception as e:
            print(f"[ERROR] Failed to process cart for {phone}: {e}")


def check_expired_pending_orders():
    while True:
        try:
            now = datetime.utcnow()
            orders = get_pending_orders()  # Returns all orders from Redis
            for order_id, order_data in orders.items():
                if order_data.get('status') == 'Pending':
                    created_at_str = order_data.get('created_at')
                    if not created_at_str:
                        continue  # Skip if no timestamp

                    created_at = datetime.fromisoformat(created_at_str)
                    if (now - created_at).total_seconds() >= 180:
                        customer_phone = order_data.get('customer')
                        # Send cancellation message
                        send_text_message(
                            customer_phone,
                            f"❌ Your order {order_id} has been cancelled due to inactivity."
                        )
                        # Delete the order
                        remove_pending_order(order_id)
        except Exception as e:
            print(f"[ERROR] Checking expired pending orders: {e}")
        time.sleep(60)  # Run every 60 seconds

# Start the background thread
threading.Thread(target=check_expired_pending_orders, daemon=True).start()