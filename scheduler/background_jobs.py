# scheduler/background_jobs.py

from apscheduler.schedulers.background import BackgroundScheduler
from services.order_service import send_cart_reminder_once, send_open_reminders

def start_scheduler():
    print("[SCHEDULER] Starting job scheduler...")
    scheduler = BackgroundScheduler(timezone='Asia/Kolkata')
    scheduler.add_job(send_open_reminders, 'cron', hour=9, minute=0)
    scheduler.add_job(send_cart_reminder_once, 'interval', minutes=10)
    scheduler.start()
    print("[SCHEDULER] Scheduler started.")