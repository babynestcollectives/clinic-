import streamlit as st
from datetime import date
from core.surgical_db import get_hospitals, SPECIALTIES, add_case

SIDES       = ["", "Right", "Left", "Bilateral", "N/A"]
GENDERS     = ["Unknown", "Male", "Female"]
ANAESTHESIA = ["", "GA", "Spinal", "Regional", "Local", "Sedation"]
ROLES       = ["", "Primary", "Assistant", "Observer"]

def render_new_case():
    st.markdown('<div class="page-title">➕ Add New Case</div>', unsafe_allow_html=True)
    HOSPITALS = get_hospitals()
    if not HOSPITALS:
        st.warning("No hospitals found in the database. Please add one first.")
        return
        
    hosp_keys  = list(HOSPITALS.keys())
    hosp_names = list(HOSPITALS.values())

    with st.form("new_case_form", clear_on_submit=True):
        st.markdown("#### 🏥 Case Information")
        c1, c2, c3 = st.columns(3)
        with c1:
            case_date = st.date_input("Date *", value=date.today())
        with c2:
            hosp_idx = st.selectbox("Hospital *", range(len(hosp_keys)),
                                    format_func=lambda i: f"{hosp_keys[i]} — {hosp_names[i]}")
            hospital_code = hosp_keys[hosp_idx]
        with c3:
            specialty = st.selectbox("Specialty *", SPECIALTIES)

        st.markdown("#### 👤 Patient")
        p1, p2, p3, p4 = st.columns([3, 2, 1, 1])
        with p1: patient_name = st.text_input("Patient Name *")
        with p2: mrn          = st.text_input("MRN / ID")
        with p3: age          = st.number_input("Age", 0, 120, 0, step=1)
        with p4: gender       = st.selectbox("Gender", GENDERS)

        st.markdown("#### 🔬 Clinical Details")
        diagnosis = st.text_area("Diagnosis", height=70)
        findings  = st.text_area("Intraoperative Findings", height=70)
        procedure = st.text_area("Procedure Performed *", height=80)

        st.markdown("#### ⚙️ Operative Details")
        o1, o2, o3, o4 = st.columns(4)
        with o1: side          = st.selectbox("Side", SIDES)
        with o2: anaesthesia   = st.selectbox("Anaesthesia", ANAESTHESIA)
        with o3: duration_min  = st.number_input("Duration (min)", 0, 600, 0, step=5)
        with o4: is_fellowship = st.checkbox("Fellowship Case")

        r1, r2 = st.columns([1, 3])
        with r1:
            role = st.selectbox(
                "Surgical Role",
                ROLES,
                help="Your role in this operation. Especially relevant for fellowship cases."
            )
        if role and is_fellowship:
            st.info(f"\U0001f3ab Fellowship case — Role: **{role}**")

        g1, g2 = st.columns(2)
        with g1: graft_type = st.text_input("Graft Type", placeholder="e.g. Semitendinosus autograft")
        with g2: implant    = st.text_input("Implant / Fixation", placeholder="e.g. PHILOS plate, PF Nail")

        st.markdown("#### 📝 Additional")
        complications = st.text_area("Complications", height=60, placeholder="Leave blank if none")
        notes         = st.text_area("Notes / Follow-up Plan", height=60)

        submitted = st.form_submit_button("💾 Save Case", type="primary")
        if submitted:
            if not patient_name.strip():
                st.error("Patient name is required.")
            elif not procedure.strip():
                st.error("Procedure is required.")
            else:
                save_role = role.strip() if role else ""
                if not save_role:
                    save_role = "Assistant" if is_fellowship else "Primary"

                new_id = add_case({
                    "case_date": str(case_date), "patient_name": patient_name.strip(),
                    "mrn": mrn.strip(), "age": age or None, "gender": gender,
                    "hospital_code": hospital_code, "specialty": specialty,
                    "diagnosis": diagnosis.strip(), "findings": findings.strip(),
                    "procedure": procedure.strip(), "side": side,
                    "graft_type": graft_type.strip(), "implant": implant.strip(),
                    "duration_min": duration_min or None, "anaesthesia": anaesthesia,
                    "complications": complications.strip(), "notes": notes.strip(),
                    "role": save_role,
                    "is_fellowship": 1 if is_fellowship else 0,
                })
                
                if new_id:
                    st.success(f"✅ Case #{new_id} — {patient_name.strip()} saved successfully!")
                else:
                    st.error("Error saving case.")

render_new_case()
