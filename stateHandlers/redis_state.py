# stateHandlers/redis_state.py

import redis
import os
import json

# Connect to Redis
redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

# ===== USER CART =====
def get_user_cart(phone):
    """Get cart for a user"""
    cart_json = redis_client.get(f"user_cart:{phone}")
    return json.loads(cart_json) if cart_json else {}

def set_user_cart(phone, cart_data):
    """Set cart for a user with TTL of 1 day"""
    redis_client.setex(f"user_cart:{phone}", 86400, json.dumps(cart_data))

def delete_user_cart(phone):
    """Delete user's cart"""
    redis_client.delete(f"user_cart:{phone}")

def get_all_carts():
    """Get all carts (for debugging)"""
    keys = redis_client.keys("user_cart:*")
    return {key.split(":")[1]: json.loads(redis_client.get(key)) for key in keys} if keys else {}

# ===== USER STATE =====
def get_user_state(phone):
    """Get current state for a user"""
    return json.loads(redis_client.get(f"user_state:{phone}")) if redis_client.exists(f"user_state:{phone}") else {}

def set_user_state(phone, state_data):
    """Set user state with TTL of 1 day"""
    redis_client.setex(f"user_state:{phone}", 86400, json.dumps(state_data))

def delete_user_state(phone):
    """Delete user state"""
    redis_client.delete(f"user_state:{phone}")

def get_all_states():
    """Debug: Get all user states"""
    keys = redis_client.keys("user_state:*")
    return {k.split(":")[1]: json.loads(redis_client.get(k)) for k in keys} if keys else {}

# ===== ACTIVE ORDERS =====
def add_pending_order(order_id, order_data):
    redis_client.setex(f"order:{order_id}", 180, json.dumps(order_data))

def get_pending_orders():
    keys = redis_client.keys("order:*")
    return {key.split(":")[1]: json.loads(redis_client.get(key)) for key in keys} if keys else {}

def get_pending_order(order_id):
    """Get a specific pending order by ID"""
    data = redis_client.get(f"order:{order_id}")
    return json.loads(data) if data else None

def update_pending_order_reminders(order_id, count):
    order_data = json.loads(redis_client.get(f"order:{order_id}"))
    order_data["reminders_sent"] = count
    redis_client.setex(f"order:{order_id}", 180, json.dumps(order_data))

def remove_pending_order(order_id):
    redis_client.delete(f"order:{order_id}")


def get_active_orders(customer_number):
    keys = redis_client.keys("order:*")
    active_orders = []

    for key in keys:
        order_id = key.split(":")[1]
        order_data = json.loads(redis_client.get(key))

        if order_data.get("customer") == customer_number:
            if order_data.get("status") in ["Pending", "Preparing", "On the Way"]:
                active_orders.append({
                    "Order ID": order_id,
                    "Branch": order_data.get("branch"),
                    "Total": order_data.get("total"),
                    "Status": order_data.get("status")
                })
    return active_orders