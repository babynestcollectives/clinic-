import streamlit as st
import pandas as pd
import plotly.express as px
from core.clinic_db import (
    get_all_patients, get_all_visits, get_all_surgeries, get_all_procedures_log,
    get_all_invoices, get_all_payments, get_all_expenses
)
from core.utils import fmt_currency

def render():
    st.markdown("# 📊 Analytics & Reporting")
    
    # Fetch all data once for analytics
    patients = get_all_patients()
    visits = get_all_visits()
    surgeries = get_all_surgeries()
    procedures = get_all_procedures_log()
    invoices = get_all_invoices()
    payments = get_all_payments()
    expenses = get_all_expenses()
    
    # ── Overview Metrics ──
    total_pts = len(patients)
    total_vis = len(visits)
    total_surg = len(surgeries)
    total_procs = len(procedures)
    
    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    c_m1.metric("Total Patients", total_pts)
    c_m2.metric("Total Visits", total_vis)
    c_m3.metric("Total Surgeries", total_surg)
    c_m4.metric("Total Procedures", total_procs)
    
    st.markdown("---")
    
    # ── Payment Breakdown Pie Charts ──
    st.markdown("## 💳 Payment Breakdown")
    
    pc1, pc2 = st.columns(2)
    
    with pc1:
        st.markdown("### Cash vs Insurance (Patients)")
        if patients:
            df_ins = pd.DataFrame(patients)
            df_ins['type'] = df_ins['is_insured'].apply(lambda x: 'Insured' if str(x) in ['1', 'True', 'true', True] else 'Cash')
            ins_counts = df_ins['type'].value_counts().reset_index()
            ins_counts.columns = ['type', 'count']
            
            if not ins_counts.empty:
                fig = px.pie(ins_counts, values='count', names='type', 
                             color_discrete_sequence=['#1a5fa8', '#5cb85c'],
                             hole=0.4)
                fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data.")
        else:
            st.info("Not enough data.")
    
    with pc2:
        st.markdown("### Revenue by Insurance Company")
        if invoices:
            df_inv = pd.DataFrame(invoices)
            # Company processing
            def get_company(row):
                co = row.get('insurance_company')
                if pd.isna(co) or not str(co).strip():
                    return 'Cash / Direct'
                return str(co).strip()
            df_inv['company'] = df_inv.apply(get_company, axis=1)
            # Summarize by company
            df_inv['net_amount'] = pd.to_numeric(df_inv.get('net_amount', 0), errors='coerce').fillna(0)
            co_revenue = df_inv.groupby('company')['net_amount'].sum().reset_index()
            co_revenue = co_revenue.rename(columns={'net_amount': 'total'}).sort_values('total', ascending=False)
            
            if not co_revenue.empty:
                fig2 = px.pie(co_revenue, values='total', names='company', hole=0.4)
                fig2.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Not enough data.")
        else:
            st.info("Not enough data.")
    
    pc3, pc4 = st.columns(2)
    
    with pc3:
        st.markdown("### Revenue by Payment Method")
        if payments:
            df_pay = pd.DataFrame(payments)
            df_pay['amount'] = pd.to_numeric(df_pay.get('amount', 0), errors='coerce').fillna(0)
            pay_revenue = df_pay.groupby('payment_method')['amount'].sum().reset_index()
            pay_revenue = pay_revenue.rename(columns={'amount': 'total'})
            
            if not pay_revenue.empty:
                fig3 = px.pie(pay_revenue, values='total', names='payment_method', hole=0.4)
                fig3.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Not enough data.")
        else:
            st.info("Not enough data.")
    
    with pc4:
        st.markdown("### Expenses by Category")
        if expenses:
            df_exp = pd.DataFrame(expenses)
            df_exp['amount'] = pd.to_numeric(df_exp.get('amount', 0), errors='coerce').fillna(0)
            exp_cat = df_exp.groupby('category')['amount'].sum().reset_index()
            exp_cat = exp_cat.rename(columns={'amount': 'total'}).sort_values('total', ascending=False)
            
            if not exp_cat.empty:
                fig4 = px.pie(exp_cat, values='total', names='category', hole=0.4)
                fig4.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Not enough data.")
        else:
            st.info("Not enough data.")
    
    st.markdown("---")
    
    # ── Clinical Charts ──
    st.markdown("## 🏥 Clinical Statistics")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### Top Diagnoses")
        if visits:
            df_v = pd.DataFrame(visits)
            if 'diagnosis' in df_v.columns:
                diags = df_v['diagnosis'].dropna().astype(str).tolist()
                diag_counts = {}
                for diag_str in diags:
                    if not diag_str.strip():
                        continue
                    parts = [d.strip() for d in diag_str.split('+') if d.strip()]
                    for p in parts:
                        key = p.lower()
                        if key not in diag_counts:
                            diag_counts[key] = {"name": p, "count": 0}
                        diag_counts[key]["count"] += 1
                
                sorted_diags = sorted(diag_counts.values(), key=lambda x: x["count"], reverse=True)[:10]
                if sorted_diags:
                    df_diag = pd.DataFrame([{"diagnosis": d["name"], "cnt": d["count"]} for d in sorted_diags])
                    st.bar_chart(df_diag.set_index("diagnosis"))
                else:
                    st.info("Not enough data.")
            else:
                st.info("Not enough data.")
        else:
            st.info("Not enough data.")
            
    with c2:
        st.markdown("### Surgery Types Distribution")
        if surgeries:
            df_surg = pd.DataFrame(surgeries)
            if 'surgery_type' in df_surg.columns:
                surg_counts = df_surg['surgery_type'].value_counts().reset_index()
                surg_counts.columns = ['surgery_type', 'cnt']
                surg_counts = surg_counts.head(10)
                if not surg_counts.empty:
                    st.bar_chart(surg_counts.set_index("surgery_type"))
                else:
                    st.info("Not enough data.")
            else:
                st.info("Not enough data.")
        else:
            st.info("Not enough data.")
            
    c3, c4 = st.columns(2)
    
    with c3:
        st.markdown("### Visits per Month")
        if visits:
            df_vm = pd.DataFrame(visits)
            if 'visit_date' in df_vm.columns:
                df_vm['month'] = df_vm['visit_date'].astype(str).str[:7]
                vm_counts = df_vm['month'].value_counts().reset_index()
                vm_counts.columns = ['month', 'cnt']
                vm_counts = vm_counts.sort_values('month', ascending=False).head(12).sort_values('month')
                if not vm_counts.empty:
                    st.line_chart(vm_counts.set_index("month"))
                else:
                    st.info("Not enough data.")
            else:
                st.info("Not enough data.")
        else:
            st.info("Not enough data.")
    
    with c4:
        st.markdown("### Top Referring Insurance Companies")
        if patients:
            df_pt = pd.DataFrame(patients)
            insured = df_pt[(df_pt['is_insured'].astype(str).isin(['1', 'True', 'true'])) & (df_pt['insurance'].notna()) & (df_pt['insurance'] != '')]
            if not insured.empty:
                top_ins = insured['insurance'].value_counts().reset_index()
                top_ins.columns = ['company', 'patients']
                top_ins = top_ins.head(10)
                if not top_ins.empty:
                    st.bar_chart(top_ins.set_index("company"))
                else:
                    st.info("Not enough data.")
            else:
                st.info("Not enough data.")
        else:
            st.info("Not enough data.")
    
    st.markdown("---")
    
    # ── Financial Trend ──
    st.markdown("## 💰 Financial Trend")
    
    monthly_rev = []
    if payments:
        df_pay = pd.DataFrame(payments)
        df_pay['month'] = df_pay['payment_date'].astype(str).str[:7]
        df_pay['amount'] = pd.to_numeric(df_pay.get('amount', 0), errors='coerce').fillna(0)
        pay_month = df_pay.groupby('month')['amount'].sum().reset_index()
        monthly_rev = pay_month.to_dict('records')
        
    monthly_exp_list = []
    if expenses:
        df_exp = pd.DataFrame(expenses)
        df_exp['month'] = df_exp['expense_date'].astype(str).str[:7]
        df_exp['amount'] = pd.to_numeric(df_exp.get('amount', 0), errors='coerce').fillna(0)
        exp_month = df_exp.groupby('month')['amount'].sum().reset_index()
        monthly_exp_list = exp_month.to_dict('records')
    
    if monthly_rev or monthly_exp_list:
        rev_dict = {r['month']: r['amount'] for r in monthly_rev}
        exp_dict = {r['month']: r['amount'] for r in monthly_exp_list}
        all_months = sorted(set(list(rev_dict.keys()) + list(exp_dict.keys())))[-12:]
        
        df_monthly = pd.DataFrame({
            "month": all_months,
            "Revenue": [rev_dict.get(m, 0) for m in all_months],
            "Expenses": [exp_dict.get(m, 0) for m in all_months],
        })
        df_monthly["Net Profit"] = df_monthly["Revenue"] - df_monthly["Expenses"]
        st.line_chart(df_monthly.set_index("month"))
        
        total_revenue = sum(rev_dict.values())
        total_expenses = sum(exp_dict.values())
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Total Revenue", fmt_currency(total_revenue))
        sc2.metric("Total Expenses", fmt_currency(total_expenses))
        sc3.metric("Net Profit", fmt_currency(total_revenue - total_expenses))
    else:
        st.info("Not enough financial data to chart.")
    
    st.markdown("---")
    
    # ── Data Export ──
    st.markdown("### Data Export")
    
    df_pts_export = pd.DataFrame(patients) if patients else pd.DataFrame()
    df_vis_export = pd.DataFrame(visits) if visits else pd.DataFrame()
    df_surg_export = pd.DataFrame(surgeries) if surgeries else pd.DataFrame()
    df_exp_export = pd.DataFrame(expenses) if expenses else pd.DataFrame()
    df_pay_export = pd.DataFrame(payments) if payments else pd.DataFrame()
    
    col1, col2, col3 = st.columns(3)
    col1.download_button("⬇ Patients (CSV)", df_pts_export.to_csv(index=False).encode() if not df_pts_export.empty else b"",
                          file_name="patients.csv", mime="text/csv", use_container_width=True)
    col2.download_button("⬇ Visits (CSV)", df_vis_export.to_csv(index=False).encode() if not df_vis_export.empty else b"",
                          file_name="visits.csv", mime="text/csv", use_container_width=True)
    col3.download_button("⬇ Surgeries (CSV)", df_surg_export.to_csv(index=False).encode() if not df_surg_export.empty else b"",
                          file_name="surgeries.csv", mime="text/csv", use_container_width=True)
    
    col4, col5 = st.columns(2)
    col4.download_button("⬇ Expenses (CSV)", df_exp_export.to_csv(index=False).encode() if not df_exp_export.empty else b"",
                          file_name="expenses.csv", mime="text/csv", use_container_width=True)
    col5.download_button("⬇ Payments (CSV)", df_pay_export.to_csv(index=False).encode() if not df_pay_export.empty else b"",
                          file_name="payments.csv", mime="text/csv", use_container_width=True)

if __name__ == '__main__':
    render()
