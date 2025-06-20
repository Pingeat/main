# services/order_service.py

import os
import csv
import uuid
import json
from datetime import datetime
from pathlib import Path
from pytz import timezone
from config.settings import ORDERS_CSV, KITCHEN_NUMBERS
from services.whatsapp_service import send_text_message,  send_kitchen_branch_alert_template

def log_order_to_csv(order_data):
    print("[ORDER SERVICE] Logging order...")
    file_exists = os.path.isfile(ORDERS_CSV)
    with open(ORDERS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=order_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(order_data)

def send_open_reminders():
    print("[REMINDER] Sending morning open alerts...")
    # Implement daily open alerts here

def send_cart_reminder_once():
    print("[REMINDER] Sending cart reminders...")
    # Implement cart cleanup and reminders here

def confirm_order(to, branch, order_id, payment_mode, user_cart,paid=False):
    print("HIIIIIIIIIIIIIIIIIII")
    cart = user_cart.get(to, {})
    summary = cart.get("summary", "")
    total = cart.get("total", 0)

    # branch_key = branch.lower()
      # Load branches from JSON
    branches_data = json.loads((Path(__file__).parent.parent / "data" / "branches.json").read_text())
    # try:
    #     with open(branches_path, "r") as f:
    #         branches_data = json.load(f)
    # except (FileNotFoundError, json.JSONDecodeError) as e:
    #     print(f"[ERROR] Failed to load branches.json: {e}")
    #     branches_data = {}

    # Get contact
    getContact = branches_data.get(branch, {}).get("contact", "")

    address = cart.get("address", "N/A")
    latitude = cart.get("latitude", "")
    longitude = cart.get("longitude", "")
    contact = getContact
    branch_location_link = branches_data.get(branch, {}).get("map_link", "")
    print(f"[BRANCH_LOCATION]: {branch_location_link}")
    customer_location_link = f"https://www.google.com/maps?q={latitude},{longitude}" if latitude and longitude else "N/A"
    order_time = get_current_ist_time()
    customer_number = to

    status_line = "✅ Payment received." if paid else "💵 Payment Mode: Cash on Delivery"
    print(branches_data)

     # ✅ Sanitize summary and address
    item_summary_clean = summary.replace("\n", " | ").replace("\t", " ").replace("  ", " ").replace("*", "").strip()[:250]
    address_clean = address.replace("\n", " ").replace("\t", " ").replace("  ", " ").strip()[:250]
    
    # Log to CSV
    log_order_to_csv({
        "Order ID": order_id,
        "Customer Number": to,
        "Order Time": get_current_ist_time(),
        "Branch": branch,
        "Address": "Takeaway" if payment_mode == "Takeaway" else "Pending",
        "Summary": summary,
        "Total": total,
        "Payment Mode": payment_mode,
        "Paid": paid,
        "Status": "Pending"
    })

    # ✅ Message to customer
    customer_msg = (
        f"🧾 *Order Confirmed!*\n"
        f"🆔 Order ID: {order_id}\n\n"
        f"{summary}\n"
        f"{status_line}\n"
        f"🕒 Time: {order_time}\n\n"
        f"🏪 Branch: {branch}\n"
        f"📍 {branch_location_link}\n"
        f"📞 Contact us if any changes: {contact}"
        f"👨‍🍳 Your food is getting ready! We’ll deliver it to you as soon as possible. 🚚💨"
    )
    
    # Send confirmation
    send_text_message(to, f"Order confirmed! {customer_msg}")
    
    # Alert kitchen
    for kitchen in KITCHEN_NUMBERS:
        send_kitchen_branch_alert_template(
            phone_number=kitchen,
            order_type=payment_mode,
            order_id=order_id,
            customer=to,
            item_summary=summary,
            total=total,
            branch=branch,
            address="Takeaway",
            location_url=customer_location_link,
            order_time = order_time
        )
    user_cart[to]["reminder_sent"] = True

def generate_order_id():
    return f"ORD-{uuid.uuid4().hex[:6].upper()}"

def get_current_ist_time():
    ist = timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")