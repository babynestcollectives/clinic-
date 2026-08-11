import streamlit as st
from datetime import date
from core.clinic_db import (get_patient, get_visit, save_visit, get_distinct_procedure_types, 
                       get_visit_procedures, delete_visit_procedures, add_procedure_log, 
                       create_invoice, create_billing_item, add_payment)
from core.utils import BODY_REGIONS, BILLING_CATEGORIES, PAYMENT_METHODS, calc_age, PROCEDURE_TYPES

def render():
    current_page = st.session_state.get("page", "")
    
    if current_page not in ["new_visit", "print_visit"] or not st.session_state.get("selected_patient"):
        st.info("👋 Please select a patient from the **Patients** tab to create or view visits.")
        # Provide a quick link to jump to the Patients page
        if st.button("Go to Patients"):
            st.switch_page("pages/clinic/2_patients.py")
        return

    if current_page == "new_visit":
        render_new_visit()
    elif current_page == "print_visit":
        render_print_visit()

def render_new_visit():
    pid = st.session_state.selected_patient
    pt = get_patient(pid)
    
    # Check if we're editing an existing visit
    edit_vid = st.session_state.get("edit_visit_id")
    existing = get_visit(edit_vid) if edit_vid else None
    
    if existing:
        st.markdown(f"# ✏️ Edit Visit — {pt['name']}")
    else:
        st.markdown(f"# ➕ New Visit — {pt['name']}")
    
    if st.button("← Back to Patient"):
        st.session_state.pop("edit_visit_id", None)
        st.session_state.page = "patient_detail"
        st.rerun()

    template = st.selectbox("📝 Select Orthopedic Template", ["General"] + BODY_REGIONS,
                             index=(["General"] + BODY_REGIONS).index(existing.get("template_used", "General")) if existing else 0)
    st.markdown("---")

    with st.form("new_visit_form"):
        c1, c2 = st.columns([1, 2])
        visit_date = c1.text_input("Visit Date *", value=existing.get("visit_date", str(date.today())) if existing else str(date.today()), placeholder="YYYY-MM-DD")
        reason = c2.text_input("Chief Complaint / Reason *", value=existing.get("reason", "") if existing else "", placeholder="e.g. Right knee pain...")
        
        injury_mech = st.text_input("Injury Mechanism (if applicable)", value=existing.get("injury_mechanism", "") if existing else "", placeholder="Fall, twisting, sports injury...")

        t_hist, t_exam, t_img, t_plan, t_bill = st.tabs(["📝 History","🩺 Examination","🔬 Imaging","💊 Treatment Plan","💰 Billing"])
        
        with t_hist:
            history = st.text_area("History of Present Illness", value=existing.get("history", "") if existing else "", height=200, placeholder="Onset, duration, character, radiation, exacerbating/relieving factors...")
            
        with t_exam:
            st.markdown(f"**{template} Examination**")
            
            # Common to all orthopedic exams
            examination = st.text_area("General Inspection / Palpation", value=existing.get("examination", "") if existing else "", height=100)
            
            rom_notes = ""
            special_tests = ""
            neuro_notes = ""
            
            if template == "Knee":
                c_rom1, c_rom2 = st.columns(2)
                flexion = c_rom1.text_input("Flexion (degrees)")
                extension = c_rom2.text_input("Extension (degrees)")
                rom_notes = f"Flexion: {flexion}, Extension: {extension}"
                
                st.markdown("**Special Tests (Check if positive)**")
                st.markdown("*Cruciate Ligaments (ACL & PCL)*")
                c_sp1, c_sp2, c_sp3, c_sp4 = st.columns(4)
                lachman = c_sp1.checkbox("Lachman Test")
                ant_drawer = c_sp2.checkbox("Anterior Drawer")
                post_drawer = c_sp3.checkbox("Posterior Drawer")
                pivot_shift = c_sp4.checkbox("Pivot-Shift")
                
                st.markdown("*Collateral Ligaments (MCL & LCL)*")
                c_sp5, c_sp6 = st.columns(2)
                valgus = c_sp5.checkbox("Valgus Stress")
                varus = c_sp6.checkbox("Varus Stress")
                
                st.markdown("*Meniscal Pathology*")
                c_sp7, c_sp8, c_sp9 = st.columns(3)
                mcmurray = c_sp7.checkbox("McMurray Test")
                thessaly = c_sp8.checkbox("Thessaly Test")
                apley = c_sp9.checkbox("Apley's Compression")
                
                other_knee = st.text_input("Other Relative Tests", key="other_knee_tests")

                tests = []
                if lachman: tests.append("Lachman")
                if ant_drawer: tests.append("Ant. Drawer")
                if post_drawer: tests.append("Post. Drawer")
                if pivot_shift: tests.append("Pivot-Shift")
                if valgus: tests.append("Valgus Stress")
                if varus: tests.append("Varus Stress")
                if mcmurray: tests.append("McMurray")
                if thessaly: tests.append("Thessaly")
                if apley: tests.append("Apley's Compression")
                
                special_tests = "Positive: " + ", ".join(tests) if tests else "All negative/normal"
                if other_knee.strip():
                    special_tests += f" | Other: {other_knee.strip()}"
                
            elif template == "Shoulder":
                c_rom1, c_rom2, c_rom3 = st.columns(3)
                forward_flex = c_rom1.text_input("Forward Flexion")
                abduction = c_rom2.text_input("Abduction")
                ext_rot = c_rom3.text_input("External Rotation")
                rom_notes = f"FF: {forward_flex}, Abd: {abduction}, ER: {ext_rot}"
                
                st.markdown("**Special Tests (Check if positive)**")
                st.markdown("*Rotator Cuff Integrity*")
                c_sp1, c_sp2, c_sp3 = st.columns(3)
                jobe = c_sp1.checkbox("Jobe's (Empty Can)")
                er_lag = c_sp2.checkbox("External Rotation Lag")
                gerber = c_sp3.checkbox("Gerber's Lift-Off")
                c_sp4, c_sp5 = st.columns(2)
                belly_press = c_sp4.checkbox("Belly Press")
                hornblower = c_sp5.checkbox("Hornblower's Sign")
                
                st.markdown("*Subacromial Impingement*")
                c_sp6, c_sp7 = st.columns(2)
                neer = c_sp6.checkbox("Neer's Sign")
                hawkins = c_sp7.checkbox("Hawkins-Kennedy")

                st.markdown("*Labral Pathology & Instability*")
                c_sp8, c_sp9 = st.columns(2)
                obrien = c_sp8.checkbox("O'Brien's (Active Compression)")
                apprehension = c_sp9.checkbox("Apprehension/Relocation")

                st.markdown("*ACJ Pathology*")
                scarf = st.checkbox("Scarf Test (Cross-Body Adduction)")

                other_shoulder = st.text_input("Other Relative Tests", key="other_shoulder_tests")
                
                tests = []
                if jobe: tests.append("Jobe's")
                if er_lag: tests.append("ER Lag Sign")
                if gerber: tests.append("Gerber's Lift-Off")
                if belly_press: tests.append("Belly Press")
                if hornblower: tests.append("Hornblower's")
                if neer: tests.append("Neer's")
                if hawkins: tests.append("Hawkins-Kennedy")
                if obrien: tests.append("O'Brien's")
                if apprehension: tests.append("Apprehension/Relocation")
                if scarf: tests.append("Scarf Test")

                special_tests = "Positive: " + ", ".join(tests) if tests else "All negative/normal"
                if other_shoulder.strip():
                    special_tests += f" | Other: {other_shoulder.strip()}"
                
            else:
                # Fallback for others
                rom_notes = st.text_area("Range of Motion", value=existing.get("rom_notes", "") if existing else "", height=80)
                special_tests = st.text_area("Special Tests", value=existing.get("special_tests", "") if existing else "", height=80)
                
            neuro_notes = st.text_area("Neurovascular Status", value=existing.get("neurovascular", "Intact distally") if existing else "Intact distally", height=80)
            
        with t_img:
            c_xr, c_mri = st.columns(2)
            xray = c_xr.text_area("🩻 X-Ray Findings", value=existing.get("xray", "") if existing else "", height=100)
            mri = c_mri.text_area("🧲 MRI Findings", value=existing.get("mri", "") if existing else "", height=100)
            c_ct, c_us = st.columns(2)
            ct = c_ct.text_area("🔬 CT Findings", value=existing.get("ct", "") if existing else "", height=100)
            us = c_us.text_area("🔊 Ultrasound", value=existing.get("us", "") if existing else "", height=100)
            imaging_other = st.text_area("📋 Other Imaging / Labs", value=existing.get("imaging_other", "") if existing else "", height=80)
            
        with t_plan:
            diagnosis = st.text_area("Primary Diagnosis *", value=existing.get("diagnosis", "") if existing else "", height=100)
            medications = st.text_area("Medications Prescribed", value=existing.get("medications", "") if existing else "", height=100)
            c_proc, c_fup = st.columns(2)
            
            with c_proc:
                st.markdown("**Procedures / Interventions**")
                
                db_procs = get_distinct_procedure_types()
                
                existing_proc_types = []
                existing_notes = ""
                if edit_vid:
                    linked_procs = get_visit_procedures(edit_vid)
                    existing_proc_types = [p['procedure_type'] for p in linked_procs]
                    if linked_procs and linked_procs[0]['notes']:
                        existing_notes = linked_procs[0]['notes']
                
                all_procs = list(set(PROCEDURE_TYPES + db_procs + existing_proc_types))
                all_procs = [p for p in all_procs if p and p != "Other"]
                all_procs.sort()
                
                legacy_text = existing.get("procedures", "") if existing else ""
                if legacy_text and not existing_proc_types and " | Notes: " not in legacy_text:
                    existing_notes = legacy_text

                default_sel = [p for p in existing_proc_types if p in all_procs]
                
                sel_procs = st.multiselect("Select Procedures", options=all_procs, default=default_sel, label_visibility="collapsed")
                custom_proc = st.text_input("Add Custom Procedure (not in list)", placeholder="Type new procedure here...")
                proc_notes = st.text_area("Procedure Notes / Details", value=existing_notes, height=68)
                
            followup = c_fup.text_area("Follow-up Plan", value=existing.get("followup", "") if existing else "", height=100)
            referrals = st.text_input("Referrals (Physio, etc.)", value=existing.get("referrals", "") if existing else "")

        with t_bill:
            st.markdown("**Quick Billing** — leave fee at 0 to skip invoice creation")
            bc1, bc2 = st.columns(2)
            bill_cat = bc1.selectbox("Service Category", BILLING_CATEGORIES, key="visit_bill_cat")
            bill_fee = bc2.number_input("Fee Amount", min_value=0.0, value=0.0, step=1.0, key="visit_bill_fee")
            bc3, bc4 = st.columns(2)
            bill_method = bc3.selectbox("Payment Method", PAYMENT_METHODS, key="visit_bill_method")
            bill_paid = bc4.checkbox("Mark as Paid immediately", value=True, key="visit_bill_paid")

        btn_label = "💾 Update Visit" if existing else "💾 Save Visit"
        if st.form_submit_button(btn_label, type="primary"):
            if not visit_date.strip() or not reason.strip() or not diagnosis.strip():
                st.error("Please fill required fields (*): Visit Date, Reason, and Diagnosis.")
            else:
                final_procs = list(sel_procs)
                if custom_proc.strip() and custom_proc.strip() not in final_procs:
                    final_procs.append(custom_proc.strip())
                
                proc_summary = " + ".join(final_procs)
                if proc_notes.strip():
                    proc_summary += f" | Notes: {proc_notes.strip()}"

                vid_saved = save_visit({
                    "patient_id": pid, "visit_date": visit_date.strip(), "reason": reason,
                    "history": history, "examination": examination,
                    "template_used": template, "rom_notes": rom_notes,
                    "special_tests": special_tests, "neurovascular": neuro_notes,
                    "injury_mechanism": injury_mech,
                    "xray": xray, "ct": ct, "mri": mri, "us": us, "imaging_other": imaging_other,
                    "diagnosis": diagnosis, "medications": medications,
                    "procedures": proc_summary, "followup": followup, "referrals": referrals
                }, vid=edit_vid)
                
                # Auto-sync procedures to procedures_log
                delete_visit_procedures(vid_saved)
                
                for p in final_procs:
                    add_procedure_log({
                        "patient_id": pid, "visit_id": vid_saved, "procedure_date": visit_date.strip(), 
                        "procedure_type": p, "body_part": template, "notes": proc_notes.strip()
                    })
                
                # Auto-create invoice if fee > 0 and this is a new visit (not edit)
                if bill_fee > 0 and not edit_vid:
                    pt_data = get_patient(pid)
                    ins_co = pt_data.get("insurance", "") if pt_data else ""
                    
                    inv_id = create_invoice({
                        "patient_id": pid, "visit_id": vid_saved, "invoice_date": visit_date.strip(), 
                        "total_amount": bill_fee, "discount": 0, "net_amount": bill_fee, 
                        "status": "Paid" if bill_paid else "Unpaid", "payment_method": bill_method, 
                        "insurance_company": ins_co
                    })
                    
                    create_billing_item({
                        "invoice_id": inv_id, "category": bill_cat, "description": f"Visit: {reason}", 
                        "quantity": 1, "unit_price": bill_fee, "total_price": bill_fee
                    })
                    
                    if bill_paid:
                        add_payment({
                            "invoice_id": inv_id, "payment_date": visit_date.strip(), 
                            "amount": bill_fee, "payment_method": bill_method
                        })
                
                st.session_state.pop("edit_visit_id", None)
                st.session_state.page = "patient_detail"
                st.rerun()

def render_print_visit():
    v = st.session_state.get("print_visit") or {}
    pt = st.session_state.get("print_patient") or {}

    cb, cp = st.columns([1, 1])
    with cb:
        if st.button("← Back to Patient"):
            st.session_state.page = "patient_detail"
            st.rerun()
    with cp:
        st.markdown("""
        <button onclick="window.print()" style="
            width:100%; padding:8px 0; background:#1a5fa8; color:#fff;
            border:none; border-radius:8px; font-size:14px;
            font-weight:600; cursor:pointer;">
            🖨 Print / Save as PDF
        </button>""", unsafe_allow_html=True)

    st.markdown("---")
    age = calc_age(pt.get("dob",""))

    st.markdown(f"""
    ## 🏥 Visit Record
    
    | | |
    |---|---|
    | **Patient** | {pt.get('name','')} |
    | **Age / DOB** | {age} / {pt.get('dob','')} |
    | **Phone** | {pt.get('phone','')} |
    | **Visit Date** | {v.get('visit_date','')} |
    | **Reason** | {v.get('reason','')} |
    | **Template** | {v.get('template_used','General')} |
    
    ---
    ### History
    **Mechanism of Injury:** {v.get('injury_mechanism','—')}
    
    {v.get('history','—')}
    
    ---
    ### Examination
    {v.get('examination','—')}
    
    **ROM:** {v.get('rom_notes','—')}
    
    **Special Tests:** {v.get('special_tests','—')}
    
    **Neurovascular:** {v.get('neurovascular','—')}
    
    ---
    ### Imaging
    **X-Ray:** {v.get('xray','—')}
    
    **MRI:** {v.get('mri','—')}
    
    ---
    ### Plan & Treatment
    **Diagnosis:** {v.get('diagnosis','—')}
    
    **Medications:** {v.get('medications','—')}
    
    **Procedures:** {v.get('procedures','—')}
    
    **Follow-up:** {v.get('followup','—')}
    
    **Referrals:** {v.get('referrals','—')}
    """)


if __name__ == '__main__':
    render()
