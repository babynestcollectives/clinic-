import streamlit as st
from core.database import get_supabase, verify_password

# ─── Page Config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Unified Medical Platform",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase
supabase = get_supabase()

# ─── Session State ────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.full_name = None

# ─── Auth ─────────────────────────────────────────────────────────
def login():
    st.markdown("<h1 style='text-align: center;'>⚕️ Unified Medical Platform</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #666;'>Dr. Yazan</h3>", unsafe_allow_html=True)
    st.write("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### 🔐 Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submitted:
                # Fetch user from Supabase
                res = supabase.table('users').select('*').eq('username', username).execute()
                
                if res.data and len(res.data) > 0:
                    user = res.data[0]
                    if verify_password(user['password_hash'], password):
                        st.session_state.logged_in = True
                        st.session_state.user = user['username']
                        st.session_state.role = user['role']
                        st.session_state.full_name = user['full_name']
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Invalid username or password")

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.full_name = None
    st.rerun()

if not st.session_state.logged_in:
    login()
    st.stop()

# ─── Main App Layout & Navigation ─────────────────────────────────

# We use Streamlit 1.36+ native navigation
pages = {
    "🏥 Clinic Management": [
        st.Page("pages/clinic/8_analytics.py", title="Dashboard", icon="📊", url_path="clinic_dashboard"),
        st.Page("pages/clinic/2_patients.py", title="Patients", icon="👥"),
        st.Page("pages/clinic/3_visits.py", title="Visits", icon="🩺"),
        st.Page("pages/clinic/10_procedures.py", title="Procedures", icon="💉"),
        st.Page("pages/clinic/4_appointments.py", title="Appointments", icon="📅"),
        st.Page("pages/clinic/5_search.py", title="Search", icon="🔍", url_path="clinic_search"),
        st.Page("pages/clinic/6_accounting.py", title="Accounting", icon="💰"),
        st.Page("pages/clinic/7_inventory.py", title="Inventory", icon="📦"),
        st.Page("pages/clinic/9_admin.py", title="Admin", icon="🛡️"),
    ],
    "🔪 Surgical Logbook": [
        st.Page("pages/surgery/1_dashboard.py", title="Surgical Dashboard", icon="📊", url_path="surgery_dashboard"),
        st.Page("pages/surgery/2_new_case.py", title="New Case", icon="➕"),
        st.Page("pages/surgery/3_search.py", title="Search & Browse", icon="🔍", url_path="surgery_search"),
    ]
}

pg = st.navigation(pages)

# Custom Sidebar content
with st.sidebar:
    st.markdown(f"**Welcome, {st.session_state.full_name}**")
    st.markdown(f"<small>Role: {st.session_state.role}</small>", unsafe_allow_html=True)
    if st.button("Logout", use_container_width=True):
        logout()
    st.markdown("---")

pg.run()
