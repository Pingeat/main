import csv
from config.credentials import GOOGLE_MAPS_API_KEY
from handlers.discount_handler import get_branch_discount
from handlers.feedback_handler import save_feedback, schedule_feedback
from handlers.marketing_handler import handle_marketing_message
from services.whatsapp_service import (
    send_text_message, send_greeting_template,
    send_delivery_takeaway_template,
    send_payment_option_template,
    send_pay_online_template,
    send_full_catalog, send_kitchen_branch_alert_template
)
import googlemaps
from services.order_service import confirm_order, generate_order_id, log_order_to_csv, update_cart_interaction
from utils.logger import log_user_activity
from utils.location_utils import get_branch_from_location
from utils.operational_hours_utils import handle_off_hour_message, is_store_open
from utils.payment_utils import generate_payment_link
from config.settings import ADMIN_NUMBERS, BRANCH_BLOCKED_USERS, BRANCH_STATUS, CART_PRODUCTS, BRANCH_DISCOUNTS, ORDERS_CSV
from stateHandlers.redis_state import add_pending_order, get_active_orders, get_pending_order, get_pending_orders, get_user_cart, remove_pending_order, set_user_cart, delete_user_cart, get_user_state, set_user_state, delete_user_state
from handlers.randomMessage_handler import matching

gmaps = googlemaps.Client(GOOGLE_MAPS_API_KEY)
quick_reply_ratings = {"5- outstanding": "5", "4- excellent": "4", "3 – good": "3", "2 – average": "2", "1 – poor": "1"}

#links
party_orders_link = "https://wa.me/918688641919?text=I%20am%20looking%20for%20a%20bulk%20order"
subscriptions_link = "https://wa.me/918688641919?text=I%20am%20looking%20for%20juices%2C%20oatmeals%20or%20fruit%20bowl%20subscription "

# Handle Incoming Messages
def handle_incoming_message(data):
    print("[MESSAGE HANDLER] Received data:", data)
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                if not messages:
                    continue
                msg = messages[0]
                sender = msg.get("from").lstrip('+')  # Normalize sender ID
                message_type = msg.get("type")
                
                print("[SENDER]: ", sender)
                # Update cart interaction time
                update_cart_interaction(sender)
                
                # Check Store Operational Hours
                if not is_store_open():
                    handle_off_hour_message(sender)
                    return "Closed hours", 200
                # Log activity
                if message_type == "text":
                    text = msg.get("text", {}).get("body", "").strip().lower()
                    log_user_activity(sender, "message_received", text)

                # Get current state
                current_state = get_user_state(sender)
                print("[PRINTING CURRENT STATE OF THE USER]: ", current_state)

                # TEXT MESSAGE HANDLING
                if message_type == "text":
                    text = msg.get("text", {}).get("body", "").strip().lower()
                    if text in ["hi", "hello", "hey", "menu"]:
                        handle_greeting(sender, current_state)
                    elif any(text.startswith(k) for k in ["ready", "preparing", "ontheway", "delivered", "cancelled"]):
                        handle_update_order_status(sender, text)
                    elif text in ["status", "check status", "my order"]:
                        handle_check_status(sender)
                    elif any(text.startswith(cmd) for cmd in ["open", "close"]):
                        handle_open_close(sender, text)
                    elif "discount" in text:
                        handle_discount(sender, text)
                    elif current_state.get("step") == "awaiting_address":
                        handle_address_input(sender, text)
                    elif current_state.get("step") == "post_order_choice":
                        handle_post_order_choice(sender, text)
                    elif current_state.get("step") == "awaiting_location":
                        handle_location_by_text(sender, text)
                    # Marketing message command
                    elif text.startswith("message customer"):
                        if not is_admin(sender):
                            send_text_message(sender, "⚠️ This feature is only available to admins.")
                            return "OK", 200
                
                        handle_marketing_message(sender, text)
                        return "OK", 200
                    else:
                        matching(sender,text)    
                    return "OK", 200

                # LOCATION MESSAGE HANDLING
                elif message_type == "location":
                    latitude = msg.get("location", {}).get("latitude")
                    longitude = msg.get("location", {}).get("longitude")
                    handle_location(sender, latitude, longitude)

                # ORDER MESSAGE HANDLING
                elif message_type == "order":
                    items = msg.get("order", {}).get("product_items", [])
                    handle_order_message(sender, items)

                # BUTTON CLICK HANDLING
                elif message_type == "button":
                    button_text = msg.get("button", {}).get("text", "").strip().lower()
                    log_user_activity(sender, "button_clicked", button_text)
                    handle_button_click(sender, button_text)

        return "OK", 200

    except Exception as e:
        import traceback
        print("[ERROR] Message handler error:\n", traceback.format_exc())
        return "OK", 200


# Handle Greeting
def handle_greeting(sender, current_state):
    from stateHandlers.redis_state import get_pending_orders
    pending_orders = get_pending_orders()

    active_orders = [o for o in pending_orders.values() if o["customer"] == sender and o["status"] == "Pending" or "Preparing"]

    if active_orders:
        print("[DEBUG] Active Orders:", active_orders)
        options = ""
        for idx, order in enumerate(active_orders, start=1):
            options += f"{idx}️⃣ Check status of `{order['order_id']}`\n"
        options += f"{len(active_orders) + 1}️⃣ Place a new order"

        send_text_message(sender, f"👋 Hello again! How can we assist you today?\n\n{options}")
        set_user_state(sender, {"step": "post_order_choice"})
    else:
        from services.whatsapp_service import send_greeting_template
        send_greeting_template(sender)
        set_user_state(sender, {"step": "start"})

# Handle Open/Close Branch Command
def handle_open_close(sender, text):
    parts = text.split()
    if len(parts) == 2:
        action, branch_name = parts
        branch_key = branch_name.strip().lower()
        if branch_key not in BRANCH_STATUS:
            send_text_message(sender, f"⚠️ Unknown branch: {branch_name}. Valid options: {', '.join(BRANCH_STATUS.keys())}")
        elif action == "open":
            BRANCH_STATUS[branch_key] = True
            send_text_message(sender, f"✅ Branch *{branch_name.title()}* is now *open* for delivery.")
            for user in BRANCH_BLOCKED_USERS.get(branch_key, []):
                send_text_message(user, f"📣 Our *{branch_name.title()}* branch is now open! You can place your order again. 🎉")
                BRANCH_BLOCKED_USERS[branch_key].clear()
        elif action == "close":
            BRANCH_STATUS[branch_key] = False
            send_text_message(sender, f"🚫 Branch *{branch_name.title()}* is now *closed* for delivery.")
    else:
        send_text_message(sender, "❗ To open/close a branch, use:\n`open madhapur`\n`close kondapur`")

# Handle Discount Setting
def handle_discount(sender, text):
    if not is_admin(sender):
        send_text_message(sender, "⚠️ This feature is only available to admins.")
        return
    parts = text.split()
    if len(parts) == 3:
        branch_name, keyword, value = parts
        branch_key = branch_name.strip().lower()
        if branch_key in BRANCH_DISCOUNTS and keyword == "discount":
            try:
                BRANCH_DISCOUNTS[branch_key] = int(value)
                send_text_message(sender, f"✅ Discount for *{branch_name.title()}* branch set to {value}%.")
            except:
                send_text_message(sender, "❗ Invalid discount value. Use a number.")
        else:
            send_text_message(sender, "❗ Unknown branch or format.")
    else:
        send_text_message(sender, "❗ Use format: `kondapur discount 10` or `madhapur discount 0`")

# Handle Location Received
def handle_location(sender, latitude, longitude):
    branch = get_branch_from_location(latitude, longitude)
    if branch:
        branch.lower()
    if not BRANCH_STATUS.get(branch, True):
        send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed. We’ll notify you when it reopens.")
        BRANCH_BLOCKED_USERS[branch].add(sender)
        log_user_activity(sender, f"branch_closed_attempt: {branch}")
        return

    if branch:
        cart = get_user_cart(sender)
        print("[handle_location]:", cart)
        cart.update({
            "branch": branch,
            "latitude": latitude,
            "longitude": longitude
        })
        set_user_cart(sender, cart)
        update_cart_interaction(sender)
        set_user_state(sender, {"step": "catalog_shown", "branch": branch})
        send_text_message(sender, f"We can deliver from {branch.title()} branch!")
        branch = branch.lower()
        discount = BRANCH_DISCOUNTS.get(branch, 0)
        print("[DISCOUNT_BRANCH _RELATED] :", discount)
        if discount > 0:
            send_text_message(sender, f"🎉 Congratulations! You've unlocked a {discount}% discount.")
        send_delivery_takeaway_template(sender)
    else:
        send_text_message(sender, "Sorry, we don't deliver to your area.")
    log_user_activity(sender, "location_received")
    
# Handle Location By Text
def handle_location_by_text(sender,text):
    geocode = gmaps.geocode(text)
    if geocode:
        location = geocode[0]["geometry"]["location"]
        latitude = location["lat"]
        longitude = location["lng"]
        print(f"📍 Address '{text}' resolved to: ({latitude}, {longitude})")
        branch = get_branch_from_location(latitude,longitude).lower()
        # ✅ Check if branch is closed
        if not BRANCH_STATUS.get(branch,True):
            send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed. We’ll notify you when it reopens.")
            BRANCH_BLOCKED_USERS[branch].add(sender)
            log_user_activity(sender, f"branch_closed_attempt: {branch}")
            return
        if branch:
            cart = get_user_cart(sender)
            print("[handle_location_by_text] :", cart)
            cart.update({
            "branch": branch,
            "latitude": latitude,
            "longitude": longitude
        })
            set_user_cart(sender, cart)
            print("[handle_location_by_text] :", cart)
            update_cart_interaction(sender)
            set_user_state(sender, {"step": "catalog_shown", "branch": branch})
            send_text_message(sender, f"We can deliver from {branch.title()} branch!")
            branch = branch.lower()
            discount = BRANCH_DISCOUNTS.get(branch, 0)
            print("[DISCOUNT_BRANCH _RELATED] :", discount)
            if discount > 0:
                send_text_message(sender, f"🎉 Congratulations! You've unlocked a {discount}% discount.")
            send_delivery_takeaway_template(sender)
    else:
        send_text_message(sender, "Sorry, we don't deliver to your area.")
        log_user_activity(sender, "location_received")
    return "OK", 200

# Handle Order Message Type
def handle_order_message(sender, items):
    total = 0
    summary = ""
    for item in items:
        prod_id = item.get("product_retailer_id")
        qty = item.get("quantity", 1)
        if prod_id in CART_PRODUCTS:
            product = CART_PRODUCTS[prod_id]
            total += product["price"] * qty
            summary += f"{product['name']} x{qty}\n"

    cart = {
        "summary": summary,
        "total": total,
        "order_id": generate_order_id(),
    }
    set_user_cart(sender, cart)
    update_cart_interaction(sender)
    send_text_message(sender, "📍 Please share your current location to check delivery availability.")
    set_user_state(sender, {"step": "awaiting_location"})
    
#Handle Button Clicks
def handle_button_click(sender, button_text):
    if button_text == "order now":
        send_full_catalog(sender)
        log_user_activity(sender, "catalog_sent")
    elif button_text == "delivery":
        send_payment_option_template(sender)
    elif button_text == "party orders":
        send_text_message(sender,f" 🎉 For party orders, message us here: {party_orders_link}")
    elif button_text == "subscriptions":
        send_text_message(sender,f" 📦 For subscriptions, message us here: {subscriptions_link}")
    elif button_text == "takeaway":
        cart = get_user_cart(sender)
        state = get_user_state(sender)
        branch = state.get("branch") or cart.get("branch")
        order_id = cart.get("order_id") or generate_order_id()
        cart.update({
            "branch": branch,
            "address": "Takeaway"
        })
        set_user_cart(sender, cart)
        update_cart_interaction(sender)
        discount = get_branch_discount(sender, branch, get_user_cart)
        confirm_order(sender, branch, order_id, "Takeaway", cart, discount, paid=False)
        set_user_state(sender, {"step": "order_confirmed"})
    elif button_text in ["pay now", "cod"]:
        cart = get_user_cart(sender)
        state = get_user_state(sender)
        branch = state.get("branch") or cart.get("branch")
        set_user_state(sender, {"step": "awaiting_address", "action": button_text.upper(), "branch": branch})
        send_text_message(sender, "Please enter your full delivery address:")
    elif button_text in quick_reply_ratings:
        rating_value = quick_reply_ratings[button_text]
        save_feedback(sender, rating_value)
        send_text_message(sender, "🙏 Thank you for your feedback!")
        delete_user_state(sender)
        return "OK", 200

#Handle Address Input
def handle_address_input(sender, address):
    cart = get_user_cart(sender)
    state = get_user_state(sender)
    action = state.get("action")
    branch = state.get("branch") or cart.get("branch")
    print("[handle_address_input] : ", cart)
    order_id = cart.get("order_id") or generate_order_id()
    total = cart.get("total", 0)
    
    cart["address"] = address
    set_user_cart(sender, cart)
    update_cart_interaction(sender)

    if action == "COD":
        discount = get_branch_discount(sender, branch, get_user_cart)
        confirm_order(sender, branch, order_id, "COD", cart, discount, paid=False)
    elif action == "PAY NOW":
        link = generate_payment_link(sender, total, order_id)
        if link:
            send_pay_online_template(sender, link)
            cart["payment_link"] = link
            set_user_cart(sender, cart)
            update_cart_interaction(sender)
        else:
            send_text_message(sender, "⚠️ Failed to generate payment link. Please try again.")

#Post Order Choice Handler
def handle_post_order_choice(sender, response):
    try:
        choice = int(response.strip())
    except:
        send_text_message(sender, "❗ Please reply with a number.")
        return "OK", 200

    from stateHandlers.redis_state import get_pending_orders
    pending_orders = [o for o in get_pending_orders().values() if o["customer"] == sender and o["status"] == "Pending" or "Preparing"]
    max_choice = len(pending_orders) + 1

    if choice < 1 or choice > max_choice:
        send_text_message(sender, f"❗ Invalid choice. Pick between 1 and {max_choice}")
        return "OK", 200

    if choice == max_choice:
        send_greeting_template(sender)
        set_user_state(sender, {"step": "start"})
        delete_user_cart(sender)
    else:
        selected = pending_orders[choice - 1]
        print("[handle_post_order_choice] :", selected)
        send_text_message(sender, f"📦 Order Status: {selected['status']}\n🆔 Order ID: {selected['order_id']}")

    return "OK", 200

#Check Status Of Current Order
def handle_check_status(sender):
    active_orders = get_active_orders(sender)
    if not active_orders:
        send_text_message(sender, "⚠️ No active orders found.")
        return

    for order in active_orders:
        send_text_message(
            sender,
            f"📦 *Order Status*: *{order['Status']}*\n"
            f"🆔 Order ID: {order['Order ID']}\n"
            f"🏪 Branch: {order['Branch']}\n"
            f"💰 Total: ₹{order['Total']}"
        )

# Update Order Status
def handle_update_order_status(sender, text):
    if not is_admin(sender):
        send_text_message(sender, "⚠️ Admin-only command.")
        return

    parts = text.split()
    if len(parts) != 2:
        send_text_message(sender, "❗ Usage: `ready ORD-XXXXXX`")
        return

    new_status, order_id = parts
    new_status_clean = new_status.capitalize()
    
    if new_status.lower() == "ontheway":
        new_status_clean = "On the Way"

    order_id = order_id.strip().upper()
    order_data = get_pending_order(order_id)
    
    if not order_data:
        send_text_message(sender, f"❌ Order `{order_id}` not found.")
        return

    # Update order data
    print("[PRINTIIG PENDING ORDER] :",get_pending_order(order_id))
    order_data["status"] = new_status_clean
    order_data["reminders_sent"] = 6  # Stop reminders
    add_pending_order(order_id, order_data)
    print("[PRINTIIG PENDING ORDER] :",get_pending_order(order_id))

    # Notify customer
    customer = order_data.get("customer")
    send_text_message(customer, f"📦 Your order `{order_id}` is now *{new_status_clean}*.")

    # Reset user if delivered
    if new_status_clean == "Delivered":
        maybe_reset_user_after_delivery(customer, order_id)

    # Notify admin
    send_text_message(sender, f"✅ Order `{order_id}` marked as *{new_status_clean}*. ")
    # Optional: Log to CSV (for history)
    log_order_to_csv({
        "Order ID": order_id,
        "Customer Number": sender,
        "Branch": order_data["branch"],
        "Address": order_data["address"],
        "Summary": order_data["summary"],
        "Total": order_data["total"],
        "Payment Mode": order_data["payment_mode"],
        "Paid": False,
        "Status": new_status_clean
    })
    
# ✅ RESET USER AFTER DELIVERY
def maybe_reset_user_after_delivery(customer_number, order_id):
    try:
        # Clear user state and cart
        set_user_state(customer_number, {"step": "start"})
        delete_user_cart(customer_number)

        # Remove order from Redis
        remove_pending_order(order_id)

        # Notify customer
        send_text_message(
            customer_number,
            "✅ Your order has been delivered! Feel free to place a new one."
        )
        print(f"[RESET] User {customer_number} reset after delivery of {order_id}")
    except Exception as e:
        print(f"[ERROR] Failed to reset user: {e}")

# Check Admin
def is_admin(phone):
    # Replace with actual list of admin numbers
    return phone in ADMIN_NUMBERS