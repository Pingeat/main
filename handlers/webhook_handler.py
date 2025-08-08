# handlers/webhook_handler.py

from flask import Blueprint, request, jsonify
from handlers.message_handlers import handle_incoming_message
# from services.order_service import update_order_status
from services.order_service import confirm_order, confirm_order_after_payment
from services.whatsapp_service import send_text_message
from config.credentials import META_VERIFY_TOKEN
from utils import logger

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

    if hub_mode == "subscribe" and hub_token == META_VERIFY_TOKEN :
        print("[WEBHOOK] Verification successful.")
        return hub_challenge, 200
    else:
        print("[WEBHOOK] Verification failed.")
        return "Verification failed", 403

# ✅ Add these for payment handling
@webhook_bp.route("/payment-success", methods=["GET"])
def payment_success():
    from services.order_service import confirm_order
    whatsapp_number = request.args.get("whatsapp")
    order_id = request.args.get("order_id")
    if whatsapp_number and order_id:
        confirm_order(whatsapp_number, "Online", order_id, paid=True)
    return "Payment confirmed", 200

@webhook_bp.route("/razorpay-webhook-tfc", methods=["POST"])
def razorpay_webhook():
    data = request.get_json()
    if data.get("event") == "payment_link.paid":
        payment_data = data.get("payload", {}).get("payment_link", {}).get("entity", {})
        whatsapp_number = payment_data.get("customer", {}).get("contact")
        order_id = payment_data.get("reference_id")
        if whatsapp_number and order_id:
            send_text_message(whatsapp_number, "✅ Your payment is confirmed! Your order is being processed.")
            # Confirm the order
            confirm_order_after_payment(whatsapp_number,order_id)
    return "OK", 200


# @webhook_bp.route("/razorpay-webhook-tfc1", methods=["POST"])
# def razorpay_webhook():
#     """Handle Razorpay payment webhook"""
#     logger.info("Razorpay webhook received.")
#     data = request.get_json()
    
#     if data.get("event") == "payment_link.paid":
#         payment_data = data.get("payload", {}).get("payment_link", {}).get("entity", {})
#         whatsapp_number = payment_data.get("customer", {}).get("contact")
#         order_id = payment_data.get("reference_id")
        
#         if whatsapp_number and order_id:
#             send_text_message(whatsapp_number, "✅ Your payment is confirmed! Your order is being processed.")
#             # Confirm the order
#             confirm_order(whatsapp_number, "Online", order_id, paid=True)
    
#     return "OK", 200


@webhook_bp.route("/download-orders")
def download_orders():
    from flask import send_file
    return send_file("orders.csv", as_attachment=True)

@webhook_bp.route("/download-user-log")
def download_user_log():
    from flask import send_file
    return send_file("user_activity_log.csv", as_attachment=True)

# @webhook_bp.route("/download-orders")
# def download_orders():
#     from flask import send_file
#     return send_file("orders.csv", as_attachment=True)

@webhook_bp.route("/download-offhour")
def download_offhour_users():
    from flask import send_file
    return send_file("offhour_users.csv", as_attachment=True)