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







# # handlers/message_handlers.py


# from config.credentials import GOOGLE_MAPS_API_KEY
# from handlers.discount_handler import get_branch_discount
# from services.whatsapp_service import (
#     send_text_message, send_greeting_template,
#     send_delivery_takeaway_template,
#     send_payment_option_template,
#     send_pay_online_template,
#     send_full_catalog
# )
# import googlemaps
# from services.order_service import confirm_order, generate_order_id
# from utils.logger import log_user_activity
# from utils.location_utils import get_branch_from_location
# from utils.payment_utils import generate_payment_link
# from config.settings import BRANCH_BLOCKED_USERS, BRANCH_STATUS, CART_PRODUCTS, BRANCH_DISCOUNTS
# from stateHandlers.redis_state import get_user_cart, set_user_cart, delete_user_cart, get_all_carts

# user_cart = {}
# user_states = {}
# gmaps = googlemaps.Client(GOOGLE_MAPS_API_KEY)


# def handle_incoming_message(data):
#     print("[MESSAGE HANDLER] Received data:", data)
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

#                 # INITIAL GREETING AND LOGGING
#                 if message_type == "text":
#                     text = msg.get("text", {}).get("body", "").strip().lower()
#                     if text in ["hi", "hello", "hey", "menu"]:
#                         send_greeting_template(sender)
#                     log_user_activity(sender, "message_received", text)
#                     # ✅ Handle open/close branch command
#                     if any(text.startswith(cmd) for cmd in ["open", "close"]):
#                         print("[ENTERED_OPEN?CLOSE] :", text)
#                         parts = text.split()
#                         print("[ENTERED_OPEN?CLOSE_PARTS] :", parts)
#                         if len(parts) == 2:
#                             action, branch_name = parts
#                             branch_key = branch_name.strip().lower()
#                             print("[ENTERED_OPEN?CLOSE_PARTS] :", branch_name)
#                             print("[ENTERED_OPEN?ACTION] :", action)
#                             # Check valid branch
#                             if branch_key not in BRANCH_STATUS:
#                                 print("[ENTERED] :")
#                                 send_text_message(sender, f"⚠️ Unknown branch: {branch_name}. Valid options: {', '.join(BRANCH_STATUS.keys())}")
#                                 return "OK", 200
                            
#                             # Handle open action
#                             if action == "open":
#                                 BRANCH_STATUS[branch_key] = True
#                                 send_text_message(sender, f"✅ Branch *{branch_name.title()}* is now *open* for delivery.")
#                                 for user in BRANCH_BLOCKED_USERS.get(branch_key, []):
#                                     send_text_message(user, f"📣 Our *{branch_name.title()}* branch is now open! You can place your order again. 🎉")
#                                     BRANCH_BLOCKED_USERS[branch_key].clear()

#                             # Handle close action
#                             elif action == "close":
#                                 BRANCH_STATUS[branch_key] = False
#                                 print("[BRANCH_STATUS] :",BRANCH_STATUS[branch_key])
#                                 send_text_message(sender, f"🚫 Branch *{branch_name.title()}* is now *closed* for delivery.")
#                                 return "OK", 200
#                         else:
#                             send_text_message(sender, "❗ To open/close a branch, use:\n`open madhapur`\n`close kondapur`")
#                             return "OK", 200

#                     if "discount" in text:
#                         print("[DISCOUNT BLOCK ENTERED]:")
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
#                             else:
#                                 send_text_message(sender, "❗ Unknown branch or format.")

#                 # BUTTON CLICKED
#                 elif message_type == "button":
#                     button_text = msg.get("button", {}).get("text", "").strip().lower()
#                     log_user_activity(sender, "button_clicked", button_text)

#                 # LOCATION RECEIVED
#                 elif message_type == "location":
#                     latitude = msg.get("location", {}).get("latitude")
#                     longitude = msg.get("location", {}).get("longitude")
#                     branch = get_branch_from_location(latitude, longitude).lower()
#                     # ✅ Check if branch is closed
#                     if not BRANCH_STATUS.get(branch, True):
#                         send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed. We’ll notify you when it reopens.")
#                         BRANCH_BLOCKED_USERS[branch].add(sender)
#                         log_user_activity(sender, f"branch_closed_attempt: {branch}")
#                         return
#                     if branch:
#                         # Store branch in both state and cart
#                         user_states[sender] = {"step": "catalog_shown", "branch": branch}
#                         user_cart.setdefault(sender, {})["branch"] = branch
#                         user_cart[sender]["latitude"] = latitude
#                         user_cart[sender]["longitude"] = longitude
#                         send_text_message(sender, f"We can deliver from {branch} branch!")
#                         send_delivery_takeaway_template(sender)
#                     else:
#                         send_text_message(sender, "Sorry, we don't deliver to your area.")
#                     log_user_activity(sender, "location_received")
#                     return "OK", 200

#                 # ORDER CART via message-type 'order'
#                 elif message_type == "order":
#                     items = msg.get("order", {}).get("product_items", [])
#                     total = 0
#                     summary = ""
#                     for item in items:
#                         prod_id = item.get("product_retailer_id")
#                         qty = item.get("quantity", 1)
#                         if prod_id in CART_PRODUCTS:
#                             product = CART_PRODUCTS[prod_id]
#                             total += product["price"] * qty
#                             summary += f"{product['name']} x{qty}\n"
#                     # initialize cart
#                     user_cart[sender] = {
#                         "summary": summary,
#                         "total": total,
#                         "order_id": generate_order_id(),
#                         # branch may come later
#                     }
#                     print(f"🛒 Cart from {sender}:\n{summary}\n💰 Total: ₹{total}")

#                     # apply discount if branch known
#                     state = user_states.get(sender, {})
#                     print("[USER_STATES_IS_PRINTING]",user_cart)
#                     send_text_message(sender, "📍 Please share your current location to check delivery availability.")
#                     user_states[sender] = {"step": "awaiting_location"}
#                     return "OK", 200

#                 # HANDLE BUTTON RESPONSES AFTER CATALOG
#                 step = user_states.get(sender, {}).get("step")
#                 if message_type == "button":
#                     button_text = msg.get("button", {}).get("text", "").strip().lower()
#                     if button_text == "order now":
#                         send_full_catalog(sender)
#                         log_user_activity(sender, "catalog_sent")
#                     elif button_text == "delivery":
#                         send_payment_option_template(sender)
#                     elif button_text == "takeaway":
#                         # retrieve branch from states or cart
#                         branch = user_states.get(sender, {}).get("branch") or user_cart.get(sender, {}).get("branch")
#                         order_id = user_cart[sender].get("order_id")
#                         if not order_id:
#                             order_id = generate_order_id()
#                             user_cart[sender]["order_id"] = order_id
#                             cart = user_cart.get(sender, {})
#                             summary = cart.get("summary", "No items found.")
#                             total = cart.get("total", 0)
#                         user_cart[sender]["branch"] = branch
#                         user_cart[sender]["address"] = "Takeaway"
#                         discount = get_branch_discount(sender,branch, user_cart)
#                         confirm_order(sender, branch, user_cart[sender]["order_id"], "Takeaway", user_cart[sender], discount, paid=False)
#                         user_states[sender] = {"step": "order_confirmed"}
#                         return "OK", 200
#                     elif button_text == "pay now":
#                         branch = user_states.get(sender, {}).get("branch") or user_cart.get(sender, {}).get("branch")
#                         user_states[sender] = {"step": "awaiting_address", "action": "pay now","branch": branch}
#                         send_text_message(sender, "Please enter your full delivery address:")
#                     elif button_text == "cod":
#                         print("[PRINTING USER:] ", user_states[sender])
#                         branch = user_states.get(sender, {}).get("branch") or user_cart.get(sender, {}).get("branch")
#                         user_states[sender] = {"step": "awaiting_address", "action": "COD", "branch": branch}
#                         send_text_message(sender, "Please enter your full delivery address:")

#                 # HANDLE ADDRESS FOR PAYMENT OR COD
#                 if message_type == "text" and step == "awaiting_address":
#                     address = msg.get("text", {}).get("body", "").strip()
#                     state = user_states[sender]
#                     cart = user_cart.get(sender, {})
#                     action = state.get("action")
#                     branch = state.get("branch") or cart.get("branch")
#                     print("[BRANCH]:", state)
#                     order_id = cart.get("order_id") or generate_order_id()
#                     total = cart.get("total", 0)
#                     cart["address"] = address
#                     print("[BRANCH]",cart)
#                     if action == "COD":
#                         discount = get_branch_discount(sender,branch, user_cart)
#                         confirm_order(sender, branch, order_id, "COD", cart, discount, paid=False)
#                     elif action == "pay now":
#                         link = generate_payment_link(sender, total, order_id)
#                         if link:
#                             send_pay_online_template(sender, link)
#                             cart["payment_link"] = link
#                         else:
#                             send_text_message(sender, "⚠️ Failed to generate payment link. Please try again.")

#                     user_states[sender] = {"step": "start"}
#                     return "OK", 200
#                 elif message_type == "text" and step == "awaiting_location" and text :
#                     geocode = gmaps.geocode(text)
#                     if geocode:
#                         location = geocode[0]["geometry"]["location"]
#                         latitude = location["lat"]
#                         longitude = location["lng"]
#                         print(f"📍 Address '{text}' resolved to: ({latitude}, {longitude})")
#                     latitude = location["lat"]
#                     user_cart[sender]["latitude"] = latitude
#                     user_cart[sender]["longitude"] = longitude
#                     print("[LOCATION RELATED TESTING]:", user_cart)
#                     branch = get_branch_from_location(latitude,longitude).lower()
#                     # ✅ Check if branch is closed
#                     if not BRANCH_STATUS.get(branch,True):
#                         send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed. We’ll notify you when it reopens.")
#                         BRANCH_BLOCKED_USERS[branch].add(sender)
#                         log_user_activity(sender, f"branch_closed_attempt: {branch}")
#                         return
#                     if branch:
#                         send_text_message(sender, f"We can deliver from {branch} branch!")
#                         user_states[sender] = {"step": "catalog_shown", "branch": branch}
#                         branch = branch.lower()
#                         discount = BRANCH_DISCOUNTS.get(branch, 0)
#                         print("[DISCOUNT_BRANCH _RELATED] :", discount)
#                         if discount > 0:
#                             send_text_message(sender, f"🎉 Congratulations! You've unlocked a {discount}% discount.")
#                         send_delivery_takeaway_template(sender)
#                     else:
#                         send_text_message(sender, "Sorry, we don't deliver to your area.")
#                     log_user_activity(sender, "location_received")

#         return "OK", 200
#     except Exception as e:
#         import traceback
#         print("[ERROR] Message handler error:\n", traceback.format_exc())
#         return "OK", 200




from config.credentials import GOOGLE_MAPS_API_KEY
from handlers.discount_handler import get_branch_discount
from services.whatsapp_service import (
    send_text_message, send_greeting_template,
    send_delivery_takeaway_template,
    send_payment_option_template,
    send_pay_online_template,
    send_full_catalog
)
import googlemaps
import os
import csv
from apscheduler.schedulers.background import BackgroundScheduler
from services.order_service import confirm_order, generate_order_id
from utils.logger import log_user_activity
from utils.location_utils import get_branch_from_location
from utils.payment_utils import generate_payment_link
from utils.admin_access import check_admin_access
from config.settings import BRANCH_BLOCKED_USERS, BRANCH_STATUS, CART_PRODUCTS, BRANCH_DISCOUNTS
from stateHandlers.redis_state import get_user_cart, set_user_cart, delete_user_cart, get_all_carts

# Remove global user_cart
user_states = {}
gmaps = googlemaps.Client(GOOGLE_MAPS_API_KEY)
ORDERS_CSV = "orders.csv"
if not os.path.exists(ORDERS_CSV):
    with open(ORDERS_CSV, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Order ID", "Customer Number", "Order Time", "Branch", "Address", "Latitude", "Longitude",
            "Summary", "Total", "Payment Mode", "Paid", "Status"
        ])


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
                    current_state = user_states.get(sender, {}).get("step")
                    print("[PRINTING CURRENT_STATE] : ", current_state)
                    if text in ["hi", "hello", "hey", "menu"]:
                        if current_state == "order_confirmed":
                            # Ask what user wants to do next
                            send_text_message(
                                sender,
                                "👋 Hello again! How can we assist you today?\n\n"
                                "1️⃣ *Place a new order*\n"
                                "2️⃣ *Check my current order status*"
                            )
                            user_states[sender] = {"step": "post_order_choice"}
                        else:
                            # Fresh greeting
                            send_greeting_template(sender)
                            user_states[sender] = {"step": "start"}
                        return
                    log_user_activity(sender, "message_received", text)
                    if any(text.startswith(cmd) for cmd in ["open", "close"]):
                        is_allowed, deny_message = check_admin_access(sender)
                        if not is_allowed:
                            send_text_message(sender, deny_message)
                            return "OK", 200

                        print("[ENTERED_OPEN/CLOSE] :", text)
                        parts = text.split()
                        if len(parts) == 2:
                            action, branch_name = parts
                            branch_key = branch_name.strip().lower()

                            if branch_key not in BRANCH_STATUS:
                                send_text_message(sender, f"⚠️ Unknown branch: {branch_name}. Valid options: {', '.join(BRANCH_STATUS.keys())}")
                                return "OK", 200

                            if action == "open":
                                BRANCH_STATUS[branch_key] = True
                                send_text_message(sender, f"✅ Branch *{branch_name.title()}* is now *open* for delivery.")
                                for user in BRANCH_BLOCKED_USERS.get(branch_key, []):
                                    send_text_message(user, f"📣 Our *{branch_name.title()}* branch is now open! You can place your order again. 🎉")
                                BRANCH_BLOCKED_USERS[branch_key].clear()

                            elif action == "close":
                                BRANCH_STATUS[branch_key] = False
                                send_text_message(sender, f"🚫 Branch *{branch_name.title()}* is now *closed* for delivery.")
                                return "OK", 200
                        else:
                            send_text_message(sender, "❗ To open/close a branch, use:\n`open madhapur`\n`close kondapur`")
                            return "OK", 200

                    # ✅ DISCOUNT command
                    if "discount" in text:
                        is_allowed, deny_message = check_admin_access(sender)
                        if not is_allowed:
                            send_text_message(sender, deny_message)
                            return "OK", 200

                        print("[DISCOUNT BLOCK ENTERED]:")
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

                    # ✅ POST-ORDER CHOICE
                    if current_state == "post_order_choice":
                        response = msg.get("text", {}).get("body", "").strip().lower()
                        if response in ["1", "1.", "new order", "place order"]:
                            send_greeting_template(sender)
                            user_states[sender] = {"step": "start"}
                            set_user_cart(sender, {})
                        elif response in ["2", "2.", "check order", "status"]:
                            send_text_message(sender, "🔍 Let me check your order status...")
                            user_states[sender] = {"step": "checking_order_status"}
                        else:
                            send_text_message(sender, "❗ Please reply with:\n1 for New Order\n2 for Order Status")
                        return

                    # ✅ STATUS UPDATE
                    status_keywords = ["ready", "preparing", "ontheway", "delivered", "cancelled"]
                    if any(text.startswith(k) for k in status_keywords):
                        is_allowed, deny_message = check_admin_access(sender)
                        if not is_allowed:
                            send_text_message(sender, deny_message)
                            return "OK", 200

                        parts = text.split()
                        if len(parts) == 2:
                            new_status, order_id = parts
                            order_id = order_id.strip().upper()
                            new_status_clean = new_status.strip().capitalize()
                            if new_status_clean.lower() == "ontheway":
                                new_status_clean = "On the Way"

                            updated = False
                            updated_rows = []

                            with open(ORDERS_CSV, "r", newline='', encoding="utf-8") as infile:
                                reader = csv.DictReader(infile)
                                for row in reader:
                                    if row["Order ID"].strip().upper() == order_id:
                                        row["Status"] = new_status
                                        updated = True

                                        customer_number = row["Customer Number"].strip()
                                        if customer_number:
                                            send_text_message(customer_number, f"📦 Your order *{order_id}* is now *{new_status_clean}*.")
                                            # if new_status_clean.lower() == "delivered":
                                            #     schedule_feedback(customer_number)

                                    updated_rows.append(row)

                            if updated:
                                with open(ORDERS_CSV, "w", newline='', encoding="utf-8") as outfile:
                                    fieldnames = list(updated_rows[0].keys())
                                    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                                    writer.writeheader()
                                    for row in updated_rows:
                                        clean_row = {key: row.get(key, "") for key in fieldnames}
                                        writer.writerow(clean_row)

                                send_text_message(sender, f"✅ Order *{order_id}* marked as *{new_status_clean}*.")
                            else:
                                send_text_message(sender, f"⚠️ Order ID *{order_id}* not found.")
                        else:
                            send_text_message(sender, "❗ To update order status, use:\nready ORD-XXXXXX")
                        return "OK", 200


                    
                    
                # BUTTON CLICKED
                elif message_type == "button":
                    button_text = msg.get("button", {}).get("text", "").strip().lower()
                    log_user_activity(sender, "button_clicked", button_text)

                # LOCATION RECEIVED
                elif message_type == "location":
                    latitude = msg.get("location", {}).get("latitude")
                    longitude = msg.get("location", {}).get("longitude")
                    branch = get_branch_from_location(latitude, longitude).lower()

                    if not BRANCH_STATUS.get(branch, True):
                        send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed. We’ll notify you when it reopens.")
                        BRANCH_BLOCKED_USERS[branch].add(sender)
                        log_user_activity(sender, f"branch_closed_attempt: {branch}")
                        return

                    if branch:
                        user_states[sender] = {"step": "catalog_shown", "branch": branch}
                        cart = get_user_cart(sender)
                        cart["branch"] = branch
                        cart["latitude"] = latitude
                        cart["longitude"] = longitude
                        set_user_cart(sender, cart)

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

                    cart = {
                        "summary": summary,
                        "total": total,
                        "order_id": generate_order_id(),
                    }
                    set_user_cart(sender, cart)

                    print(f"🛒 Cart from {sender}:\n{summary}\n💰 Total: ₹{total}")

                    send_text_message(sender, "📍 Please share your current location to check delivery availability.")
                    user_states[sender] = {"step": "awaiting_location"}
                    return "OK", 200

                step = user_states.get(sender, {}).get("step")

                if message_type == "button":
                    button_text = msg.get("button", {}).get("text", "").strip().lower()
                    if button_text == "order now":
                        send_full_catalog(sender)
                        log_user_activity(sender, "catalog_sent")
                    elif button_text == "delivery":
                        send_payment_option_template(sender)
                    elif button_text == "takeaway":
                        cart = get_user_cart(sender)
                        branch = user_states.get(sender, {}).get("branch") or cart.get("branch")
                        order_id = cart.get("order_id") or generate_order_id()
                        cart["branch"] = branch
                        cart["address"] = "Takeaway"
                        set_user_cart(sender, cart)

                        discount = get_branch_discount(sender, branch, get_user_cart)
                        confirm_order(sender, branch, order_id, "Takeaway", cart, discount, paid=False)
                        user_states[sender] = {"step": "order_confirmed"}
                        return "OK", 200
                    elif button_text == "pay now":
                        cart = get_user_cart(sender)
                        branch = user_states.get(sender, {}).get("branch") or cart.get("branch")
                        user_states[sender] = {"step": "awaiting_address", "action": "pay now", "branch": branch}
                        send_text_message(sender, "Please enter your full delivery address:")
                    elif button_text == "cod":
                        cart = get_user_cart(sender)
                        branch = user_states.get(sender, {}).get("branch") or cart.get("branch")
                        user_states[sender] = {"step": "awaiting_address", "action": "COD", "branch": branch}
                        send_text_message(sender, "Please enter your full delivery address:")

                if message_type == "text" and step == "awaiting_address":
                    address = msg.get("text", {}).get("body", "").strip()
                    cart = get_user_cart(sender)
                    state = user_states[sender]
                    action = state.get("action")
                    branch = state.get("branch") or cart.get("branch")
                    order_id = cart.get("order_id") or generate_order_id()
                    total = cart.get("total", 0)

                    cart["address"] = address
                    set_user_cart(sender, cart)

                    if action == "COD":
                        discount = get_branch_discount(sender, branch, get_user_cart)
                        confirm_order(sender, branch, order_id, "COD", cart, discount, paid=False)
                        user_states[sender] = {"step": "order_confirmed"}
                    elif action == "pay now":
                        link = generate_payment_link(sender, total, order_id)
                        if link:
                            send_pay_online_template(sender, link)
                            cart["payment_link"] = link
                            set_user_cart(sender, cart)
                        else:
                            send_text_message(sender, "⚠️ Failed to generate payment link. Please try again.")
                    user_states[sender] = {"step": "start"}
                    return "OK", 200

                elif message_type == "text" and step == "awaiting_location":
                    text = msg.get("text", {}).get("body", "").strip()
                    geocode = gmaps.geocode(text)
                    if geocode:
                        location = geocode[0]["geometry"]["location"]
                        latitude = location["lat"]
                        longitude = location["lng"]
                        print(f"📍 Address '{text}' resolved to: ({latitude}, {longitude})")

                        cart = get_user_cart(sender)
                        cart["latitude"] = latitude
                        cart["longitude"] = longitude
                        set_user_cart(sender, cart)

                        branch = get_branch_from_location(latitude, longitude).lower()

                        if not BRANCH_STATUS.get(branch, True):
                            send_text_message(sender, f"⚠️ Our *{branch}* branch is currently closed.")
                            BRANCH_BLOCKED_USERS[branch].add(sender)
                            log_user_activity(sender, f"branch_closed_attempt: {branch}")
                            return

                        if branch:
                            send_text_message(sender, f"We can deliver from {branch} branch!")
                            user_states[sender] = {"step": "catalog_shown", "branch": branch}
                            discount = BRANCH_DISCOUNTS.get(branch, 0)
                            if discount > 0:
                                send_text_message(sender, f"🎉 Congratulations! You've unlocked a {discount}% discount.")
                            send_delivery_takeaway_template(sender)
                        else:
                            send_text_message(sender, "Sorry, we don't deliver to your area.")
                    log_user_activity(sender, "location_received")

        return "OK", 200
    except Exception as e:
        import traceback
        print("[ERROR] Message handler error:\n", traceback.format_exc())
        return "OK", 200