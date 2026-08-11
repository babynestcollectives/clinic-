import streamlit as st
import pandas as pd
from datetime import date
from core.clinic_db import (
    get_all_patients, get_patient_invoices, create_invoice, add_payment, 
    get_invoice, get_all_invoices, get_revenue_summary, add_expense, 
    get_recent_expenses, get_expenses_in_range, add_external_income, 
    get_recent_external_income, get_external_income_in_range, 
    get_payments_in_range, get_unpaid_invoices, get_invoices_in_range, 
    add_billing_item, update_invoice_status, get_outstanding_balance
)
from core.utils import CURRENCY, fmt_currency, BILLING_CATEGORIES, PAYMENT_METHODS, EXPENSE_CATEGORIES

def render():
    st.markdown("# 💰 Accounting & Billing")
    
    t_dash, t_inv, t_pay, t_inc, t_exp = st.tabs([
        "📊 Dashboard", "📝 New Invoice", "💳 Payments", "➕ Other Income", "📉 Expenses"
    ])
    
    with t_dash:
        render_dashboard()
        
    with t_inv:
        render_new_invoice()
        
    with t_pay:
        render_payments()
        
    with t_inc:
        render_external_income()
        
    with t_exp:
        render_expenses()

def render_dashboard():
    st.markdown("### 📅 Filter Period")
    filter_type = st.radio("Select Period", ["Today", "This Month", "This Year", "All Time", "Custom Range"], horizontal=True, label_visibility="collapsed")
    
    today_dt = date.today()
    if filter_type == "Today":
        start_str = str(today_dt)
        end_str = str(today_dt)
    elif filter_type == "This Month":
        start_str = str(today_dt.replace(day=1))
        end_str = str(today_dt)
    elif filter_type == "This Year":
        start_str = str(today_dt.replace(month=1, day=1))
        end_str = str(today_dt)
    elif filter_type == "All Time":
        start_str = "1900-01-01"
        end_str = "2100-01-01"
    elif filter_type == "Custom Range":
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Start Date", today_dt)
        end_date = c2.date_input("End Date", today_dt)
        start_str = str(start_date)
        end_str = str(end_date)
        
    st.markdown("---")
    
    # Quick Stats
    today_rev = get_payments_in_range(start_str, end_str) or 0
    today_ext_inc = get_external_income_in_range(start_str, end_str) or 0
    total_rev = today_rev + today_ext_inc
    
    total_out = get_outstanding_balance() or 0
    today_exp = get_expenses_in_range(start_str, end_str) or 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{fmt_currency(total_rev)}</div>
        <div class="metric-label">Period Revenue</div>
    </div>""", unsafe_allow_html=True)
    
    c2.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #d9534f;">{fmt_currency(total_out)}</div>
        <div class="metric-label">Outstanding Balance (All)</div>
    </div>""", unsafe_allow_html=True)
    
    c3.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #f0ad4e;">{fmt_currency(today_exp)}</div>
        <div class="metric-label">Period Expenses</div>
    </div>""", unsafe_allow_html=True)
    
    net_profit = total_rev - today_exp
    net_color = "#5cb85c" if net_profit >= 0 else "#d9534f"
    c4.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {net_color};">{fmt_currency(net_profit)}</div>
        <div class="metric-label">Period Net Profit</div>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent Invoices
    st.markdown("### Invoices for Period")
    invoices = get_invoices_in_range(start_str, end_str)
    
    if invoices:
        df_inv = pd.DataFrame(invoices)
        df_inv["balance"] = df_inv["net_amount"] - df_inv["paid"]
        
        # Format for display
        df_display = df_inv.copy()
        df_display["net_amount"] = df_display["net_amount"].apply(lambda x: fmt_currency(x))
        df_display["paid"] = df_display["paid"].apply(lambda x: fmt_currency(x))
        df_display["balance"] = df_display["balance"].apply(lambda x: fmt_currency(x))
        
        cols_to_show = ["id", "patient", "invoice_date", "net_amount", "paid", "balance", "status", "payment_method"]
        st.dataframe(df_display[[c for c in cols_to_show if c in df_display.columns]], use_container_width=True, hide_index=True)
    else:
        st.info("No invoices found.")

def render_new_invoice():
    patients = get_all_patients()
    if not patients:
        st.warning("Please add patients before creating an invoice.")
        return
    
    st.markdown("### Search Patient")
    search_term = st.text_input("Type name or phone to filter", key="inv_pt_search").lower()
    
    if search_term:
        filtered = [p for p in patients if search_term in p['name'].lower() or (p.get('phone') and search_term in p['phone'])]
    else:
        filtered = patients
    
    if not filtered:
        st.warning("No patients match your search.")
        return
        
    pt_options = {p['id']: f"{p['name']} - {p.get('phone','')} ({p.get('insurance') if p.get('is_insured') else 'Cash'})" for p in filtered}
    
    with st.form("new_invoice_form"):
        pid = st.selectbox("Select Patient *", options=list(pt_options.keys()), format_func=lambda x: pt_options[x])
        
        c1, c2 = st.columns(2)
        inv_date = c1.date_input("Invoice Date")
        
        pt = next((p for p in filtered if p['id'] == pid), None)
        payment_type = "Insurance" if pt and pt.get("is_insured") else "Cash"
        pmt_method = c2.selectbox("Expected Payment Method", PAYMENT_METHODS, index=PAYMENT_METHODS.index(payment_type) if payment_type in PAYMENT_METHODS else 0)
        
        st.markdown("### Line Items")
        
        items = []
        for i in range(3):
            st.markdown(f"**Item {i+1}**")
            col_cat, col_desc, col_qty, col_price = st.columns([2, 3, 1, 1])
            cat = col_cat.selectbox(f"Category {i}", BILLING_CATEGORIES, key=f"cat_{i}", label_visibility="collapsed")
            desc = col_desc.text_input(f"Description {i}", placeholder="Description", key=f"desc_{i}", label_visibility="collapsed")
            qty = col_qty.number_input(f"Qty {i}", min_value=1, value=1, step=1, key=f"qty_{i}", label_visibility="collapsed")
            price = col_price.number_input(f"Unit Price {i}", min_value=0.0, value=0.0, step=0.5, key=f"price_{i}", label_visibility="collapsed")
            items.append({"category": cat, "description": desc, "quantity": qty, "unit_price": price})
            
        c_disc, c_pad = st.columns([1, 3])
        discount = c_disc.number_input("Discount Amount", min_value=0.0, value=0.0, step=1.0)
        
        if st.form_submit_button("💾 Generate Invoice", type="primary"):
            valid_items = [item for item in items if item["description"].strip() and item["unit_price"] > 0]
            if not valid_items:
                st.error("Please add at least one valid line item with a description and price.")
            else:
                total_amt = sum(item["quantity"] * item["unit_price"] for item in valid_items)
                net_amt = total_amt - discount
                
                inv_data = {
                    "patient_id": pid,
                    "invoice_date": str(inv_date),
                    "total_amount": total_amt,
                    "discount": discount,
                    "net_amount": net_amt,
                    "payment_method": pmt_method,
                    "insurance_company": pt.get("insurance") if pt else "",
                    "status": "Unpaid"
                }
                
                inv_id = create_invoice(inv_data)
                
                for item in valid_items:
                    item_data = {
                        "invoice_id": inv_id,
                        "category": item["category"],
                        "description": item["description"],
                        "quantity": item["quantity"],
                        "unit_price": item["unit_price"],
                        "total_price": item["quantity"] * item["unit_price"]
                    }
                    add_billing_item(item_data)
                    
                st.success(f"Invoice #{inv_id} generated successfully!")
                st.rerun()

def render_payments():
    st.markdown("### Record Payment")
    
    unpaid_list = get_unpaid_invoices()
    
    # Filter those with actual outstanding balance
    unpaid_list = [i for i in unpaid_list if (i["net_amount"] - i.get("paid", 0)) > 0]
    
    if not unpaid_list:
        st.info("No unpaid invoices.")
    else:
        inv_options = {i["id"]: f"Inv #{i['id']} - {i['name']} (Balance: {fmt_currency(i['net_amount'] - i.get('paid', 0))})" for i in unpaid_list}
        
        with st.form("payment_form"):
            inv_id = st.selectbox("Select Invoice", options=list(inv_options.keys()), format_func=lambda x: inv_options[x])
            selected_inv = next(i for i in unpaid_list if i["id"] == inv_id)
            balance = selected_inv["net_amount"] - selected_inv.get("paid", 0)
            
            c1, c2, c3 = st.columns(3)
            pmt_date = c1.date_input("Payment Date")
            amount = c2.number_input("Amount", min_value=0.1, max_value=float(balance), value=float(balance), step=1.0)
            pmt_method = c3.selectbox("Payment Method", PAYMENT_METHODS)
            
            ref = st.text_input("Reference No. (Cheque / Transfer / Card Approval Code)")
            
            if st.form_submit_button("💳 Receive Payment", type="primary"):
                pmt_data = {
                    "invoice_id": inv_id,
                    "payment_date": str(pmt_date),
                    "amount": amount,
                    "payment_method": pmt_method,
                    "reference_no": ref
                }
                add_payment(pmt_data)
                
                # Check if fully paid
                new_paid = selected_inv.get("paid", 0) + amount
                if new_paid >= selected_inv["net_amount"]:
                    update_invoice_status(inv_id, 'Paid')
                else:
                    update_invoice_status(inv_id, 'Partial')
                    
                st.success("Payment recorded!")
                st.rerun()

def render_expenses():
    st.markdown("### Log Expense")
    
    with st.form("expense_form"):
        c1, c2, c3 = st.columns(3)
        exp_date = c1.date_input("Date")
        category = c2.selectbox("Category", EXPENSE_CATEGORIES)
        amount = c3.number_input("Amount", min_value=0.0, value=0.0, step=1.0)
        
        desc = st.text_input("Description")
        
        if st.form_submit_button("📉 Save Expense"):
            if amount <= 0 or not desc.strip():
                st.error("Amount must be > 0 and description is required.")
            else:
                exp_data = {
                    "expense_date": str(exp_date),
                    "category": category,
                    "description": desc,
                    "amount": amount
                }
                add_expense(exp_data)
                st.success("Expense logged!")
                st.rerun()
                
    st.markdown("---")
    st.markdown("### Recent Expenses")
    expenses = get_recent_expenses(10)
    
    if expenses:
        df_exp = pd.DataFrame(expenses)
        df_exp["amount"] = df_exp["amount"].apply(lambda x: fmt_currency(x))
        st.dataframe(df_exp[["expense_date", "category", "description", "amount"]], use_container_width=True, hide_index=True)
    else:
        st.info("No expenses logged.")

def render_external_income():
    st.markdown("### Log Other Income")
    
    with st.form("income_form"):
        c1, c2, c3 = st.columns(3)
        inc_date = c1.date_input("Date")
        source = c2.text_input("Source / Patient")
        amount = c3.number_input("Amount", min_value=0.0, value=0.0, step=1.0)
        
        desc = st.text_input("Description")
        
        if st.form_submit_button("💰 Save Income"):
            if amount <= 0 or not source.strip():
                st.error("Amount must be > 0 and source is required.")
            else:
                inc_data = {
                    "income_date": str(inc_date),
                    "source": source,
                    "description": desc,
                    "amount": amount
                }
                add_external_income(inc_data)
                st.success("Income logged!")
                st.rerun()
                
    st.markdown("---")
    st.markdown("### Recent Other Income")
    incomes = get_recent_external_income(10)
    
    if incomes:
        df_inc = pd.DataFrame(incomes)
        df_inc["amount"] = df_inc["amount"].apply(lambda x: fmt_currency(x))
        st.dataframe(df_inc[["income_date", "source", "description", "amount"]], use_container_width=True, hide_index=True)
    else:
        st.info("No external income logged.")

if __name__ == '__main__':
    render()
