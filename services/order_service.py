# services/order_service.py

import os
import csv
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from pytz import timezone
from config.settings import BRANCH_DISCOUNTS, ORDERS_CSV, KITCHEN_NUMBERS
from services.whatsapp_service import send_text_message,  send_kitchen_branch_alert_template,send_selected_catalog_items
from stateHandlers.redis_state import add_pending_order, delete_user_cart, delete_yesterdays_data, get_off_hour_users, get_user_cart, set_user_cart, set_user_state
catalog_lookup = json.loads((Path(__file__).parent.parent / "data" / "products.json").read_text())


def log_order_to_csv(order_data):
    print("[ORDER SERVICE] Logging order...")
    file_exists = os.path.isfile(ORDERS_CSV)
    with open(ORDERS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=order_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(order_data)

def send_open_reminders():
    """Send opening reminders to users who messaged during off-hours"""
    ist = timezone('Asia/Kolkata')
    today = datetime.now(ist).date().isoformat()
    
    # Get users who messaged yesterday or today
    yesterday = (datetime.now(ist) - timedelta(days=1)).date().isoformat()
    
    for date in [yesterday, today]:
        users = get_off_hour_users(date)
        for user in users:
            try:
                send_text_message(user, "🌞 Good morning! We’re now open and ready to take your orders. 🍧")
                print(f"[REMINDER] Sent open reminder to {user}")
            except Exception as e:
                print(f"[ERROR] Failed to send reminder to {user}: {e}")

    # Clear yesterday's data
    delete_yesterdays_data(yesterday)

def update_cart_interaction(phone):
    """Update cart timestamp"""
    cart = get_user_cart(phone)
    print("[PRINTING LAST INTERACTION] :", cart)
    # Set interaction time if missing
    if cart:
        cart["last_interaction_time"] = get_current_ist_time()
    print("[PRINTING AFTER LAST INTERACTION] :", cart)
    set_user_cart(phone, cart)

def send_cart_reminder_once(phone):
    """Send cart reminder to user"""
    cart = get_user_cart(phone)
    print("[PRINTING INSIDE CART REMINDER ONCE] :", cart)
    if not cart:  # ✅ Handle missing cart
        print(f"[REMINDER] No cart found for {phone}")
        return False

    if not cart.get("summary"):
        return False

    reminder_message = (
        "🛒 Just a reminder! You still have items in your cart.\n"
        f"{cart.get('summary', '')}\n"
        "Complete your order with delivery or takeaway now! 😊"
    )
    ####new code to test
    try:
    
        cart = get_user_cart(phone)
        print(f"[🛒🛒🛒 DEBUG] Cart for {phone}: {cart}")

        if not cart or "summary" not in cart:
            print(f"[REMINDER] No summary in cart for {phone}")
            return False

        # Step 1: Extract product names from summary
        lines = cart["summary"].strip().split("\n")
        product_names = [line.rsplit(" x", 1)[0].strip() for line in lines]  # Extract names before " xN"

        # Step 2: Match names to catalog to get product IDs
        name_to_id = {v["name"]: k for k, v in catalog_lookup.items()}
        product_ids = []

        for name in product_names:
            product_id = name_to_id.get(name)
            if product_id:
                product_ids.append(product_id)
            else:
                print(f"[WARN] Product name '{name}' not found in catalog.")

        # Step 3: Send message
        if product_ids:
            send_selected_catalog_items(phone, product_ids)
            cart["reminder_sent"] = True
            set_user_cart(phone, cart)
            print(f"[REMINDER] Sent catalog reminder with items: {product_ids}")
            return True
        else:
            print(f"[REMINDER] No matching product IDs found for {phone}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to send cart reminder to {phone}: {e}")
        return False

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