# handlers/webhook_handler.py

from flask import Blueprint, request, jsonify
from handlers.message_handlers import handle_incoming_message

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    print("[WEBHOOK] Incoming POST request received.")
    data = request.get_json()
    handle_incoming_message(data)
    return jsonify({"status": "OK"}), 200

@webhook_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    print("[WEBHOOK] Verifying token...")
    hub_mode = request.args.get("hub.mode")
    hub_token = request.args.get("hub.verify_token")
    hub_challenge = request.args.get("hub.challenge")

    if hub_mode == "subscribe" and hub_token == "pine_eat123":
        print("[WEBHOOK] Verification successful.")
        return hub_challenge, 200
    else:
        print("[WEBHOOK] Verification failed.")
        return "Verification failed", 403