import streamlit as st
import pandas as pd
from core.clinic_db import get_all_inventory, add_inventory_item, update_inventory_item, delete_inventory_item, get_low_stock_items
from core.utils import fmt_currency

INVENTORY_CATEGORIES = ["Implant", "Medication", "Injection Material", "Casting / Splinting", "Surgical Supply", "Office Supply", "Other"]

def render():
    st.markdown("# 📦 Inventory & Implants")
    
    t_list, t_new = st.tabs(["📋 Current Stock", "➕ Add Item"])
    
    with t_list:
        render_stock()
        
    with t_new:
        render_add_item()

def render_stock():
    items = get_all_inventory()
    
    if items:
        # Low stock alerts
        low_stock = get_low_stock_items()
        if low_stock:
            st.warning(f"⚠️ {len(low_stock)} item(s) below minimum stock level!")
        
        for item in items:
            item_dict = dict(item)
            stock_warning = " ⚠️ LOW" if (item_dict.get('current_stock') or 0) <= (item_dict.get('min_stock_alert') or 0) else ""
            with st.expander(f"**{item_dict.get('item_name', '')}** — {item_dict.get('category', '')}  ·  Stock: {item_dict.get('current_stock', 0)}{stock_warning}"):
                st.write(f"**Supplier:** {item_dict.get('supplier') or '—'}")
                st.write(f"**Cost:** {fmt_currency(item_dict.get('cost_price', 0))}  ·  **Selling:** {fmt_currency(item_dict.get('selling_price', 0))}")
                st.write(f"**Expiry:** {item_dict.get('expiry_date') or 'N/A'}")
                
                st.markdown("---")
                
                # Quick stock update
                with st.form(f"edit_inv_{item_dict.get('id')}"):
                    st.markdown("**Edit Item**")
                    ec1, ec2 = st.columns(2)
                    e_name = ec1.text_input("Name", value=item_dict.get('item_name', ''), key=f"en_{item_dict.get('id')}")
                    e_cat = ec2.selectbox("Category", INVENTORY_CATEGORIES,
                                          index=INVENTORY_CATEGORIES.index(item_dict.get('category', '')) if item_dict.get('category') in INVENTORY_CATEGORIES else 0,
                                          key=f"ec_{item_dict.get('id')}")
                    e_supplier = st.text_input("Supplier", value=item_dict.get('supplier') or "", key=f"es_{item_dict.get('id')}")
                    ec3, ec4 = st.columns(2)
                    e_cost = ec3.number_input("Cost Price", value=float(item_dict.get('cost_price', 0)), min_value=0.0, step=0.5, key=f"ecp_{item_dict.get('id')}")
                    e_sell = ec4.number_input("Selling Price", value=float(item_dict.get('selling_price', 0)), min_value=0.0, step=0.5, key=f"esp_{item_dict.get('id')}")
                    ec5, ec6 = st.columns(2)
                    e_stock = ec5.number_input("Current Stock", value=int(item_dict.get('current_stock', 0)), min_value=0, step=1, key=f"est_{item_dict.get('id')}")
                    e_alert = ec6.number_input("Min Stock Alert", value=int(item_dict.get('min_stock_alert', 0)), min_value=0, step=1, key=f"eal_{item_dict.get('id')}")
                    
                    fc1, fc2 = st.columns(2)
                    if fc1.form_submit_button("💾 Save Changes"):
                        update_inventory_item(item_dict.get('id'), {
                            'item_name': e_name, 'category': e_cat, 'supplier': e_supplier,
                            'cost_price': e_cost, 'selling_price': e_sell,
                            'current_stock': e_stock, 'min_stock_alert': e_alert,
                            'expiry_date': item_dict.get('expiry_date')
                        })
                        st.success("Item updated!")
                        st.rerun()
                
                if st.button("🗑 Delete Item", key=f"di_{item_dict.get('id')}"):
                    delete_inventory_item(item_dict.get('id'))
                    st.rerun()
    else:
        st.info("Inventory is empty.")

def render_add_item():
    with st.form("new_inventory_form"):
        c1, c2 = st.columns(2)
        item_name = c1.text_input("Item Name *")
        category = c2.selectbox("Category", INVENTORY_CATEGORIES)
        
        supplier = st.text_input("Supplier / Manufacturer")
        
        c3, c4 = st.columns(2)
        cost_price = c3.number_input("Cost Price", min_value=0.0, step=0.5)
        selling_price = c4.number_input("Selling Price", min_value=0.0, step=0.5)
        
        c5, c6 = st.columns(2)
        stock = c5.number_input("Initial Stock Quantity", min_value=0, step=1)
        alert = c6.number_input("Low Stock Alert Threshold", min_value=0, step=1, value=5)
        
        expiry = st.date_input("Expiry Date (If applicable)", value=None)
        
        if st.form_submit_button("💾 Add Item", type="primary"):
            if not item_name.strip():
                st.error("Item name is required.")
            else:
                data = {
                    "item_name": item_name,
                    "category": category,
                    "supplier": supplier,
                    "cost_price": cost_price,
                    "selling_price": selling_price,
                    "current_stock": stock,
                    "min_stock_alert": alert,
                    "expiry_date": str(expiry) if expiry else None
                }
                add_inventory_item(data)
                st.success("Item added to inventory!")
                st.rerun()

if __name__ == '__main__':
    render()
