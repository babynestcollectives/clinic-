import streamlit as st
import pandas as pd
from core.clinic_db import (get_all_patients, get_patient, save_patient, delete_patient,
                get_visits, get_visit, save_visit, delete_visit,
                delete_surgery, get_patient_invoices, get_procedures_log, get_surgeries, get_followups, add_followup)
from core.surgical_db import get_patient_surgical_cases
from core.utils import (calc_age, SPORTS_LEVELS, SMOKING_STATUS, LATERALITY_OPTIONS,
                    REHAB_PHASES, role_can, fmt_currency)

def render():
    if not role_can(st.session_state.role, "patients_view"):
        st.error("You do not have permission to view patients.")
        return

    # Routing within the patients module
    current_page = st.session_state.get("page", "patients")
    
    # If they arrived here from a non-patient state, reset to patients list
    if current_page not in ["patients", "new_patient", "patient_detail", "confirm_delete_patient"]:
        current_page = "patients"
        st.session_state.page = "patients"

    if current_page == "patients":
        render_patients_list()
    elif current_page == "new_patient":
        render_new_patient()
    elif current_page == "patient_detail":
        render_patient_detail()
    elif current_page == "confirm_delete_patient":
        render_confirm_delete()


def render_patients_list():
    st.markdown("# 👥 Patients")

    col_s, col_btn = st.columns([5, 1])
    with col_s:
        search = st.text_input("", placeholder="🔍  Search by name, phone or insurance...", label_visibility="collapsed")
    with col_btn:
        if role_can(st.session_state.role, "patients"):
            if st.button("➕ New Patient", type="primary", use_container_width=True):
                st.session_state.page = "new_patient"
                st.rerun()

    patients = get_all_patients(search)
    if not patients:
        st.info("No patients found. Click '+ New Patient' to create the first record.")
    else:
        for pt in patients:
            age = calc_age(pt["dob"])
            visits = get_visits(pt["id"])
            flags = []
            if pt.get("dm"): flags.append(("dm", f"DM: {pt['dm']}"))
            if pt.get("htn"): flags.append(("htn", f"HTN: {pt['htn']}"))
            if pt.get("allergies"): flags.append(("allergy", f"⚠ {pt['allergies']}"))
            
            badges_html = "".join(
                f'<span class="badge {"badge-warn" if t=="allergy" else ""}">{lbl}</span>'
                for t, lbl in flags
            )
            
            insurance_str = pt.get("insurance_policy_no") or pt.get("insurance") or ""
            meta_parts = [x for x in [age, pt.get("phone",""), insurance_str] if x]
            meta = " · ".join(meta_parts)

            col_info, col_open = st.columns([6, 1])
            with col_info:
                st.markdown(f"""
                <div class="pt-card">
                    <div class="pt-card-name">{pt['name']}</div>
                    <div class="pt-card-meta">{len(visits)} visit{'s' if len(visits)!=1 else ''}{'  ·  '+meta if meta else ''}</div>
                    {"<div style='margin-top:6px'>"+badges_html+"</div>" if badges_html else ""}
                </div>""", unsafe_allow_html=True)
            with col_open:
                st.write("")
                st.write("")
                if st.button("Open →", key=f"op_{pt['id']}", use_container_width=True):
                    st.session_state.selected_patient = pt["id"]
                    st.session_state.page = "patient_detail"
                    st.rerun()


def render_new_patient():
    st.markdown("# ➕ New Patient")
    if st.button("← Back to Patients"):
        st.session_state.page = "patients"
        st.rerun()
    st.write("")

    with st.form("new_patient_form"):
        st.markdown('<div class="section-label">Basic Information</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        name    = c1.text_input("Full Name *")
        dob_str = c2.text_input("Date of Birth", placeholder="YYYY-MM-DD  e.g. 1985-06-20")
        
        c3, c4 = st.columns(2)
        phone = c3.text_input("Phone Number")
        emergency = c4.text_input("Emergency Contact")
        
        st.markdown('<div class="section-label">Insurance & Billing</div>', unsafe_allow_html=True)
        c_ins1, c_ins2 = st.columns(2)
        is_insured = c_ins1.radio("Payment Type", ["Cash", "Insured"], index=0)
        insurance_co = ""
        policy_no = ""
        expiry = ""
        
        if is_insured == "Insured":
            insurance_co = c_ins2.text_input("Insurance Company")
            c_ins3, c_ins4 = st.columns(2)
            policy_no = c_ins3.text_input("Policy Number")
            expiry = c_ins4.text_input("Expiry Date (YYYY-MM-DD)")

        st.markdown('<div class="section-label">Orthopedic Profile</div>', unsafe_allow_html=True)
        co1, co2 = st.columns(2)
        occupation = co1.text_input("Occupation", placeholder="Desk job, manual labor, student...")
        sports = co2.selectbox("Sports Activity Level", SPORTS_LEVELS)
        
        co3, co4 = st.columns(2)
        smoking = co3.selectbox("Smoking Status", SMOKING_STATUS)
        laterality = co4.selectbox("Dominant Side", ["Right", "Left", "Ambidextrous", "Unknown"], index=0)

        st.markdown('<div class="section-label">Medical Background</div>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        dm = c5.text_input("DM (Diabetes)", placeholder="Type 1 / Type 2 / No")
        htn = c6.text_input("HTN (Hypertension)", placeholder="Yes / No / Controlled")
        
        c7, c8 = st.columns(2)
        asthma = c7.text_input("Asthma", placeholder="Yes / No / Mild / Severe")
        chronic = c8.text_input("Other Chronic Diseases", placeholder="Thyroid, Heart disease...")
        
        c9, c10 = st.columns(2)
        meds = c9.text_input("Chronic Medications", placeholder="Metformin, Amlodipine...")
        allergies = c10.text_input("Allergies", placeholder="Penicillin, NSAIDs...")
        
        surgeries = st.text_input("Previous Surgeries", placeholder="Appendectomy 2018, ACL 2015...")
        notes = st.text_area("Other Notes", height=80)

        if st.form_submit_button("💾 Save Patient"):
            if not name.strip():
                st.error("Patient name is required.")
            else:
                pid = save_patient({
                    "name": name.strip(), "dob": dob_str.strip(),
                    "phone": phone, "emergency_contact": emergency,
                    "is_insured": 1 if is_insured == "Insured" else 0,
                    "insurance": insurance_co, "insurance_policy_no": policy_no, "insurance_expiry": expiry,
                    "occupation": occupation, "sports_level": sports, "smoking": smoking, "laterality": laterality,
                    "dm": dm, "htn": htn, "asthma": asthma, "chronic_diseases": chronic,
                    "medications": meds, "allergies": allergies,
                    "surgeries": surgeries, "notes": notes
                })
                st.session_state.selected_patient = pid
                st.session_state.page = "patient_detail"
                st.rerun()


def render_patient_detail():
    pid = st.session_state.selected_patient
    pt = get_patient(pid)
    if not pt:
        st.error("Patient not found.")
        st.stop()

    age = calc_age(pt["dob"])
    info_parts = [x for x in [age, pt.get("dob",""), pt.get("phone","")] if x]
    
    if pt.get("is_insured"):
        info_parts.append(f"Insured: {pt.get('insurance','')}")
    else:
        info_parts.append("Cash")

    hc1, hc2, hc3 = st.columns([5, 1, 1])
    with hc1:
        st.markdown(f"# {pt['name']}")
        st.markdown(f"<span style='color:#666;font-size:13px'>{' · '.join(info_parts)}</span>", unsafe_allow_html=True)
    with hc2:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "patients"
            st.rerun()
    with hc3:
        if role_can(st.session_state.role, "patients") and st.button("🗑 Delete", use_container_width=True):
            st.session_state.page = "confirm_delete_patient"
            st.rerun()

    tab_file, tab_visits, tab_procs, tab_surgeries, tab_followups, tab_billing = st.tabs([
        "📋 Patient File", "🗓 Visits", "💉 Procedures", "🔪 Surgeries", "🔄 Follow-ups", "💰 Billing"
    ])

    # ── Patient File ──
    with tab_file:
        if not role_can(st.session_state.role, "patients"):
            st.info("You do not have permission to edit patient files.")
            # Read-only view
            st.json(pt)
        else:
            with st.form("edit_patient"):
                st.markdown('<div class="section-label">Basic Information</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                name    = c1.text_input("Full Name", value=pt["name"] or "")
                dob_str = c2.text_input("Date of Birth", value=pt["dob"] or "", placeholder="YYYY-MM-DD")
                
                c3, c4 = st.columns(2)
                phone     = c3.text_input("Phone Number", value=pt["phone"] or "")
                emergency = c4.text_input("Emergency Contact", value=pt.get("emergency_contact") or "")
                
                st.markdown('<div class="section-label">Insurance & Billing</div>', unsafe_allow_html=True)
                c_ins1, c_ins2 = st.columns(2)
                
                is_insured_idx = 1 if pt.get("is_insured") else 0
                is_insured = c_ins1.radio("Payment Type", ["Cash", "Insured"], index=is_insured_idx)
                
                insurance_co = c_ins2.text_input("Insurance Company", value=pt["insurance"] or "")
                c_ins3, c_ins4 = st.columns(2)
                policy_no = c_ins3.text_input("Policy Number", value=pt.get("insurance_policy_no") or "")
                expiry = c_ins4.text_input("Expiry Date (YYYY-MM-DD)", value=pt.get("insurance_expiry") or "")

                st.markdown('<div class="section-label">Orthopedic Profile</div>', unsafe_allow_html=True)
                co1, co2 = st.columns(2)
                occupation = co1.text_input("Occupation", value=pt.get("occupation") or "")
                
                try: sports_idx = SPORTS_LEVELS.index(pt.get("sports_level", SPORTS_LEVELS[0]))
                except: sports_idx = 0
                sports = co2.selectbox("Sports Activity Level", SPORTS_LEVELS, index=sports_idx)
                
                co3, co4 = st.columns(2)
                try: smoke_idx = SMOKING_STATUS.index(pt.get("smoking", SMOKING_STATUS[0]))
                except: smoke_idx = 0
                smoking = co3.selectbox("Smoking Status", SMOKING_STATUS, index=smoke_idx)
                
                try: lat_idx = LATERALITY_OPTIONS.index(pt.get("laterality", LATERALITY_OPTIONS[0]))
                except: lat_idx = 0
                laterality = co4.selectbox("Dominant Side", LATERALITY_OPTIONS, index=lat_idx)

                st.markdown('<div class="section-label">Medical Background</div>', unsafe_allow_html=True)
                c5, c6 = st.columns(2)
                dm     = c5.text_input("DM",     value=pt["dm"] or "",     placeholder="Type 1 / Type 2 / No")
                htn    = c6.text_input("HTN",    value=pt["htn"] or "",    placeholder="Yes / No / Controlled")
                c7, c8 = st.columns(2)
                asthma = c7.text_input("Asthma", value=pt["asthma"] or "", placeholder="Yes / No / Mild / Severe")
                chronic = c8.text_input("Other Chronic", value=pt.get("chronic_diseases") or "")
                
                c9, c10 = st.columns(2)
                meds   = c9.text_input("Chronic Medications", value=pt["medications"] or "")
                allergies = c10.text_input("Allergies",          value=pt["allergies"] or "")
                surgeries = st.text_input("Previous Surgeries",value=pt["surgeries"] or "")
                notes = st.text_area("Other Notes", value=pt["notes"] or "", height=80)

                if st.form_submit_button("💾 Save Changes"):
                    save_patient({
                        "name": name, "dob": dob_str.strip(),
                        "phone": phone, "emergency_contact": emergency,
                        "is_insured": 1 if is_insured == "Insured" else 0,
                        "insurance": insurance_co, "insurance_policy_no": policy_no, "insurance_expiry": expiry,
                        "occupation": occupation, "sports_level": sports, "smoking": smoking, "laterality": laterality,
                        "dm": dm, "htn": htn, "asthma": asthma, "chronic_diseases": chronic,
                        "medications": meds, "allergies": allergies,
                        "surgeries": surgeries, "notes": notes
                    }, pid=pid)
                    st.success("Saved ✓")
                    st.rerun()

    # ── Visits ──
    with tab_visits:
        vc1, vc2 = st.columns([5, 1])
        with vc2:
            if role_can(st.session_state.role, "visits"):
                if st.button("➕ New Visit", type="primary", use_container_width=True):
                    st.session_state.page = "new_visit"
                    st.switch_page("pages/clinic/3_visits.py")

        visits = get_visits(pid)
        if not visits:
            st.info("No visits recorded yet.")
        else:
            for v in visits:
                template = v.get("template_used", "General")
                label = f"📅 {v['visit_date']}   {'· ' + v['reason'] if v.get('reason') else ''}   [{template}]"
                with st.expander(label, expanded=False):
                    
                    t_hist, t_exam, t_img, t_plan = st.tabs(["📝 History","🩺 Exam","🔬 Imaging","💊 Plan"])
                    
                    with t_hist:
                        st.markdown("**Reason:** " + (v.get("reason") or "—"))
                        st.markdown("**History:**\n" + (v.get("history") or "—"))
                        if v.get("injury_mechanism"):
                            st.markdown("**Injury Mechanism:** " + v.get("injury_mechanism"))
                            
                    with t_exam:
                        st.markdown("**Examination:**\n" + (v.get("examination") or "—"))
                        if v.get("rom_notes"):
                            st.markdown("**ROM:**\n" + v.get("rom_notes"))
                        if v.get("special_tests"):
                            st.markdown("**Special Tests:**\n" + v.get("special_tests"))
                        if v.get("neurovascular"):
                            st.markdown("**Neurovascular:**\n" + v.get("neurovascular"))
                            
                    with t_img:
                        for k, l in [("xray","X-Ray"),("mri","MRI"),("ct","CT"),("us","Ultrasound"),("imaging_other","Other")]:
                            if v.get(k): st.markdown(f"**{l}:**\n" + v[k])
                            
                    with t_plan:
                        st.markdown("**Diagnosis:** " + (v.get("diagnosis") or "—"))
                        st.markdown("**Medications:** " + (v.get("medications") or "—"))
                        st.markdown("**Procedures:** " + (v.get("procedures") or "—"))
                        st.markdown("**Follow-up:** " + (v.get("followup") or "—"))
                        st.markdown("**Referrals:** " + (v.get("referrals") or "—"))

                    st.markdown("---")
                    col_p, col_e, col_d = st.columns([1, 1, 4])
                    with col_p:
                        if st.button("🖨 Print", key=f"pr_{v['id']}"):
                            st.session_state.print_visit = get_visit(v["id"])
                            st.session_state.print_patient = pt
                            st.session_state.page = "print_visit"
                            st.switch_page("pages/clinic/3_visits.py")
                    with col_e:
                        if role_can(st.session_state.role, "visits") and st.button("✏️ Edit", key=f"ev_{v['id']}"):
                            st.session_state.edit_visit_id = v["id"]
                            st.session_state.page = "new_visit"
                            st.switch_page("pages/clinic/3_visits.py")
                    with col_d:
                        if role_can(st.session_state.role, "visits"):
                            # Delete with confirmation
                            if st.session_state.get(f"confirm_del_v_{v['id']}"):
                                st.warning("Are you sure? This cannot be undone.")
                                cd1, cd2 = st.columns(2)
                                if cd1.button("Yes, Delete", key=f"yd_{v['id']}"):
                                    delete_visit(v["id"])
                                    st.session_state.pop(f"confirm_del_v_{v['id']}", None)
                                    st.rerun()
                                if cd2.button("Cancel", key=f"cd_{v['id']}"):
                                    st.session_state.pop(f"confirm_del_v_{v['id']}", None)
                                    st.rerun()
                            else:
                                if st.button("🗑 Delete visit", key=f"dv_{v['id']}"):
                                    st.session_state[f"confirm_del_v_{v['id']}"] = True
                                    st.rerun()

    # ── Procedures ──
    with tab_procs:
        procs = get_procedures_log(pid)
        if not procs:
            st.info("No procedures logged.")
        else:
            for p in procs:
                with st.expander(f"💉 {p['procedure_date']} - {p['procedure_type']}"):
                    st.write(f"**Body Part:** {p.get('body_part', '—')} ({p.get('laterality', '—')})")
                    st.write(f"**Medication:** {p.get('medication_used', '—')} (Lot: {p.get('lot_number', '—')})")
                    st.write(f"**Volume/Dose:** {p.get('volume_dose', '—')}")
                    st.write(f"**Notes:** {p.get('notes', '—')}")
        
    # ── Surgeries ──
    with tab_surgeries:
        surg_list = get_surgeries(pid)
        logbook_cases = get_patient_surgical_cases(pid)
        
        if not surg_list and not logbook_cases:
            st.info("No surgeries logged.")
            
        if surg_list:
            st.markdown("#### Clinic Scheduled Surgeries")
            for s in surg_list:
                with st.expander(f"🔪 {s['surgery_date']} - {s['surgery_type']} ({s['status']})"):
                    st.write(f"**Side:** {s['laterality']}")
                    st.write(f"**Assistant:** {s['assistant']}")
                    st.write(f"**Anesthesia:** {s['anesthesia_type']}")
                    st.write(f"**Pre-op:** {s['preop_diagnosis']}")
                    st.write(f"**Post-op:** {s['postop_diagnosis']}")
                    st.write(f"**Approach:** {s['approach']}")
                    st.write(f"**Findings:** {s['findings']}")
                    st.write(f"**Closure:** {s['closure']}")
                    # Delete with confirmation
                    if st.session_state.get(f"confirm_del_s_{s['id']}"):
                        st.warning("Are you sure? This cannot be undone.")
                        cs1, cs2 = st.columns(2)
                        if cs1.button("Yes, Delete", key=f"yds_{s['id']}"):
                            delete_surgery(s["id"])
                            st.session_state.pop(f"confirm_del_s_{s['id']}", None)
                            st.rerun()
                        if cs2.button("Cancel", key=f"cds_{s['id']}"):
                            st.session_state.pop(f"confirm_del_s_{s['id']}", None)
                            st.rerun()
                    else:
                        if st.button("🗑 Delete Surgery", key=f"ds_{s['id']}"):
                            st.session_state[f"confirm_del_s_{s['id']}"] = True
                            st.rerun()

        if logbook_cases:
            st.markdown("#### Surgical Logbook Cases")
            for c in logbook_cases:
                with st.expander(f"🏥 {c['case_date']} - {c['procedure']} @ {c.get('hospital_name', 'Unknown')}"):
                    st.write(f"**Diagnosis:** {c.get('diagnosis') or '—'}")
                    st.write(f"**Side:** {c.get('side') or '—'}")
                    st.write(f"**Specialty:** {c.get('specialty') or '—'}")
                    st.write(f"**Anaesthesia:** {c.get('anaesthesia') or '—'}  |  **Duration:** {c.get('duration_min') or '—'} mins")
                    st.write(f"**Graft / Implant:** {c.get('graft_type') or '—'} / {c.get('implant') or '—'}")
                    st.write(f"**Findings:** {c.get('findings') or '—'}")
                    st.write(f"**Complications:** {c.get('complications') or '—'}")
                    st.write(f"**Notes:** {c.get('notes') or '—'}")

    # ── Follow-ups ──
    with tab_followups:
        followups = get_followups(pid)
        
        st.markdown("### Add Follow-up")
        with st.form("new_followup"):
            c1, c2 = st.columns(2)
            f_date = c1.date_input("Due Date")
            f_phase = c2.selectbox("Rehab Phase", REHAB_PHASES)
            f_notes = st.text_input("Notes")
            if st.form_submit_button("Add Follow-up"):
                add_followup({
                    'patient_id': pid,
                    'due_date': str(f_date),
                    'rehab_phase': f_phase,
                    'notes': f_notes,
                    'status': 'Pending'
                })
                st.rerun()
                
        st.markdown("### Scheduled Follow-ups")
        if not followups:
            st.info("No follow-ups tracked.")
        else:
            df = pd.DataFrame(followups)
            st.dataframe(df[["due_date", "rehab_phase", "status", "notes"]], use_container_width=True, hide_index=True)
        
    # ── Billing ──
    with tab_billing:
        invoices = get_patient_invoices(pid)
        if not invoices:
            st.info("No invoices found for this patient.")
        else:
            df_inv = pd.DataFrame(invoices)
            df_inv["balance"] = df_inv["net_amount"] - df_inv["paid"]
            df_display = df_inv.copy()
            df_display["net_amount"] = df_display["net_amount"].apply(lambda x: fmt_currency(x))
            df_display["paid"] = df_display["paid"].apply(lambda x: fmt_currency(x))
            df_display["balance"] = df_display["balance"].apply(lambda x: fmt_currency(x))
            st.dataframe(df_display[["id", "invoice_date", "net_amount", "paid", "balance", "status", "payment_method"]],
                         use_container_width=True, hide_index=True)
            
            total_billed = sum(i["net_amount"] for i in invoices)
            total_paid = sum(i["paid"] for i in invoices)
            st.markdown(f"**Total Billed:** {fmt_currency(total_billed)}  ·  **Paid:** {fmt_currency(total_paid)}  ·  **Outstanding:** {fmt_currency(total_billed - total_paid)}")


def render_confirm_delete():
    pid = st.session_state.selected_patient
    pt = get_patient(pid)
    st.markdown("# 🗑 Delete Patient")
    st.warning(f"Are you sure you want to delete **{pt['name']}** and ALL their visit records, surgeries, and billing? This cannot be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Yes, Delete", type="primary"):
        delete_patient(pid)
        st.session_state.selected_patient = None
        st.session_state.page = "patients"
        st.rerun()
    if c2.button("Cancel"):
        st.session_state.page = "patient_detail"
        st.rerun()


if __name__ == '__main__':
    render()
