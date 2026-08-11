import streamlit as st
import pandas as pd
from datetime import date
from core.surgical_db import search_cases, get_hospitals, SPECIALTIES, get_case, update_case, delete_case, get_followups, add_followup

SIDES       = ["", "Right", "Left", "Bilateral", "N/A"]
GENDERS     = ["Unknown", "Male", "Female"]
ANAESTHESIA = ["", "GA", "Spinal", "Regional", "Local", "Sedation"]
ROLES       = ["", "Primary", "Assistant", "Observer"]
OUTCOMES    = ["", "Pending", "Excellent", "Good", "Fair", "Poor"]

def render_search():
    st.markdown('<div class="page-title">🔍 Search, Edit & Browse Cases</div>', unsafe_allow_html=True)
    HOSPITALS = get_hospitals()
    
    tab1, tab2, tab3 = st.tabs(["🔍 Search & Browse", "✏️ Edit Case", "📤 Export Data"])
    
    # ─── SEARCH & BROWSE ───────────────────────────────────────────────
    with tab1:
        with st.expander("🔎 Search Filters", expanded=True):
            s1, s2, s3 = st.columns(3)
            with s1:
                keywords = st.text_input("Keywords (space-separated)", placeholder="e.g. ACL knee semitendinosus")
            with s2:
                hosp_opts = ["All"] + list(HOSPITALS.keys())
                hosp_filter = st.selectbox("Hospital", hosp_opts, format_func=lambda x: "All Hospitals" if x == "All" else f"{x} — {HOSPITALS[x]}")
            with s3:
                spec_filter = st.selectbox("Specialty", ["All"] + SPECIALTIES, format_func=lambda x: "All Specialties" if x == "All" else x)

            d1, d2, d3, d4 = st.columns(4)
            with d1: date_from = st.date_input("From Date", value=None)
            with d2: date_to   = st.date_input("To Date",   value=None)
            with d3:
                fellowship_filter = st.selectbox("Case Type", ["All", "Fellowship Only", "Specialist Only"])
            with d4:
                compl_only = st.checkbox("Complications only")

        fu_int = -1
        if fellowship_filter == "Fellowship Only":   fu_int = 1
        elif fellowship_filter == "Specialist Only": fu_int = 0

        results = search_cases(
            keywords=keywords,
            hospital="" if hosp_filter == "All" else hosp_filter,
            specialty="" if spec_filter == "All" else spec_filter,
            date_from=str(date_from) if date_from else "",
            date_to=str(date_to) if date_to else "",
            is_fellowship=fu_int,
            complication_only=compl_only,
        )

        if results:
            st.markdown(f'<div class="search-result-count">Found <strong>{len(results)}</strong> case(s)</div>', unsafe_allow_html=True)
            df = pd.DataFrame(results)
            df["Hospital"] = df["hospital_code"].map(lambda x: HOSPITALS.get(x, x))
            df["Fellowship"] = df["is_fellowship"].map({1: "✅ Yes", 0: "No"})
            df["Date"] = pd.to_datetime(df["case_date"], errors="coerce").dt.strftime("%d %b %Y")
            
            def has_comp(x):
                return "⚠️" if x and str(x).strip() not in ("", "None", "nan") else ""
            
            df["⚠️"] = df["complications"].apply(has_comp)
            
            display_df = df[["id", "Date", "patient_name", "mrn", "specialty", "Hospital", "diagnosis", "procedure", "side", "role", "Fellowship", "⚠️"]].rename(columns={
                "id": "#", "patient_name": "Patient", "mrn": "MRN",
                "specialty": "Specialty", "diagnosis": "Diagnosis",
                "procedure": "Procedure", "side": "Side", "role": "Role"
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.info("To edit a case, go to the **✏️ Edit Case** tab.")
        else:
            st.info("No cases match your search.")
            
    # ─── EDIT CASE ──────────────────────────────────────────────────
    with tab2:
        st.markdown("#### Find a case to edit")
        lookup_id = st.number_input("Enter Case # directly", min_value=1, step=1, value=1)
        
        if lookup_id:
            case = get_case(int(lookup_id))
            if not case:
                st.error(f"Case #{lookup_id} not found.")
            else:
                st.markdown(f"---\n#### Editing Case #{case['id']} — {case.get('patient_name')}")
                
                if not HOSPITALS:
                    st.warning("No hospitals found. Please add a hospital first.")
                    return
                
                with st.expander("🗑️ Delete this case"):
                    st.error("This permanently deletes the case and all its follow-ups.")
                    if st.button("Confirm Delete", type="secondary"):
                        delete_case(case["id"])
                        st.success("Case deleted.")
                        st.rerun()
                
                def vi(field, default=""):
                    v = case.get(field, default)
                    return v if v is not None else default

                with st.form("edit_form"):
                    hosp_keys = list(HOSPITALS.keys())
                    hosp_names = list(HOSPITALS.values())
                    
                    e1, e2, e3 = st.columns(3)
                    with e1:
                        try:    dv = pd.to_datetime(vi("case_date")).date()
                        except: dv = date.today()
                        case_date = st.date_input("Date *", value=dv)
                    with e2:
                        cur_hosp = vi("hospital_code", hosp_keys[0])
                        hi = hosp_keys.index(cur_hosp) if cur_hosp in hosp_keys else 0
                        hosp_idx = st.selectbox("Hospital *", range(len(hosp_keys)),
                                                format_func=lambda i: f"{hosp_keys[i]} — {hosp_names[i]}", index=hi)
                        hospital_code = hosp_keys[hosp_idx]
                    with e3:
                        cur_spec = vi("specialty", SPECIALTIES[0])
                        si = SPECIALTIES.index(cur_spec) if cur_spec in SPECIALTIES else 0
                        specialty = st.selectbox("Specialty *", SPECIALTIES, index=si)
                        
                    p1, p2, p3, p4 = st.columns([3, 2, 1, 1])
                    with p1: patient_name = st.text_input("Patient Name *", value=vi("patient_name"))
                    with p2: mrn          = st.text_input("MRN / ID", value=vi("mrn"))
                    with p3: age          = st.number_input("Age", 0, 120, int(vi("age") or 0), step=1)
                    with p4:
                        gi = GENDERS.index(vi("gender", "Unknown")) if vi("gender") in GENDERS else 0
                        gender = st.selectbox("Gender", GENDERS, index=gi)
                        
                    diagnosis = st.text_area("Diagnosis", value=vi("diagnosis"))
                    findings  = st.text_area("Intraoperative Findings", value=vi("findings"))
                    procedure = st.text_area("Procedure Performed *", value=vi("procedure"))
                    
                    o1, o2, o3, o4 = st.columns(4)
                    with o1:
                        cur_side = vi("side", "")
                        si2 = SIDES.index(cur_side) if cur_side in SIDES else 0
                        side = st.selectbox("Side", SIDES, index=si2)
                    with o2:
                        cur_ana = vi("anaesthesia", "")
                        ai = ANAESTHESIA.index(cur_ana) if cur_ana in ANAESTHESIA else 0
                        anaesthesia = st.selectbox("Anaesthesia", ANAESTHESIA, index=ai)
                    with o3:
                        duration_min = st.number_input("Duration (min)", 0, 600, int(vi("duration_min") or 0), step=5)
                    with o4:
                        is_fellowship = st.checkbox("Fellowship Case", value=bool(vi("is_fellowship", 0)))
                        
                    cur_role = vi("role", "")
                    ri = ROLES.index(cur_role) if cur_role in ROLES else 0
                    role = st.selectbox("Surgical Role", ROLES, index=ri)
                    
                    graft_type = st.text_input("Graft Type", value=vi("graft_type"))
                    implant    = st.text_input("Implant / Fixation", value=vi("implant"))
                    complications = st.text_area("Complications", value=vi("complications"))
                    notes         = st.text_area("Notes", value=vi("notes"))
                    
                    saved = st.form_submit_button("💾 Save Changes", type="primary")
                    if saved:
                        update_case(case["id"], {
                            "case_date": str(case_date), "patient_name": patient_name.strip(),
                            "mrn": mrn.strip(), "age": age or None, "gender": gender,
                            "hospital_code": hospital_code, "specialty": specialty,
                            "diagnosis": diagnosis.strip(), "findings": findings.strip(),
                            "procedure": procedure.strip(), "side": side,
                            "graft_type": graft_type.strip(), "implant": implant.strip(),
                            "duration_min": duration_min or None, "anaesthesia": anaesthesia,
                            "complications": complications.strip(), "notes": notes.strip(),
                            "role": role, "is_fellowship": 1 if is_fellowship else 0,
                        })
                        st.success("Case updated!")
                        
                # Followups
                st.markdown("#### 📅 Follow-ups")
                followups = get_followups(case["id"])
                for fu in followups:
                    icon = {"Excellent": "🌟", "Good": "✅", "Fair": "🟡", "Poor": "🔴"}.get(fu.get("outcome", ""), "📋")
                    st.write(f"{icon} **{fu['fu_date']}** — {fu.get('outcome', '—')} | {fu.get('notes', '')}")
                    
                with st.form("fu_form"):
                    fu_date    = st.date_input("Date", value=date.today())
                    fu_outcome = st.selectbox("Outcome", OUTCOMES)
                    fu_notes = st.text_area("Notes")
                    if st.form_submit_button("➕ Save Follow-up"):
                        add_followup(case["id"], str(fu_date), fu_notes, fu_outcome)
                        st.success("Follow-up saved!")
                        st.rerun()
                        
    # ─── EXPORT ────────────────────────────────────────────────────────
    with tab3:
        st.info("Apply filters in the **Search & Browse** tab. The filtered results there will be exported here.")
        if results:
            df_export = pd.DataFrame(results)
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download CSV",
                data=csv,
                file_name=f"surgical_logbook_{date.today()}.csv",
                mime="text/csv",
                type="primary"
            )

render_search()
