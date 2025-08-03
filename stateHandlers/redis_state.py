# stateHandlers/redis_state.py

from datetime import datetime
from pytz import timezone 
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
    """
    Add or update a pending order in Redis with a created_at timestamp.
    """
    try:
        # Add created_at timestamp if not already present
        if 'created_at' not in order_data:
            order_data['created_at'] = datetime.utcnow().isoformat()
        redis_client.set(f"order:{order_id.upper()}", json.dumps(order_data))
        print(f"[REDIS] Added order {order_id} with status: {order_data.get('status')}")
    except Exception as e:
        print(f"[ERROR] Failed to save order {order_id}: {e}")

def get_pending_orders():
    keys = redis_client.keys("order:*")
    return {key.split(":")[1]: json.loads(redis_client.get(key)) for key in keys} if keys else {}

def get_pending_order(order_id):
    order_id = order_id.strip().upper()
    data = redis_client.get(f"order:{order_id}")
    if not data:
        print(f"[ERROR] Order {order_id} not found in Redis")
        return None
    try:
        return json.loads(data)
    except Exception as e:
        print(f"[ERROR] Failed to parse order {order_id}: {e}")
        return None

def update_pending_order_reminders(order_id, count):
    key = f"order:{order_id}"
    order_data = json.loads(redis_client.get(key))
    order_data["reminders_sent"] = count
    redis_client.set(key, json.dumps(order_data))  # No TTL

def remove_pending_order(order_id):
    # order_id = order_id.strip().upper()
    redis_client.delete(f"order:{order_id.upper()}")


def get_active_orders(customer_number):
    active_orders = []
    for key in redis_client.keys("order:*"):
        order_id = key.split(":")[1]
        try:
            order_data = json.loads(redis_client.get(key))
            if order_data.get("customer") == customer_number:
                status = order_data.get("status", "Pending")
                if status in ["Pending", "Preparing", "On the Way"]:
                    active_orders.append({
                        "Order ID": order_id,
                        "Branch": order_data.get("branch", ""),
                        "Total": order_data.get("total", 0),
                        "Status": status
                    })
        except Exception as e:
            print(f"[ERROR] Redis parse error: {e}")
    return active_orders

def get_pending_orders_for_user(phone):
    """Get all pending orders for a specific user"""
    keys = redis_client.keys("order:*")
    result = {}
    
    for key in keys:
        order_id = key.split(":")[1]
        order_data = json.loads(redis_client.get(key))
        
        if order_data.get("customer") == phone:
            result[order_id] = order_data
            
    return result

# ===== ACTIVE Hours =====

def add_off_hour_user(phone):
    """Add user to today's off-hour list"""
    today = datetime.now(timezone('Asia/Kolkata')).date().isoformat()
    redis_client.sadd(f"off_hour_users:{today}", phone)
    redis_client.expire(f"off_hour_users:{today}", 86400)  # Auto-delete after 24h

def get_off_hour_users(date=None):
    """Get users who messaged during off-hours"""
    if not date:
        date = datetime.now(timezone('Asia/Kolkata')).date().isoformat()
    
    return redis_client.smembers(f"off_hour_users:{date}")

def delete_yesterdays_data(yesterday) :
    # Clear yesterday's data
    redis_client.delete(f"off_hour_users:{yesterday}")

# ===== Feedback ===== #
FEEDBACK_SCHEDULED_KEY = "feedback_scheduled:{}"
def add_scheduled_feedback(to_number, order_id) :
    # Store scheduled feedback for reference
    redis_client.setex(FEEDBACK_SCHEDULED_KEY.format(to_number), 86400, order_id)

def get_scheduled_feedback(phone_number):
    redis_client.get(FEEDBACK_SCHEDULED_KEY.format(phone_number))

def delete_scheduled_feedfack(phone_number):
    # Clean up Redis
    redis_client.delete(FEEDBACK_SCHEDULED_KEY.format(phone_number))

def add_feedback_history(phone, order_id, rating):
    """Track user feedback history"""
    feedback_key = f"feedback_history:{phone}"
    feedback_data = {
        "order_id": order_id,
        "rating": rating,
        "timestamp": get_current_ist_time()
    }
    redis_client.rpush(feedback_key, json.dumps(feedback_data))
    redis_client.expire(feedback_key, 86400 * 30)  # Keep 30 days


def get_current_ist_time():
    ist = timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")


# Get all customers from Redis
def get_all_customers():
    """Get all customers from Redis carts"""
    carts = get_all_carts()
    return set(carts.keys())

# ===== SAVING BRANCH =====
def set_branch(phone, branch_name):
    """Set branch for a user with TTL of 1 day"""
    redis_client.setex(f"user_branch:{phone}", 86400, branch_name)