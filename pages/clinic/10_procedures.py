import streamlit as st
import pandas as pd
from datetime import date
from core.clinic_db import get_all_patients, get_all_procedures_log, add_procedure_log, delete_procedure_log
from core.utils import PROCEDURE_TYPES, BODY_REGIONS, LATERALITY_OPTIONS

def render():
    st.markdown("# 💉 Procedures Log")
    
    t_log, t_new = st.tabs(["📝 Recent Procedures", "➕ Log New Procedure"])
    
    with t_log:
        render_recent_procedures()
        
    with t_new:
        render_new_procedure()

def render_recent_procedures():
    procs = get_all_procedures_log()
    
    if procs:
        df = pd.DataFrame(procs)
        cols_to_show = ["id", "patient", "procedure_date", "procedure_type", "body_part", "laterality", "medication_used"]
        st.dataframe(df[[c for c in cols_to_show if c in df.columns]], use_container_width=True, hide_index=True)
    else:
        st.info("No procedures logged yet.")

def render_new_procedure():
    patients = get_all_patients()
    if not patients:
        st.warning("Please add patients first.")
        return
    
    st.markdown("### Search Patient")
    search_term = st.text_input("Type name or phone number to filter patients list", key="proc_pt_search").lower()
    
    if search_term:
        filtered_patients = [p for p in patients if search_term in p['name'].lower() or (p.get('phone') and search_term in p['phone'])]
    else:
        filtered_patients = patients
    
    if not filtered_patients:
        st.warning("No patients match your search.")
        return
        
    pt_options = {p['id']: f"{p['name']} - {p.get('phone', 'No Phone')}" for p in filtered_patients}
    
    with st.form("new_procedure_form"):
        pid = st.selectbox("Select Patient *", options=list(pt_options.keys()), format_func=lambda x: pt_options[x])
        
        c1, c2 = st.columns(2)
        proc_date = c1.date_input("Date *", value=date.today())
        proc_type = c2.selectbox("Procedure Type *", PROCEDURE_TYPES)
        
        c3, c4 = st.columns(2)
        body_part = c3.selectbox("Body Region", BODY_REGIONS)
        laterality = c4.selectbox("Side", LATERALITY_OPTIONS)
        
        c5, c6 = st.columns(2)
        meds = c5.text_input("Medication / Material Used", placeholder="e.g. Depo-Medrol 40mg, Cast synthetic")
        lot = c6.text_input("Lot Number / Batch", placeholder="If applicable for implants/injections")
        
        volume = st.text_input("Volume / Dose", placeholder="e.g. 1cc + 1cc Lidocaine")
        
        consent = st.checkbox("Written consent obtained")
        notes = st.text_area("Procedure Notes / Complications", height=100)
        
        if st.form_submit_button("💾 Log Procedure", type="primary"):
            data = {
                "patient_id": pid,
                "procedure_date": str(proc_date),
                "procedure_type": proc_type,
                "body_part": body_part,
                "laterality": laterality,
                "medication_used": meds,
                "lot_number": lot,
                "volume_dose": volume,
                "consent_obtained": 1 if consent else 0,
                "notes": notes
            }
            add_procedure_log(data)
            st.success("Procedure logged successfully!")
            st.rerun()

if __name__ == '__main__':
    render()
