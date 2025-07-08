# discount_handler.py
from config.settings import BRANCH_DISCOUNTS

def get_branch_discount(to, branch, get_user_cart_func):
    """
    Calculates discount based on branch and cart total.
    
    Args:
        to: WhatsApp number of user
        branch: Branch name
        get_user_cart_func: Function to retrieve user cart from Redis
    
    Returns:
        dict: Discount info including percent, amount, and final total
    """
    cart = get_user_cart_func(to)  # Call the function to get cart
    total = cart.get("total", 0)
    branch_key = branch.lower()
    discount_percent = BRANCH_DISCOUNTS.get(branch_key, 0)

    discount_amount = (total * discount_percent) // 100
    final_total = total - discount_amount

    return {
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "final_total": final_total
    }