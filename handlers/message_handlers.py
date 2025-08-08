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
    send_full_catalog, send_kitchen_branch_alert_template,send_rakhi_products,send_branch_selection_message,send_date_selection_message
)
import googlemaps
from services.order_service import confirm_order, confirm_order_after_payment, generate_order_id, log_order_to_csv, update_cart_interaction
from utils import logger
from utils.logger import log_user_activity
from utils.location_utils import get_branch_from_location
from utils.operational_hours_utils import handle_off_hour_message, is_store_open
from utils.payment_utils import generate_payment_link
from config.settings import ADMIN_NUMBERS, BRANCH_BLOCKED_USERS, BRANCH_STATUS, CART_PRODUCTS, BRANCH_DISCOUNTS, ORDERS_CSV
from stateHandlers.redis_state import add_pending_order, get_active_orders, get_pending_order, get_pending_orders, get_user_cart, is_branch_open, remove_pending_order, set_user_cart, delete_user_cart, get_user_state, set_user_state, delete_user_state, set_branch
from handlers.randomMessage_handler import matching
from config.settings import party_orders_link, BRANCHES, DATES

gmaps = googlemaps.Client(GOOGLE_MAPS_API_KEY)
quick_reply_ratings = {"5- outstanding": "5", "4- excellent": "4", "3 – good": "3", "2 – average": "2", "1 – poor": "1"}
RAKHI_HAMPER_PRODUCT_IDS = [
        "51jetppvov", "oici2ap1qd", 
        "5hfaymh61s", "8olxnu3afk",
        "aadudpumcb", "40llavglo4",
        "jykbu2a2ez", "9l89g0ezc9",
        "gvil23bxf8", "ygeeysblx2",
        "eyl9q23h7m", "mo1hlc617k",
        "p6kuuli1n6"
    ]


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
                    
                # INTERACTIVE LIST / BUTTON HANDLING
                elif message_type == "interactive":
                    interactive = msg.get("interactive", {})
                    selected_value = None

                    if "list_reply" in interactive:
                        selected_value = interactive["list_reply"]["id"]
                    elif "button_reply" in interactive:
                        selected_value = interactive["button_reply"]["id"]

                    log_user_activity(sender, "interactive_selected", selected_value)
                    
                    if current_state.get("step") == "awaiting_location":
                        handle_branch_selection(sender, selected_value, current_state)
                    elif current_state.get("step") == "SELECT_DATE":
                        handle_date_selection(sender, selected_value, current_state)
                    
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
    active_orders = None

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
# def handle_open_close(sender, text):
#     parts = text.split()
#     if len(parts) == 2:
#         action, branch_name = parts
#         branch_key = branch_name.strip().lower()
#         if branch_key not in BRANCH_STATUS:
#             send_text_message(sender, f"⚠️ Unknown branch: {branch_name}. Valid options: {', '.join(BRANCH_STATUS.keys())}")
#         elif action == "open":
#             BRANCH_STATUS[branch_key] = True
#             send_text_message(sender, f"✅ Branch *{branch_name.title()}* is now *open* for delivery.")
#             for user in BRANCH_BLOCKED_USERS.get(branch_key, []):
#                 send_text_message(user, f"📣 Our *{branch_name.title()}* branch is now open! You can place your order again. 🎉")
#                 BRANCH_BLOCKED_USERS[branch_key].clear()
#         elif action == "close":
#             BRANCH_STATUS[branch_key] = False
#             print(BRANCH_STATUS)
#             send_text_message(sender, f"🚫 Branch *{branch_name.title()}* is now *closed* for delivery.")
#     else:
#         send_text_message(sender, "❗ To open/close a branch, use:\n`open madhapur`\n`close kondapur`")


from stateHandlers.redis_state import get_branch_status, set_branch_status

def handle_open_close(sender, text):
    parts = text.split()
    if len(parts) == 2:
        action, branch_name = parts
        branch_key = branch_name.strip().lower()

        branch_status = get_branch_status()
        if branch_key not in branch_status:
            send_text_message(sender, f"⚠️ Unknown branch: {branch_name}. Valid options: {', '.join(branch_status.keys())}")
            return

        if action == "open":
            set_branch_status(branch_key, True)
            send_text_message(sender, f"✅ Branch *{branch_name.title()}* is now *open* for delivery.")
            for user in BRANCH_BLOCKED_USERS.get(branch_key, []):
                send_text_message(user, f"📣 Our *{branch_name.title()}* branch is now open! You can place your order again. 🎉")
                BRANCH_BLOCKED_USERS[branch_key].clear()

        elif action == "close":
            set_branch_status(branch_key, False)
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
    if branch is None:
        send_text_message(sender, "Sorry, we don't deliver to your area.")
        log_user_activity(sender, "location_received_out_of_area")
        return
    branch.lower()
    if not is_branch_open(branch):
        send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed. We’ll notify you when it reopens.")
        BRANCH_BLOCKED_USERS[branch].add(sender)
        log_user_activity(sender, f"branch_closed_attempt: {branch}")
        return

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
    if discount > 0:
        send_text_message(sender, f"🎉 Congratulations! You've unlocked a {discount}% discount.")
    send_delivery_takeaway_template(sender)
    log_user_activity(sender, "location_received")
    
# Handle Location By Text
def handle_location_by_text(sender,text):
    geocode = gmaps.geocode(text)
    if geocode:
        location = geocode[0]["geometry"]["location"]
        latitude = location["lat"]
        longitude = location["lng"]
        print(f"📍 Address '{text}' resolved to: ({latitude}, {longitude})")
        branch = get_branch_from_location(latitude,longitude)
        if branch is None:
            send_text_message(sender, "Sorry, we don't deliver to your area.")
            log_user_activity(sender, "location_received_out_of_area")
            return
        branch = branch.lower()
        # ✅ Check if branch is closed
        # ✅ Check if branch is closed
        if not is_branch_open(branch):
            send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed. We’ll notify you when it reopens.")
            BRANCH_BLOCKED_USERS[branch].add(sender)
            log_user_activity(sender, f"branch_closed_attempt: {branch}")
            return
        cart = get_user_cart(sender)
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
    return "OK", 200
    

# Handle Order Message Type
def handle_order_message(sender, items):
    has_rakhi_hamper = False
    total = 0
    summary = ""
    for item in items:
        prod_id = item.get("product_retailer_id")
        qty = item.get("quantity", 1)
        
        if prod_id in CART_PRODUCTS:
            product = CART_PRODUCTS[prod_id]
            total += product["price"] * qty
            summary += f"{product['name']} x{qty}\n"
            
            if prod_id in RAKHI_HAMPER_PRODUCT_IDS:
                has_rakhi_hamper = True
              
    cart = {
        "summary": summary,
        "total": total,
        "order_id": generate_order_id(),
    }
    set_user_cart(sender, cart)
    update_cart_interaction(sender)
    
    if has_rakhi_hamper:
        send_branch_selection_message(sender) 
        set_user_state(sender, {"step": "awaiting_location"})   
    else:
        send_text_message(sender, "📍 Please share your current location to check delivery availability.")
        set_user_state(sender, {"step": "awaiting_location"})
        
      
def handle_branch_selection(sender, selected_branch, current_state):
    
    if current_state and current_state.get("step") == "awaiting_location":

        valid_branches = [b.lower() for b in BRANCHES]
        if selected_branch.lower() not in valid_branches:
            
            selected_branch = next(
                b for b in BRANCHES if b.lower() == selected_branch.lower()
            )

        geocode = gmaps.geocode(selected_branch)
        location = geocode[0]["geometry"]["location"]
        latitude = location["lat"]
        longitude = location["lng"]

        user_state = get_user_state(sender) or {}
        user_state.update({
            "branch": selected_branch,
            "latitude": latitude,
            "longitude": longitude,
            "step": "SELECT_DATE"  
        })
        set_user_state(sender, user_state)

        cart = get_user_cart(sender) or {}
        cart.update({
            "branch": selected_branch,
            "latitude": latitude,
            "longitude": longitude
        })
        set_user_cart(sender, cart)

        print(f"[DEBUG] Branch: {selected_branch}, Lat: {latitude}, Lon: {longitude}")

        send_date_selection_message(sender)

  
def handle_date_selection(sender, selected_date, current_state):
    """Handle date selection from interactive list"""

    if current_state and current_state.get("step") == "SELECT_DATE":
        
        selected_date_normalized = selected_date.strip().lower() if selected_date else None
        valid_dates = [d.strip().lower() for d in DATES]

        if selected_date_normalized in valid_dates:
            set_user_state(sender, {"step": "DATE_SELECTED", "selected_date": selected_date_normalized})
            send_delivery_takeaway_template(sender)


    
def check_order_conflict(sender, selected_type):
    state = get_user_state(sender)
    existing_type = state.get("order_type")
    if existing_type and existing_type != selected_type:
        send_text_message(sender, f"⚠️ You've already selected {existing_type}. Please continue with it or restart the order.")
        return True
    return False

def check_action_conflict(sender, selected_action):
    state = get_user_state(sender)
    existing_action = state.get("action")
    if existing_action and existing_action != selected_action:
        send_text_message(sender, f"⚠️ You've already selected {existing_action}. Please continue with it or restart the order.")
        return True
    return False

# Handle button click
def handle_button_click(sender, button_text):
    if button_text == "order now":
        send_full_catalog(sender)
        log_user_activity(sender, "catalog_sent")
        
    elif button_text == "party orders":
        send_text_message(sender,party_orders_link)
        
    elif button_text == "rakhi hampers":
        send_rakhi_products(sender)

    elif button_text == "delivery":
        if check_order_conflict(sender, "Delivery"):
            return "OK", 200
        state = get_user_state(sender)
        set_user_state(sender, {**state, "order_type": "Delivery"})
        send_payment_option_template(sender)

    elif button_text == "takeaway":
        if check_order_conflict(sender, "Takeaway"):
            return "OK", 200
        state = get_user_state(sender)
        set_user_state(sender, {**state, "order_type": "Takeaway"})

        cart = get_user_cart(sender)
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

    elif button_text in ["pay now", "cod (cash on delivery)"]:
        print("[BUTTOONNNNNNNNNNNNNNNNNNNNNNNNNNNNN]:", button_text)
        selected_action = button_text.upper()
        if check_action_conflict(sender, selected_action):
            return "OK", 200

        cart = get_user_cart(sender)
        state = get_user_state(sender)
        branch = state.get("branch") or cart.get("branch")
        set_user_state(sender, {"step": "awaiting_address", "action": selected_action, "branch": branch})
        send_text_message(sender, "Please enter your full delivery address:")

    elif button_text in quick_reply_ratings:
        rating_value = quick_reply_ratings[button_text]
        save_feedback(sender, rating_value)
        send_text_message(sender, "🙏 Thank you for your feedback!")
        delete_user_state(sender)
        return "OK", 200


# Handle address input
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

    if action == "COD (CASH ON DELIVERY)":
        discount = get_branch_discount(sender, branch, get_user_cart)
        confirm_order(sender, branch, order_id, "cod (cash on delivery)", cart, discount, paid=False)
    # In your message handler where PAY NOW is processed
    elif action == "PAY NOW":
        # First send a message that we're generating the payment link
        send_text_message(sender, "🔄 *Generating Payment Link*\n\nPlease wait a moment while we create your secure payment link...")
    
        # Generate payment link with retry
        link = generate_payment_link(sender, 1, order_id)
    
        if link:
            # Clear the "generating" message by sending the actual payment link
            send_pay_online_template(sender, link)
            cart["payment_link"] = link
            set_user_cart(sender, cart)
            update_cart_interaction(sender)
            logger.info(f"Payment link successfully sent to {sender} for order {order_id}")
    else:
        # Send a more helpful error message with options
        error_message = ("⚠️ *Payment Link Issue*\n\n"
                         "We're having trouble generating your payment link. This could be due to:\n\n"
                         "1. Temporary network issues\n"
                         "2. Payment gateway maintenance\n\n"
                         "Please try again in a few minutes. If the issue persists, contact support.")
        
        send_text_message(sender, error_message)
        logger.error(f"Failed to generate payment link for {sender} after multiple attempts")



# def check_payment_status(order_id):
#     """
#     Check if a payment has been completed for a given order.
    
#     Args:
#         order_id (str): The order ID to check
        
#     Returns:
#         tuple: (bool, str) - (is_paid, payment_id or error message)
#     """
#     try:
#         # You'll need to implement this based on Razorpay's API
#         # This is just a placeholder
#         url = f"https://api.razorpay.com/v1/payments?reference_id={order_id}"
        
#         response = requests.get(
#             url,
#             auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
#         )
        
#         if response.status_code == 200:
#             payments = response.json().get("items", [])
#             for payment in payments:
#                 if payment.get("status") == "captured":
#                     return True, payment.get("id")
        
#         return False, "Payment not completed yet"
#     except Exception as e:
#         logger.error(f"Error checking payment status: {str(e)}")
#         return False, str(e)

# def handle_payment_check(sender, order_id):
#     """Handle payment status check requests from users"""
#     is_paid, result = check_payment_status(order_id)
    
#     if is_paid:
#         send_text_message(sender, "✅ *Payment Confirmed*\n\nYour payment has been successfully processed. Your order is now being prepared!")
#         # Update order status to PAID
#         # update_order_status(order_id, ORDER_STATUS["PAID"])
#         return True
#     else:
#         send_text_message(sender, f"⏳ *Payment Status*\n\n{result}\n\nWould you like to:\n1. Try again\n2. Generate new payment link")
#         # Store state to handle the next response
#         set_user_state(sender, {
#             "step": "PAYMENT_STATUS_CHECK",
#             "order_id": order_id
#         })
#         return False

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
    print (ADMIN_NUMBERS)
    return phone in ADMIN_NUMBERS