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