"""
styles.py — Centralized CSS for the Streamlit app
"""
import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
    /* Force light theme across all Streamlit containers */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main,
    section.main > div,
    .block-container {
        background-color: #f4f6f9 !important;
        color: #1a1a1a !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] > div:first-child {
        background-color: #ffffff !important;
        border-right: 1px solid #e0e3e8;
    }
    [data-testid="stSidebar"] * { color: #1a1a1a !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #1a1a1a !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        text-align: left;
        border-radius: 8px;
        font-size: 13px;
        width: 100%;
        padding: 8px 12px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #f0f2f5 !important;
        border-color: #e0e3e8 !important;
    }

    /* All text inputs / textareas */
    input, textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="base-input"] input {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border-color: #ced3da !important;
    }
    label,
    .stTextInput label,
    .stTextArea label,
    .stDateInput label,
    .stSelectbox label,
    .stRadio label {
        color: #333 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }

    /* Headings */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1a1a1a !important;
    }

    /* All buttons */
    .stButton > button {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #ced3da !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        background-color: #f0f2f5 !important;
    }
    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #1a5fa8 !important;
        color: #ffffff !important;
        border-color: #1a5fa8 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #154d8a !important;
    }
    /* Form submit buttons */
    [data-testid="stFormSubmitButton"] > button {
        background-color: #1a5fa8 !important;
        color: #ffffff !important;
        border-color: #1a5fa8 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #154d8a !important;
    }

    /* Tabs */
    [data-baseweb="tab-list"] {
        background-color: #eef0f4 !important;
        border-bottom: 1px solid #e0e3e8 !important;
        border-radius: 8px 8px 0 0;
    }
    [data-baseweb="tab"] {
        background: transparent !important;
        color: #555 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    [aria-selected="true"][data-baseweb="tab"] {
        color: #1a5fa8 !important;
        border-bottom: 2px solid #1a5fa8 !important;
        background: transparent !important;
    }
    [data-baseweb="tab-panel"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e3e8 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 18px !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #e0e3e8 !important;
        border-radius: 10px !important;
        margin-bottom: 10px !important;
    }
    [data-testid="stExpander"] details summary p,
    [data-testid="stExpander"] summary {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }
    [data-testid="stExpander"] > div > div {
        background: #ffffff !important;
    }

    /* Cards */
    .pt-card {
        background: #ffffff;
        border: 1px solid #e0e3e8;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .pt-card-name { font-size: 15px; font-weight: 700; color: #1a1a1a; }
    .pt-card-meta { font-size: 12px; color: #666; margin-top: 3px; }

    /* Badges */
    .badge {
        display: inline-block;
        background: #e8f0fb; color: #1a5fa8;
        font-size: 11px; padding: 2px 9px;
        border-radius: 20px; border: 1px solid #b8d0f0;
        margin-right: 4px; margin-top: 4px;
    }
    .badge-warn { background:#fff4e5; color:#8a4000; border-color:#ffd08a; }

    /* Section labels */
    .section-label {
        font-size: 11px; font-weight: 700; color: #888;
        letter-spacing: 0.06em; text-transform: uppercase;
        margin: 14px 0 8px; padding-bottom: 5px;
        border-bottom: 1px solid #e0e3e8;
    }

    /* Metric cards */
    .metric-card {
        background: #ffffff; border: 1px solid #e0e3e8;
        border-radius: 12px; padding: 20px; text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .metric-value { font-size: 36px; font-weight: 700; color: #1a5fa8; line-height: 1; }
    .metric-label { font-size: 12px; color: #888; margin-top: 6px; }

    /* Search result */
    .sr-divider { border: none; border-top: 1px solid #e8eaed; margin: 10px 0; }

    /* Hide Streamlit deploy button */
    .stDeployButton { display: none !important; }

    /* Print */
    @media print {
        [data-testid="stSidebar"],
        .stButton,
        [data-testid="stToolbar"],
        [data-testid="stFormSubmitButton"],
        .no-print { display: none !important; }
        .stApp, .block-container { background: white !important; }
    }
    </style>
    """, unsafe_allow_html=True)
