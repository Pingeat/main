from config.settings import BRANCH_DISCOUNTS


def get_branch_discount(to,branch, user_cart):
    cart = user_cart[to]
    print("[PINTING_CART] : ", cart)
    total = cart.get("total", 0)
    
    # ✅ Discount logic
    branch_key = branch.lower()
    discount_percent = BRANCH_DISCOUNTS.get(branch_key, 0)
    print("[discount_percent] :", discount_percent)
    discount_amount = (total * discount_percent) // 100
    print("[discount_amount] :", discount_amount)
    final_total = total - discount_amount
    print("[final_total]:", final_total)
    return {
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "final_total": final_total
    }