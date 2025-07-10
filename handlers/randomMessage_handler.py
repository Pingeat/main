import re
import json
from pathlib import Path
from services.whatsapp_service import (
    send_selected_catalog_items,
    send_full_catalog
)



def matching(sender,text):
    CART_PRODUCTS = json.loads((Path(__file__).parent.parent / "data" / "products.json").read_text())

    matched_items = []
    matched_items_id = []
    print(text)
    
    

    for id, info in CART_PRODUCTS.items():
        name = info.get("name", "").lower()
        if re.search(re.escape(text), name):
            matched_items.append(f'{info["name"]} - ₹{info["price"]}')
            matched_items_id.append(id)
    
    

    if matched_items:
        send_selected_catalog_items(sender,matched_items_id)
  
    else:
        send_full_catalog(sender)
 
        

        
