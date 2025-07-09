# services/order_service.py

import os
import csv
import uuid
import json
from datetime import datetime
from pathlib import Path
from pytz import timezone
from config.settings import BRANCH_DISCOUNTS, ORDERS_CSV, KITCHEN_NUMBERS
from services.whatsapp_service import send_text_message,  send_kitchen_branch_alert_template
from stateHandlers.redis_state import add_pending_order, delete_user_cart, get_user_cart, set_user_state

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
    # # Implement daily open alerts here
    # """Send morning open alerts to users who tried ordering during closed hours."""
    # print("[REMINDER] Sending morning open alerts...")

    # today = str(datetime.now(timezone('Asia/Kolkata')).date())
    # new_rows = []

    # if not os.path.exists(OFF_HOUR_USERS_CSV):
    #     return

    # with open(OFF_HOUR_USERS_CSV, newline='') as f:
    #     reader = csv.DictReader(f)
    #     for row in reader:
    #         if row["Date"] == today:
    #             phone = row["Phone Number"]
    #             send_text_message(phone, "🌞 Good morning! We’re now open and ready to take your orders.")
    #         else:
    #             new_rows.append(row)

    # with open(OFF_HOUR_USERS_CSV, "w", newline='') as f:
    #     writer = csv.DictWriter(f, fieldnames=["Phone Number", "Date"])
    #     writer.writeheader()
    #     writer.writerows(new_rows)

def send_cart_reminder_once():
    print("[REMINDER] Sending cart reminders...")
    # # Implement cart cleanup and reminders here
    # """Send cart reminders and clean up old carts."""
    # print("[REMINDER] Sending cart reminders and cleaning up old carts...")

    # ist = timezone('Asia/Kolkata')
    # now = datetime.now(ist)

    # to_delete = []

    # for phone, cart in list(user_cart.items()):
    #     last_time_raw = cart.get("last_interaction_time")
    #     reminder_sent = cart.get("reminder_sent", False)
    #     address = cart.get("address")

    #     if last_time_raw:
    #         try:
    #             if isinstance(last_time_raw, datetime):
    #                 last_time = last_time_raw
    #             else:
    #                 last_time = datetime.strptime(last_time_raw, "%Y-%m-%d %H:%M:%S")
    #                 last_time = ist.localize(last_time)
    #         except Exception as e:
    #             print("⚠️ Error parsing last interaction time:", e)
    #             continue

    #         if now - last_time > timedelta(days=1):
    #             print(f"🗑️ Deleting abandoned cart for {phone}")
    #             to_delete.append(phone)
    #         elif now - last_time > timedelta(minutes=5) and cart.get("summary") and not address and not reminder_sent:
    #             send_text_message(phone, "🛒 Just a reminder! You still have items in your cart. Complete your order with delivery or takeaway.")
    #             user_cart[phone]["reminder_sent"] = True

    # for phone in to_delete:
    #     del user_cart[phone]
    

# Confirm Order
def confirm_order(to, branch, order_id, payment_mode, user_cart, discount, paid=False):
    print("[CONFIRM_ORDER] Confirming new order:", order_id)
    
    cart = get_user_cart(to)
    summary = cart.get("summary", "")
    total = cart.get("total", 0)

    # Load branches data
    branches_data = json.loads((Path(__file__).parent.parent / "data" / "branches.json").read_text())
    contact = branches_data.get(branch, {}).get("contact", "")

    # Build final summary with discount
    discount_percent = discount.get("discount_percent", 0)
    discount_amount = discount.get("discount_amount", 0)
    final_total = discount.get("final_total", total)

    if discount_percent > 0:
        summary += f"\n\n💸 *{discount_percent}% Discount Applied*: -₹{discount_amount}"
    summary += f"\n💰 *Total Payable*: ₹{final_total}"

    # Get address and location
    address = cart.get("address", "Takeaway" if payment_mode == "Takeaway" else "N/A")
    latitude = cart.get("latitude", "")
    longitude = cart.get("longitude", "")
    branch_location_link = branches_data.get(branch, {}).get("map_link", "")
    customer_location_link = f"https://www.google.com/maps?q={latitude},{longitude}" if latitude and longitude else "N/A"
    status_line = "✅ Payment received." if paid else "💵 Payment Mode: Cash on Delivery"
    order_time = get_current_ist_time()

    # Sanitize strings for WhatsApp
    item_summary_clean = summary.replace("\n", " | ").replace("*", "").strip()[:250]
    address_clean = address.replace("\n", " ").strip()[:250]

    # Log to CSV
    log_order_to_csv({
        "Order ID": order_id,
        "Customer Number": to,
        "Order Time": get_current_ist_time(),
        "Branch": branch,
        "Address": address_clean,
        "Summary": summary,
        "Total": total,
        "Payment Mode": payment_mode,
        "Paid": paid,
        "Status": "Pending"
    })

    # Save order in Redis
    add_pending_order(order_id, {
        "customer": to,
        "branch": branch,
        "order_id": order_id,
        "payment_mode": payment_mode,
        "summary": summary,
        "total": total,
        "address": address_clean,
        "location_url": customer_location_link,
        "order_time": get_current_ist_time(),
        "status": "Pending",
        "reminders_sent": 0
    })
    
    
    # ✅ Message to customer
    customer_msg = (
        f"🧾 *Order Confirmed!*\n"
        f"🆔 Order ID: {order_id}\n\n"
        f"{item_summary_clean}\n"
        f"{status_line}\n"
        f"🕒 Time: {order_time}\n\n"
        f"🏪 Branch: {branch}\n"
        f"📍 {branch_location_link}\n"
        f"📞 Contact us if any changes: {contact}"
        f"👨‍🍳 Your food is getting ready! We’ll deliver it to you as soon as possible. 🚚💨"
    )
    
    # Send confirmation
    send_text_message(to, f"Order confirmed! {customer_msg}")
    # Alert kitchen(s)
    for kitchen in KITCHEN_NUMBERS:
        send_kitchen_branch_alert_template(
            phone_number=kitchen,
            order_type=payment_mode,
            order_id=order_id,
            customer=to,
            item_summary=item_summary_clean,
            total=total,
            branch=branch,
            address=address_clean,
            location_url=customer_location_link,
            order_time=get_current_ist_time()
        )

    # Delete cart and set state
    delete_user_cart(to)
    set_user_state(to, {"step": "order_confirmed"})

def generate_order_id():
    return f"ORD-{uuid.uuid4().hex[:6].upper()}"

def get_current_ist_time():
    ist = timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")