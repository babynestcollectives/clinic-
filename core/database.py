import streamlit as st
from supabase import create_client, Client
import hashlib
import binascii

# --- Supabase Initialization ---
@st.cache_resource
def get_supabase() -> Client:
    """Initialize and return the Supabase client using Streamlit secrets."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        st.info("Have you added your Supabase URL and Key to `.streamlit/secrets.toml`?")
        st.stop()

# --- Auth Helpers ---
def hash_password(password: str) -> str:
    """Hash a password for storing."""
    import os
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    try:
        salt = stored_password[:64]
        stored_pwdhash = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        return pwdhash == stored_pwdhash
    except:
        return False
