import streamlit as st
import pandas as pd
from core.clinic_db import master_search
from core.utils import calc_age

def render():
    st.markdown("# 🔍 Master Search")
    st.markdown("Search across **all visit records** — diagnoses, medications, procedures, history, labs, imaging, and more.")

    query = st.text_input("", placeholder="e.g.  ACL repair,  metformin,  pneumonia ...", label_visibility="collapsed")

    if query.strip():
        results = master_search(query.strip())
        st.markdown(f"**{len(results)}** result{'s' if len(results)!=1 else ''} for *{query}*")

        if not results:
            st.info("No records found matching your search.")
        else:
            df_export = pd.DataFrame(results)
            st.download_button("⬇ Export results to CSV",
                               df_export.to_csv(index=False).encode(),
                               file_name=f"search_{query}.csv",
                               mime="text/csv")
            st.markdown("---")

            q_lower = query.lower()
            field_map_keys = [
                ("Diagnosis",    "diagnosis"),
                ("Medications",  "treatment_meds"),
                ("Procedures",   "procedures"),
                ("History",      "history"),
                ("Examination",  "examination"),
                ("Labs",         "labs"),
                ("X-Ray",        "xray"),
                ("CT",           "ct"),
                ("MRI",          "mri"),
                ("US",           "us"),
                ("Other Imaging","imaging_other"),
                ("Reason",       "reason"),
                ("Follow-up",    "followup"),
                ("Referrals",    "referrals"),
            ]

            for r in results:
                age = calc_age(r.get("dob",""))

                matched = [fname for fname, fkey in field_map_keys
                           if r.get(fkey) and q_lower in r[fkey].lower()]

                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    header = f"**{r['patient_name']}**"
                    if age: header += f"  ·  {age}"
                    header += f"  ·  📅 {r['visit_date']}"
                    if r.get("reason"): header += f"  ·  *{r['reason']}*"
                    st.markdown(header)

                    if r.get("diagnosis"):      st.markdown(f"- **Diagnosis:** {r['diagnosis']}")
                    if r.get("treatment_meds"): st.markdown(f"- **Medications:** {r['treatment_meds']}")
                    if r.get("procedures"):     st.markdown(f"- **Procedures:** {r['procedures']}")
                    
                    if matched:
                        st.caption(f"Matched in: {', '.join(matched)}")

                with col_btn:
                    if st.button("Open →", key=f"sr_{r['patient_id']}_{r['visit_id']}"):
                        st.session_state.selected_patient = r["patient_id"]
                        st.session_state.page = "patient_detail"
                        st.switch_page("pages/clinic/2_patients.py")

                st.markdown("---")
    else:
        st.markdown("<div style='color:#999;font-size:14px;margin-top:24px;text-align:center'>Type a clinical term to search across all records</div>", unsafe_allow_html=True)


if __name__ == '__main__':
    render()
