import streamlit as st
import pandas as pd
from datetime import date
from core.clinic_db import get_all_patients, update_appointment_status, get_appointments, add_appointment, get_all_surgeries, add_surgery
from core.utils import SURGERY_TYPES, LATERALITY_OPTIONS

def render():
    st.markdown("# 🗓 Appointments & Surgery Booking")
    
    t_today, t_book, t_surg, t_book_surg = st.tabs([
        "📅 Today's Appointments", "➕ Book Appointment", 
        "🔪 Surgery Schedule", "➕ Schedule Surgery"
    ])
    
    with t_today:
        render_schedule()
        
    with t_book:
        render_booking()
        
    with t_surg:
        render_surgery_list()
        
    with t_book_surg:
        render_new_surgery()

def render_schedule():
    selected_date = st.date_input("Select Date", value=date.today(), key="apt_date_sel")
    
    apts = get_appointments(str(selected_date))
    
    if apts:
        for a_dict in apts:
            with st.expander(f"🕐 {a_dict['appointment_time'] or '—'}  ·  **{a_dict['patient_name']}**  ·  {a_dict['reason'] or ''}  [{a_dict['status']}]"):
                st.write(f"**Phone:** {a_dict['patient_phone'] or '—'}")
                st.write(f"**Reason:** {a_dict['reason'] or '—'}")
                st.write(f"**Current Status:** {a_dict['status']}")
                
                c1, c2 = st.columns(2)
                with c1:
                    new_status = st.selectbox(
                        "Update Status", 
                        ["Scheduled", "Arrived", "In Progress", "Completed", "No-Show", "Cancelled"],
                        index=["Scheduled", "Arrived", "In Progress", "Completed", "No-Show", "Cancelled"].index(a_dict['status']) if a_dict['status'] in ["Scheduled", "Arrived", "In Progress", "Completed", "No-Show", "Cancelled"] else 0,
                        key=f"status_{a_dict['id']}"
                    )
                    if st.button("✅ Update", key=f"upd_{a_dict['id']}"):
                        update_appointment_status(a_dict['id'], new_status)
                        st.success(f"Status updated to {new_status}")
                        st.rerun()
                with c2:
                    if a_dict.get('patient_id'):
                        st.write("")
                        st.write("")
                        if st.button("📂 Open Patient File", key=f"open_pt_{a_dict['id']}", use_container_width=True):
                            st.session_state.selected_patient = a_dict['patient_id']
                            st.session_state.page = "patient_detail"
                            st.switch_page("pages/clinic/2_patients.py")
    else:
        st.info("No appointments scheduled for this date.")

def render_booking():
    patients = get_all_patients()
    
    st.markdown("### Search Patient")
    search_term = st.text_input("Type name or phone number to filter patients list", key="apt_pt_search").lower()
    
    if search_term:
        filtered_patients = [p for p in patients if search_term in p['name'].lower() or (p['phone'] and search_term in p['phone'])]
    else:
        filtered_patients = patients
        
    pt_options = {p['id']: f"{p['name']} - {p.get('phone', 'No Phone')}" for p in filtered_patients}
    
    with st.form("book_apt_form"):
        is_new = st.checkbox("New Patient (Not in system yet)")
        
        if is_new:
            pt_name = st.text_input("Patient Name *")
            pt_phone = st.text_input("Patient Phone")
            pid = None
        else:
            if not filtered_patients:
                st.warning("No patients match your search. Please check 'New Patient'.")
                return
            pid = st.selectbox("Select Patient *", options=list(pt_options.keys()), format_func=lambda x: pt_options[x])
            pt = next(p for p in filtered_patients if p['id'] == pid)
            pt_name = pt['name']
            pt_phone = pt['phone']
            
        c1, c2 = st.columns(2)
        apt_date = c1.date_input("Date *", value=date.today(), key="apt_book_date")
        apt_time = c2.time_input("Time")
        
        reason = st.text_input("Reason for Visit")
        
        if st.form_submit_button("💾 Book Appointment", type="primary"):
            if is_new and not pt_name.strip():
                st.error("Patient name is required.")
            else:
                add_appointment({
                    "patient_id": pid, "patient_name": pt_name, "patient_phone": pt_phone, 
                    "appointment_date": str(apt_date), "appointment_time": str(apt_time)[:5], 
                    "reason": reason, "status": "Scheduled"
                })
                st.success("Appointment booked!")
                st.rerun()

def render_surgery_list():
    surgeries = get_all_surgeries()
    
    if surgeries:
        df = pd.DataFrame(surgeries)
        st.dataframe(df[["id", "patient", "surgery_date", "surgery_type", "laterality", "status", "approach"]], use_container_width=True, hide_index=True)
    else:
        st.info("No surgeries scheduled or logged.")

def render_new_surgery():
    patients = get_all_patients()
    if not patients:
        st.warning("Please add patients first.")
        return
        
    st.markdown("### Surgical Booking")
    search_term = st.text_input("Type name or phone number to filter patients list", key="surg_pt_search").lower()
    
    if search_term:
        filtered_patients = [p for p in patients if search_term in p['name'].lower() or (p['phone'] and search_term in p['phone'])]
    else:
        filtered_patients = patients
        
    if not filtered_patients:
        st.warning("No patients match your search.")
        return
        
    pt_options = {p['id']: f"{p['name']} - {p.get('phone', 'No Phone')}" for p in filtered_patients}
    
    with st.form("new_surgery_form"):
        pid = st.selectbox("Select Patient *", options=list(pt_options.keys()), format_func=lambda x: pt_options[x], key="surg_pt")
        
        c1, c2, c3 = st.columns(3)
        surg_date = c1.date_input("Date *", value=date.today(), key="surg_date")
        surg_type = c2.selectbox("Surgery Type *", SURGERY_TYPES)
        laterality = c3.selectbox("Side", LATERALITY_OPTIONS)
        
        status = st.selectbox("Status", ["Scheduled", "Completed", "Cancelled"])
        
        st.markdown("### Operative Details")
        c4, c5 = st.columns(2)
        assistant = c4.text_input("Assistant")
        anesthesia = c5.selectbox("Anesthesia", ["General", "Spinal", "Regional Block", "Local"])
        
        preop = st.text_input("Pre-operative Diagnosis")
        postop = st.text_input("Post-operative Diagnosis (if completed)")
        
        st.markdown("### Surgical Notes")
        approach = st.text_area("Approach", height=80)
        findings = st.text_area("Intra-operative Findings", height=100)
        closure = st.text_area("Closure / Drains", height=80)
        
        if st.form_submit_button("💾 Save Surgery", type="primary"):
            add_surgery({
                "patient_id": pid, "surgery_date": str(surg_date), "surgery_type": surg_type, 
                "laterality": laterality, "status": status, "assistant": assistant, 
                "anesthesia_type": anesthesia, "preop_diagnosis": preop, 
                "postop_diagnosis": postop, "approach": approach, 
                "findings": findings, "closure": closure
            })
            st.success("Surgery record created!")
            st.rerun()


if __name__ == '__main__':
    render()
