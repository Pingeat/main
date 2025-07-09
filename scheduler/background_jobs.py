# scheduler/background_jobs.py

from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from services.order_service import send_cart_reminder_once, send_open_reminders
from services.whatsapp_service import send_text_message
from stateHandlers.redis_state import get_pending_orders, remove_pending_order, update_pending_order_reminders

def start_scheduler():
    print("[SCHEDULER] Starting job scheduler...")
    scheduler = BackgroundScheduler(timezone='Asia/Kolkata')
    scheduler.add_job(send_open_reminders, 'cron', hour=9, minute=0)
    scheduler.add_job(send_cart_reminder_once, 'interval', minutes=10)
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