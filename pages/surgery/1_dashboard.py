import streamlit as st
import pandas as pd
import plotly.express as px
from core.surgical_db import stats_summary

def render_dashboard():
    st.markdown('<div class="page-title">📊 Dashboard</div>', unsafe_allow_html=True)
    stats = stats_summary()
    
    if stats["total"] == 0:
        st.info("No cases yet. Use **➕ New Case** to add your first operation.")
        return
        
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Cases",       stats["total"])
    c2.metric("Fellowship",        stats["fellowship"])
    c3.metric("Specialist",        stats["specialist"])
    c4.metric("Complications",     stats["complications"])
    c5.metric("Complication Rate", f"{stats['complication_rate']}%")
    if stats.get("avg_duration"):
        st.caption(f"Average operative duration: **{stats['avg_duration']} min**")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card-title">Cases by Hospital</div>', unsafe_allow_html=True)
        hosp_df = pd.DataFrame(stats["by_hospital"])
        if not hosp_df.empty:
            fig = px.bar(hosp_df, x="hospital_name", y="n", text="n",
                         color="hospital_name",
                         labels={"n": "Cases", "hospital_name": ""})
            fig.update_traces(textposition="outside")
            fig.update_layout(showlegend=False, plot_bgcolor="white",
                              margin=dict(t=20, b=20, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="card-title">Cases by Specialty</div>', unsafe_allow_html=True)
        spec_df = pd.DataFrame(stats["by_specialty"])
        if not spec_df.empty:
            fig2 = px.pie(spec_df, names="specialty", values="n", hole=0.45,
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(showlegend=True, margin=dict(t=20, b=20, l=10, r=10),
                               legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig2, use_container_width=True)

    if stats.get("by_month"):
        st.markdown('<div class="card-title">Cases Over Time</div>', unsafe_allow_html=True)
        time_df = pd.DataFrame(stats["by_month"])
        fig3 = px.area(time_df, x="mo", y="n", labels={"mo": "Month", "n": "Cases"},
                       color_discrete_sequence=["#0E7C86"])
        fig3.update_layout(plot_bgcolor="white", margin=dict(t=20, b=20, l=10, r=10))
        fig3.update_traces(fill="tozeroy", fillcolor="rgba(14,124,134,0.12)")
        st.plotly_chart(fig3, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="card-title">Top 15 Procedures</div>', unsafe_allow_html=True)
        proc_df = pd.DataFrame(stats["by_procedure"]).head(15)
        if not proc_df.empty:
            if "procedure" in proc_df.columns:
                proc_df["procedure"] = proc_df["procedure"].str[:55]
                fig4 = px.bar(proc_df.sort_values("n"), x="n", y="procedure",
                              orientation="h", text="n",
                              color_discrete_sequence=["#1B3A6B"],
                              labels={"n": "Cases", "procedure": ""})
                fig4.update_traces(textposition="outside")
                fig4.update_layout(plot_bgcolor="white", margin=dict(t=10, b=10, l=10, r=40))
                st.plotly_chart(fig4, use_container_width=True)

    with col4:
        st.markdown('<div class="card-title">Top 15 Diagnoses</div>', unsafe_allow_html=True)
        diag_df = pd.DataFrame(stats["by_diagnosis"]).head(15)
        if not diag_df.empty:
            if "diagnosis" in diag_df.columns:
                diag_df["diagnosis"] = diag_df["diagnosis"].str[:55]
                fig5 = px.bar(diag_df.sort_values("n"), x="n", y="diagnosis",
                              orientation="h", text="n",
                              color_discrete_sequence=["#0E7C86"],
                              labels={"n": "Cases", "diagnosis": ""})
                fig5.update_traces(textposition="outside")
                fig5.update_layout(plot_bgcolor="white", margin=dict(t=10, b=10, l=10, r=40))
                st.plotly_chart(fig5, use_container_width=True)

render_dashboard()
