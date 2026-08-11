import streamlit as st
import pandas as pd
from core.clinic_db import get_all_users, add_user, delete_user, change_user_password
from core.utils import ROLES

def render():
    st.markdown("# ⚙️ Admin Settings")
    
    t_users, t_password, t_backup, t_clinic = st.tabs([
        "👥 User Management", "🔑 Change Password", "💾 Database Backup", "🏥 Clinic Settings"
    ])
    
    with t_users:
        render_users()
    
    with t_password:
        render_change_password()
        
    with t_backup:
        render_backup()
        
    with t_clinic:
        st.info("Clinic general settings (name, branding, currency) are currently set in utils.py.")

def render_users():
    st.markdown("### Manage Access")
    
    users = get_all_users()
    
    if users:
        df = pd.DataFrame(users)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("### Delete User")
        user_options = {u['id']: f"{u['username']}" for u in users if u['username'] != 'admin'}
        if user_options:
            with st.form("delete_user_form"):
                del_user_id = st.selectbox("Select user to delete", options=list(user_options.keys()), format_func=lambda x: user_options[x])
                if st.form_submit_button("🗑 Delete User"):
                    delete_user(del_user_id)
                    st.success("User deleted successfully!")
                    st.rerun()
        else:
            st.info("No other users to delete.")
        
    st.markdown("---")
    with st.form("new_user_form"):
        st.markdown("### Add New User")
        c1, c2 = st.columns(2)
        username = c1.text_input("Username")
        fullname = c2.text_input("Full Name")
        
        c3, c4 = st.columns(2)
        password = c3.text_input("Password", type="password")
        role = c4.selectbox("Role", ROLES)
        
        if st.form_submit_button("➕ Create User", type="primary"):
            if not username or not password or not fullname:
                st.error("All fields are required.")
            else:
                try:
                    add_user({
                        "username": username.lower().strip(),
                        "password": password,
                        "role": role,
                        "full_name": fullname.strip()
                    })
                    st.success(f"User {username} created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating user: {e}")

def render_change_password():
    st.markdown("### Change Your Password")
    st.markdown(f"Logged in as: **{st.session_state.user}**")
    
    with st.form("change_pw_form"):
        current_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("🔑 Change Password", type="primary"):
            if not current_pw or not new_pw:
                st.error("All fields are required.")
            elif new_pw != confirm_pw:
                st.error("New password and confirmation do not match.")
            elif len(new_pw) < 4:
                st.error("Password must be at least 4 characters.")
            else:
                # Verify current password before allowing change
                from core.database import verify_password, get_supabase
                supabase = get_supabase()
                user_resp = supabase.table('users').select('id, password_hash').eq('username', st.session_state.user).execute()
                if user_resp.data:
                    user = user_resp.data[0]
                    if verify_password(user['password_hash'], current_pw):
                        change_user_password(user['id'], new_pw)
                        st.success("Password changed successfully!")
                    else:
                        st.error("Current password is incorrect.")
                else:
                    st.error("User not found.")

def render_backup():
    st.markdown("### Database Backup")
    st.info("Database is hosted on Supabase cloud. Backups are managed automatically.")

if __name__ == '__main__':
    render()
