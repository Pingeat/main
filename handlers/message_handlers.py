# # handlers/message_handlers.py

# from services.whatsapp_service import (
#     send_text_message, send_greeting_template, 
#     send_delivery_takeaway_template, 
#     send_payment_option_template, 
#     send_pay_online_template,  # NEW
#     send_full_catalog
#     # send_kitchen_branch_alert_template
# )
# from services.order_service import confirm_order, generate_order_id
# from utils.logger import log_user_activity
# from utils.location_utils import get_branch_from_location
# from utils.payment_utils import generate_payment_link  # ✅ Import here
# from config.settings import (CART_PRODUCTS, BRANCH_DISCOUNTS)  # ✅ Make sure CART_PRODUCTS is imported

# user_cart = {}
# user_states = {}

# def handle_incoming_message(data):
#     print("[MESSAGE HANDLER] Received data:", data)
#     branch = ""
#     try:
#         for entry in data.get("entry", []):
#             for change in entry.get("changes", []):
#                 value = change.get("value", {})
#                 messages = value.get("messages", [])
#                 if not messages:
#                     continue
#                 msg = messages[0]
#                 sender = msg.get("from")
#                 message_type = msg.get("type")

#                 # Log every message
#                 if message_type == "text":
#                     text = msg.get("text", {}).get("body", "").strip().lower()
#                     if text in ["hi", "hello", "hey"]:
#                         send_greeting_template(sender)
#                         # send_text_message(sender, "HIII, RAA NANA KANNA")
#                     log_user_activity(sender, "message_received", text)
#                 elif message_type == "button":
#                     button_text = msg.get("button", {}).get("text", "").strip().lower()
#                     log_user_activity(sender, "button_clicked", button_text)
#                 elif message_type == "location":
#                     print("error 2 adv")
#                     latitude = msg.get("location", {}).get("latitude")
#                     print("error 3 adv")
#                     longitude = msg.get("location", {}).get("longitude")
#                     print("error 4 adv")
#                     branch = get_branch_from_location(latitude, longitude)
#                     print("error 1 advi")
#                     if branch:
#                         send_text_message(sender, f"We can deliver from {branch} branch!")
#                         user_states[sender] = {"step": "catalog_shown", "branch": branch}
#                         send_delivery_takeaway_template(sender)
#                     else:
#                         send_text_message(sender, "Sorry, we don't deliver to your area.")
#                     log_user_activity(sender, "location_received")
#                 elif message_type == "order":
#                     product_items = msg.get("order", {}).get("product_items", [])
#                     total = 0
#                     summary = ""
#                     for item in product_items:
#                         prod_id = item.get("product_retailer_id")
#                         qty = item.get("quantity", 1)
#                         if prod_id in CART_PRODUCTS:
#                             product = CART_PRODUCTS[prod_id]
#                             total += product["price"] * qty
#                             summary += f"{product['name']} x{qty}\n"
#                     user_cart[sender] = {
#                         "summary": summary,
#                         "total": total,
#                         "order_id": generate_order_id()
#                     }
#                     print(f"🛒 Cart from {sender}:\n{summary}\n💰 Total: ₹{total}")
#                     branch = user_cart.get(sender, {}).get("branch", "").lower()
#                     discount = BRANCH_DISCOUNTS.get(branch, 0)
#                     if discount > 0:
#                         send_text_message(sender, f"🎉 *Congratulations!* You’ve unlocked a *{discount}% discount*. It will be auto-applied at checkout. 🎁")

#                     send_text_message(sender, "📍 Please *share your Current location* to check delivery availability.")
#                     user_states[sender] = {"step": "awaiting_location"}
#                     return "OK", 200
#                     log_user_activity(sender, "cart_ordered")

#                 # Handle user steps
#                 step = user_states.get(sender, {}).get("step")
#                 if message_type == "text" and step == "awaiting_address":
#                     print("[BRANCH]:" ,user_cart.get(sender, {}).get("branch", "Kondapur"))
#                     address = msg.get("text", {}).get("body", "").strip()
#                     print("kkkkkkkkkk")
#                     action = user_states[sender]["action"]
#                     branch = user_cart.get(sender, {}).get("branch", "")
#                     order_id = user_cart.get(sender, {}).get("order_id")
#                     total = user_cart.get(sender, {}).get("total", 0)
#                     print("PPPPPPPPPP")

#                     if not order_id:
#                         order_id = generate_order_id()
#                         user_cart[sender]["order_id"] = order_id

#                     user_cart[sender]["address"] = address
                    
#                     if action == "COD(Cash on delivery)":
#                         print("HHHHHHHHH")
#                         print(sender)
#                         print("HHHHHHHHH")
#                         confirm_order(sender, branch, order_id, "COD",user_cart[sender], paid=False)
#                     elif action == "pay now":
#                         # ✅ Use generate_payment_link here
#                         payment_link = generate_payment_link(sender, total, order_id)
#                         if payment_link:
#                             send_pay_online_template(sender, payment_link)
#                             user_cart[sender]["payment_link"] = payment_link
#                         else:
#                             send_text_message(sender, "⚠️ Failed to generate payment link. Please try again.")

#                     user_states[sender] = {"step": "start"}
#                     return "OK", 200

#                 elif message_type == "text" and step == "start":
#                     text = msg.get("text", {}).get("body", "").strip().lower()
#                     if text in ["hi", "hello", "hey"]:
#                         send_greeting_template(sender)
#                 elif message_type == "text" and step == "awaiting_location" :
#                     print("[LOCATION_HANDLER]: HII ADVITHA")
#                     latitude = msg.get("location", {}).get("latitude")
#                     print(latitude)
#                     longitude = msg.get("location", {}).get("longitude")
#                     print(longitude)
#                     branch = get_branch_from_location(latitude, longitude)
#                     print("[LOCATION_HANDLER]: 123")
#                     if branch:
#                         send_text_message(sender, f"We can deliver from {branch} branch!")
#                         user_states[sender] = {"step": "catalog_shown", "branch": branch}
#                     else:
#                         send_text_message(sender, "Sorry, we don't deliver to your area.")
#                     log_user_activity(sender, "location_received")

#                 elif message_type == "button":
#                     button_text = msg.get("button", {}).get("text", "").strip().lower()
#                     if button_text == "order now":
#                         send_full_catalog(sender)
#                         log_user_activity(sender, "catalog sent")
#                     elif button_text == "delivery":
#                         send_payment_option_template(sender)
#                     elif button_text == "takeaway":
#                         branch = user_cart.get(sender, {}).get("branch", "Kondapur")
#                         confirm_order(sender, branch, user_cart[sender]["order_id"], "Takeaway", user_cart, paid=False)
#                         user_states[sender] = {"step": "order_confirmed"}
#                         return "OK", 200
#                     elif button_text == "pay now":
#                         user_states[sender] = {"step": "awaiting_address", "action": "pay now"}
#                         send_text_message(sender, "Please enter your full delivery address:")
#                     elif button_text == "cod":
#                         send_text_message(sender, "Please enter your full delivery address:")
#                         user_states[sender] = {"step": "awaiting_address", "action": "COD(Cash on delivery)"}
                        
#                     elif "discount" in text:
#                         parts = text.split()
#                         if len(parts) == 3:
#                             branch_name, keyword, value = parts
#                             branch_key = branch_name.strip().lower()
#                             if branch_key in BRANCH_DISCOUNTS and keyword == "discount":
#                                 try:
#                                     BRANCH_DISCOUNTS[branch_key] = int(value)
#                                     send_text_message(sender, f"✅ Discount for *{branch_name.title()}* branch set to {value}%.")
#                                 except:
#                                     send_text_message(sender, "❗ Invalid discount value. Use a number.")
#                                 else:
#                                     send_text_message(sender, "❗ Unknown branch or format.")
#                         else:
#                             send_text_message(sender, "❗ Use format: `kondapur discount 10` or `madhapur discount 0`")
#                             return "OK", 200


#     except Exception as e:
#         print("[ERROR] Message handler error:", e)
#     return "OK", 200









from config.credentials import GOOGLE_MAPS_API_KEY
from services.whatsapp_service import (
    send_text_message, send_greeting_template,
    send_delivery_takeaway_template,
    send_payment_option_template,
    send_pay_online_template,
    send_full_catalog
)
import googlemaps
from services.order_service import confirm_order, generate_order_id
from utils.logger import log_user_activity
from utils.location_utils import get_branch_from_location
from utils.payment_utils import generate_payment_link
from config.settings import CART_PRODUCTS, BRANCH_DISCOUNTS

user_cart = {}
user_states = {}
gmaps = googlemaps.Client(GOOGLE_MAPS_API_KEY)


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
                sender = msg.get("from")
                message_type = msg.get("type")

                # INITIAL GREETING AND LOGGING
                if message_type == "text":
                    text = msg.get("text", {}).get("body", "").strip().lower()
                    if text in ["hi", "hello", "hey"]:
                        send_greeting_template(sender)
                    log_user_activity(sender, "message_received", text)

                # BUTTON CLICKED
                elif message_type == "button":
                    button_text = msg.get("button", {}).get("text", "").strip().lower()
                    log_user_activity(sender, "button_clicked", button_text)

                # LOCATION RECEIVED
                elif message_type == "location":
                    latitude = msg.get("location", {}).get("latitude")
                    longitude = msg.get("location", {}).get("longitude")
                    branch = get_branch_from_location(latitude, longitude)
                    if branch:
                        # Store branch in both state and cart
                        user_states[sender] = {"step": "catalog_shown", "branch": branch}
                        user_cart.setdefault(sender, {})["branch"] = branch
                        send_text_message(sender, f"We can deliver from {branch} branch!")
                        send_delivery_takeaway_template(sender)
                    else:
                        send_text_message(sender, "Sorry, we don't deliver to your area.")
                    log_user_activity(sender, "location_received")
                    return "OK", 200

                # ORDER CART via message-type 'order'
                elif message_type == "order":
                    items = msg.get("order", {}).get("product_items", [])
                    total = 0
                    summary = ""
                    for item in items:
                        prod_id = item.get("product_retailer_id")
                        qty = item.get("quantity", 1)
                        if prod_id in CART_PRODUCTS:
                            product = CART_PRODUCTS[prod_id]
                            total += product["price"] * qty
                            summary += f"{product['name']} x{qty}\n"
                    # initialize cart
                    user_cart[sender] = {
                        "summary": summary,
                        "total": total,
                        "order_id": generate_order_id(),
                        # branch may come later
                    }
                    print(f"🛒 Cart from {sender}:\n{summary}\n💰 Total: ₹{total}")

                    # apply discount if branch known
                    state = user_states.get(sender, {})
                    if "branch" in state:
                        br = state["branch"].lower()
                        disc = BRANCH_DISCOUNTS.get(br, 0)
                        if disc > 0:
                            send_text_message(sender, f"🎉 Congratulations! You've unlocked a {disc}% discount.")

                    send_text_message(sender, "📍 Please share your current location to check delivery availability.")
                    user_states[sender] = {"step": "awaiting_location"}
                    return "OK", 200

                # HANDLE BUTTON RESPONSES AFTER CATALOG
                step = user_states.get(sender, {}).get("step")
                if message_type == "button":
                    button_text = msg.get("button", {}).get("text", "").strip().lower()
                    if button_text == "order now":
                        send_full_catalog(sender)
                        log_user_activity(sender, "catalog_sent")
                    elif button_text == "delivery":
                        send_payment_option_template(sender)
                    elif button_text == "takeaway":
                        # retrieve branch from states or cart
                        print["TAKEAWAY"]
                        branch = user_states.get(sender, {}).get("branch") or user_cart.get(sender, {}).get("branch")
                        order_id = user_cart[sender].get("order_id")
                        if not order_id:
                            order_id = generate_order_id()
                            user_cart[sender]["order_id"] = order_id
                            cart = user_cart.get(sender, {})
                            summary = cart.get("summary", "No items found.")
                            total = cart.get("total", 0)
                        user_cart[sender]["branch"] = branch
                        user_cart[sender]["address"] = "Takeaway"
                        confirm_order(sender, branch, user_cart[sender]["order_id"], "Takeaway", user_cart[sender], paid=False)
                        user_states[sender] = {"step": "order_confirmed"}
                        return "OK", 200
                    elif button_text == "pay now":
                        branch = user_states.get(sender, {}).get("branch") or user_cart.get(sender, {}).get("branch")
                        user_states[sender] = {"step": "awaiting_address", "action": "pay now","branch": branch}
                        send_text_message(sender, "Please enter your full delivery address:")
                    elif button_text == "cod":
                        print("[PRINTING USER:] ", user_states[sender])
                        branch = user_states.get(sender, {}).get("branch") or user_cart.get(sender, {}).get("branch")
                        user_states[sender] = {"step": "awaiting_address", "action": "COD", "branch": branch}
                        send_text_message(sender, "Please enter your full delivery address:")

                # HANDLE ADDRESS FOR PAYMENT OR COD
                if message_type == "text" and step == "awaiting_address":
                    address = msg.get("text", {}).get("body", "").strip()
                    state = user_states[sender]
                    cart = user_cart.get(sender, {})
                    action = state.get("action")
                    branch = state.get("branch") or cart.get("branch")
                    print("[BRANCH]:", state)
                    order_id = cart.get("order_id") or generate_order_id()
                    total = cart.get("total", 0)
                    cart["address"] = address
                    print("[BRANCH]",cart)
                    if action == "COD":
                        confirm_order(sender, branch, order_id, "COD", cart, paid=False)
                    elif action == "pay now":
                        link = generate_payment_link(sender, total, order_id)
                        if link:
                            send_pay_online_template(sender, link)
                            cart["payment_link"] = link
                        else:
                            send_text_message(sender, "⚠️ Failed to generate payment link. Please try again.")

                    user_states[sender] = {"step": "start"}
                    return "OK", 200
                elif message_type == "text" and step == "awaiting_location" and text :
                    print("[LOCATION_HANDLER]: HII ADVITHA")
                    geocode = gmaps.geocode(text)
                    if geocode:
                        location = geocode[0]["geometry"]["location"]
                        latitude = location["lat"]
                        longitude = location["lng"]
                        print(f"📍 Address '{text}' resolved to: ({latitude}, {longitude})")
                    latitude = location["lat"]
                    branch = get_branch_from_location(latitude,longitude)
                    if branch:
                        send_text_message(sender, f"We can deliver from {branch} branch!")
                        user_states[sender] = {"step": "catalog_shown", "branch": branch}
                        send_delivery_takeaway_template(sender)
                    else:
                        send_text_message(sender, "Sorry, we don't deliver to your area.")
                    log_user_activity(sender, "location_received")

        return "OK", 200
    except Exception as e:
        print("[ERROR] Message handler error:", e)
        return "OK", 200
