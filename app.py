# app.py

from flask import Flask
from handlers.webhook_handler import webhook_bp
from scheduler.background_jobs import start_scheduler

print("[APP] Initializing WhatsApp bot...")

app = Flask(__name__)
app.register_blueprint(webhook_bp)

if __name__ == "__main__":
    print("[APP] Starting scheduler and Flask server...")
    start_scheduler()
    app.run(host="0.0.0.0", port=10000,debug=True)