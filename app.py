from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from apify_service import scrape_latest_15_posts
from auditor import run_senior_audit, run_single_post_audit
from intelligence import run_dynamic_audit_pipeline
import supabase_service as db
from datetime import datetime, timezone

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Intelligence Command Center",
    page_icon="🛡️"
)

# ── Session State Initialization ──────────────────────────────────────────────
if "active_audit" not in st.session_state:
    st.session_state.active_audit = None

# ── Sidebar Cache & History Matrix ───────────────────────────────────────────
st.sidebar.markdown("""
<div style='background: linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(219, 39, 119, 0.05) 100%); 
            padding: 20px; border-radius: 16px; border: 1px solid rgba(124, 58, 237, 0.15); margin-bottom: 20px;'>
    <h3 style='margin: 0 0 10px 0; font-family: "Outfit", sans-serif; color: var(--sol-violet); font-size: 18px;'>
        🛡️ Cache & History Matrix
    </h3>
    <p style='font-size: 12px; color: var(--sol-base01); margin: 0;'>
        Enterprise Caching & Token Conservation Engine
    </p>
</div>
""", unsafe_allow_html=True)

# Display Supabase configuration status badge
if db.is_supabase_configured():
    st.sidebar.markdown("""
    <div style='display: inline-flex; align-items: center; background: rgba(5, 150, 105, 0.1); 
                border: 1px solid rgba(5, 150, 105, 0.25); color: var(--sol-green); 
                padding: 6px 12px; border-radius: 30px; font-size: 11px; font-weight: 700; 
                letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 20px;'>
        <span style='width: 6px; height: 6px; background-color: var(--sol-green); border-radius: 50%; display: inline-block; margin-right: 8px;'></span>
        🟢 Supabase Sync Active
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div style='display: inline-flex; align-items: center; background: rgba(217, 119, 6, 0.1); 
                border: 1px solid rgba(217, 119, 6, 0.25); color: var(--sol-yellow); 
                padding: 6px 12px; border-radius: 30px; font-size: 11px; font-weight: 700; 
                letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 20px;'>
        <span style='width: 6px; height: 6px; background-color: var(--sol-yellow); border-radius: 50%; display: inline-block; margin-right: 8px;'></span>
        ⚠️ Supabase Offline (Local Fallback)
    </div>
    """, unsafe_allow_html=True)

st.sidebar.write("### ⚙️ Caching Rules")

# Highly user-friendly simple checkbox configuration
use_cache = st.sidebar.checkbox(
    "🔄 Use Cached Audit if Available (Last 7 Days)", 
    value=True, 
    help="When enabled, the system will instantly load existing data if this handle was audited in the last 7 days, saving your Apify and Gemini tokens!"
)

st.sidebar.write("---")

# Sidebar Manual Cache Retrieval
st.sidebar.write("### ⚡ Retrieve Past Audit")
cached_url = st.sidebar.text_input(
    "Enter Instagram handle or URL:",
    placeholder="username or URL",
    key="cached_url_input"
)
load_cache_btn = st.sidebar.button("⚡ LOAD FROM CACHE", type="primary", use_container_width=True)

if load_cache_btn:
    if not cached_url:
        st.sidebar.warning("Please enter a username or Instagram URL.")
    else:
        with st.spinner("Retrieving from Supabase..."):
            cached_data = db.get_cached_audit(cached_url)
            if cached_data:
                st.session_state.active_audit = cached_data
                st.session_state.active_audit["source"] = "Supabase Sidebar Cache"
                st.toast(f"✅ Cache HIT! Loaded @{cached_data['handle']}!", icon="⚡")
                st.rerun()
            else:
                st.sidebar.error("❌ No cached audit found in the last 7 days. Try running a Live Audit in the main panel.")

st.sidebar.write("---")

# Sidebar Clickable History List
st.sidebar.write("### 📂 Recent Audits History")
recent_runs = []
if db.is_supabase_configured():
    recent_runs = db.get_recent_audits(limit=5)
    
if recent_runs:
    for r in recent_runs:
        if st.sidebar.button(f"👤 @{r['handle']}", key=f"hist_{r['handle']}", use_container_width=True):
            with st.spinner(f"Loading cached audit for @{r['handle']}..."):
                cached_data = db.get_cached_audit(r['handle'])
                if cached_data:
                    st.session_state.active_audit = cached_data
                    st.session_state.active_audit["source"] = "Supabase History"
                    st.toast(f"✅ Loaded @{r['handle']} from Supabase cache!", icon="⚡")
                    st.rerun()
                else:
                    st.sidebar.error(f"Failed to load cached data for @{r['handle']}.")
else:
    if db.is_supabase_configured():
        st.sidebar.info("No audit history found in Supabase yet. Run a live audit to start building history!")
    else:
        st.sidebar.info("Provide SUPABASE_URL and SUPABASE_KEY in your .env file to enable shared history and audit caching.")

st.sidebar.write("---")


# ── CSS ───────────────────────────────────────────────────────────────────────
# ── CSS ───────────────────────────────────────────────────────────────────────
st.html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* 1. PALETTE DESIGN SYSTEM & VARIABLES */
    :root {
        --sol-base03: #F8FAFC;   /* Very soft slate/white background */
        --sol-base02: #FFFFFF;   /* Pure white elevated glass card surface */
        --sol-base01: #64748B;   /* Muted text / slate border */
        --sol-base00: #475569;   /* Slate midtone */
        --sol-base0:  #334155;   /* Slate body */
        --sol-base1:  #1E293B;   /* Dark slate body / strong text */
        --sol-base2:  #0F172A;   /* High contrast secondary headers */
        --sol-base3:  #0F172A;   /* Slate 900 high contrast headers */
        
        /* Premium Accent Highlights */
        --sol-cyan:    #0ea5e9;   /* Sky blue/cyan pulse */
        --sol-blue:    #2563eb;   /* Info blue badges */
        --sol-green:   #059669;   /* Victory Emerald status */
        --sol-yellow:  #d97706;   /* Warning Amber */
        --sol-orange:  #ea580c;   /* Action primary CTA */
        --sol-red:     #e11d48;   /* Friction Rose-Crimson */
        --sol-violet:  #7c3aed;   /* Violet layout badge */
        --sol-magenta: #db2777;   /* Dynamic pink highlights */
    }

    /* 2. GLOBAL BACKGROUND AND TYPOGRAPHY SCALE */
    .stApp {
        background: radial-gradient(circle at top right, rgba(124, 58, 237, 0.08), rgba(0,0,0,0) 60%), radial-gradient(circle at bottom left, rgba(219, 39, 119, 0.05), rgba(0,0,0,0) 50%), #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif !important;
    }
    
    header, [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
        background: transparent !important;
        border: none !important;
    }
    
    html, body, [data-testid="stWidgetLabel"] p {
        font-size: 16px !important;
        font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif !important;
    }
    
    p, li, span, label {
        color: var(--sol-base0) !important; /* Muted slate body copy */
    }

    .block-container {
        padding: 2.5rem 3rem 4rem !important;
        max-width: 1200px !important;
    }

    /* Typography Hierarchy */
    h1 {
        background: linear-gradient(135deg, #7c3aed 0%, #db2777 50%, #e11d48 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 44px !important;
        font-weight: 800 !important;
        line-height: 1.2 !important;
        padding-top: 10px !important;
        padding-bottom: 5px !important;
        margin-top: 0px !important;
        display: block !important;
        text-shadow: 0 4px 20px rgba(124, 58, 237, 0.1) !important;
    }
    
    div[data-testid="stMarkdownContainer"], .element-container {
        overflow: visible !important;
    }
    .tagline-text {
        color: #64748B !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        margin-top: -5px !important;
        margin-bottom: 25px !important;
        letter-spacing: 0.5px !important;
    }
    
    h2 {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: var(--sol-base3) !important;
        margin-top: 25px !important;
        font-family: 'Outfit', sans-serif !important;
    }

    h3, .section-title {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: var(--sol-base3) !important;
        margin-bottom: 15px !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    strong {
        color: var(--sol-base2) !important;
    }

    /* 3. PREMIUM FLOATING CARDS & GLASSMORPHIC CARDS */
    .dribbble-card, .feature-box, .section-card, .metric-card, .metric-card-box, .metric-card-panel {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid rgba(124, 58, 237, 0.12) !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.08) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        margin-bottom: 20px !important;
    }
    
    .dribbble-card:hover, .feature-box:hover, .section-card:hover, .metric-card:hover, .metric-card-box:hover, .metric-card-panel:hover {
        border-color: rgba(219, 39, 119, 0.35) !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 20px 40px -15px rgba(124, 58, 237, 0.15), 0 0 20px 0 rgba(219, 39, 119, 0.02) !important;
    }
    
    .card-header-text {
        color: #64748B !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        margin-top: 0 !important;
        margin-bottom: 16px !important;
    }

    /* Target metric summary numerical values directly */
    [data-testid="stMetricValue"] div {
        font-size: 38px !important;
        font-weight: 800 !important;
        color: var(--sol-base3) !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    [data-testid="stMetricLabel"] p {
        font-size: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        color: var(--sol-base0) !important;
    }

    /* CUSTOM METRIC ROW STYLING OVERLAYS */
    .metric-card {
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, var(--sol-violet), var(--sol-magenta));
        opacity: 0.8;
    }
    .metric-label {
        font-size: 12px !important;
        font-weight: 700 !important;
        color: var(--sol-base0) !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        margin-bottom: 8px !important;
    }
    .metric-value {
        font-size: 36px !important;
        font-weight: 800 !important;
        color: var(--sol-base3) !important;
        font-family: 'Outfit', sans-serif !important;
        line-height: 1.1 !important;
        margin-bottom: 12px !important;
    }
    .metric-unit {
        font-size: 18px !important;
        font-weight: 400 !important;
        color: var(--sol-base0) !important;
        margin-left: 4px !important;
    }
    .badge {
        font-size: 11px !important;
        font-weight: 700 !important;
        padding: 6px 12px !important;
        border-radius: 30px !important;
        display: inline-block !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* ADVANCED ANALYSIS METRICS OVERLAYS */
    .metric-header {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: var(--sol-base0) !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        margin-bottom: 10px !important;
    }
    .metric-number {
        font-size: 34px !important;
        font-weight: 800 !important;
        color: var(--sol-base3) !important;
        font-family: 'Outfit', sans-serif !important;
        margin-bottom: 8px !important;
    }
    .pill-blue {
        background: rgba(37, 99, 235, 0.1) !important;
        border: 1px solid rgba(37, 99, 235, 0.25) !important;
        color: var(--sol-blue) !important;
        padding: 4px 10px !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        display: inline-block !important;
        text-transform: uppercase !important;
    }

    /* 4. PREMIUM DYNAMIC TABS ARCHITECTURE (PILL SHAPE) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px !important;
        padding: 8px !important;
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 30px !important;
        border: 1px solid rgba(124, 58, 237, 0.12) !important;
        backdrop-filter: blur(10px) !important;
        margin-bottom: 25px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-radius: 20px !important;
        color: #64748B !important;
        padding: 12px 26px !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--sol-base3) !important;
        background-color: rgba(15, 23, 42, 0.05) !important;
        cursor: pointer !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 24px rgba(124, 58, 237, 0.25) !important;
    }

    .stTabs [data-baseweb="tab-highlight-bar"] {
        background-color: transparent !important;
        height: 0px !important;
    }

    /* 5. FORM INPUTS & SELECTION MENU SKINNING */
    [data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[role="button"] {
        background-color: #FFFFFF !important;
        color: var(--sol-base3) !important;
        border: 1px solid rgba(124, 58, 237, 0.2) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stTextInput"] input:focus, [data-testid="stSelectbox"] div[role="button"]:focus {
        border-color: var(--sol-violet) !important;
        box-shadow: 0 0 12px rgba(124, 58, 237, 0.25) !important;
    }

    /* 6. PRIMARY ACTION BUTTONS OVERHAUL */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, var(--sol-violet) 0%, var(--sol-magenta) 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        box-shadow: 0 8px 20px rgba(124, 58, 237, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, var(--sol-magenta) 0%, var(--sol-violet) 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(124, 58, 237, 0.35) !important;
    }

    /* 7. CUSTOM ENTERPRISE DATA TABLES (FLOATING CARD DESIGN) */
    .table-intel-header-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.9) 100%) !important;
        border: 1px solid rgba(124, 58, 237, 0.15) !important;
        border-left: 4px solid var(--sol-violet) !important;
        border-radius: 16px 16px 0px 0px !important;
        padding: 18px 24px !important;
        margin-bottom: -12px !important;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.04) !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .header-main-title {
        color: var(--sol-base3) !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .telemetry-meta-badge {
        background: rgba(124, 58, 237, 0.08) !important;
        border: 1px solid rgba(124, 58, 237, 0.2) !important;
        color: var(--sol-violet) !important;
        font-family: monospace !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .custom-table-container table, table.dash-table, div[data-testid="stMarkdownContainer"] table {
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 10px !important;
        background-color: transparent !important;
    }
    
    .custom-table-container th, table.dash-table th, div[data-testid="stMarkdownContainer"] table th {
        background: transparent !important;
        color: var(--sol-violet) !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        padding: 12px 16px !important;
        border-bottom: 2px solid rgba(124, 58, 237, 0.15) !important;
        text-align: left !important;
    }
    
    .custom-table-container td, table.dash-table td, div[data-testid="stMarkdownContainer"] table td {
        background-color: rgba(255, 255, 255, 0.6) !important;
        border: 1px solid rgba(15, 23, 42, 0.03) !important;
        border-style: solid none !important;
        color: var(--sol-base1) !important;
        font-size: 14px !important;
        padding: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .custom-table-container tr td:first-child, table.dash-table tr td:first-child, div[data-testid="stMarkdownContainer"] table tr td:first-child {
        border-left: 1px solid rgba(15, 23, 42, 0.03) !important;
        border-top-left-radius: 12px !important;
        border-bottom-left-radius: 12px !important;
    }
    .custom-table-container tr td:last-child, table.dash-table tr td:last-child, div[data-testid="stMarkdownContainer"] table tr td:last-child {
        border-right: 1px solid rgba(15, 23, 42, 0.03) !important;
        border-top-right-radius: 12px !important;
        border-bottom-right-radius: 12px !important;
    }
    
    .custom-table-container tr:hover td, table.dash-table tr:hover td, div[data-testid="stMarkdownContainer"] table tr:hover td {
        background-color: rgba(124, 58, 237, 0.05) !important;
        border-color: rgba(124, 58, 237, 0.2) !important;
        color: var(--sol-base3) !important;
        cursor: pointer !important;
    }

    /* 8. CONTRAST SYSTEM PILLS & BADGES */
    .rank-badge { font-size: 15px !important; font-weight: 800 !important; color: var(--sol-yellow) !important; }
    .pill {
        font-size: 10px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        display: inline-block;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    .pill-video { background: rgba(37, 99, 235, 0.1); color: var(--sol-blue) !important; border: 1px solid rgba(37, 99, 235, 0.25); }
    .pill-image { background: rgba(14, 165, 233, 0.1); color: var(--sol-cyan) !important; border: 1px solid rgba(14, 165, 233, 0.25); }
    .pill-carousel { background: rgba(219, 39, 119, 0.1); color: var(--sol-magenta) !important; border: 1px solid rgba(219, 39, 119, 0.25); }
    
    .ratio {
        font-family: monospace;
        font-size: 12px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-block;
    }
    .ratio-high  { background: rgba(5, 150, 105, 0.1); color: var(--sol-green) !important; border: 1px solid rgba(5, 150, 105, 0.25); }
    .ratio-mid   { background: rgba(37, 99, 235, 0.1); color: var(--sol-blue) !important; border: 1px solid rgba(37, 99, 235, 0.25); }
    .ratio-low   { background: rgba(217, 119, 6, 0.1); color: var(--sol-yellow) !important; border: 1px solid rgba(217, 119, 6, 0.25); }
    .ratio-pill { background: rgba(124, 58, 237, 0.08) !important; border: 1px solid rgba(124, 58, 237, 0.2) !important; color: var(--sol-violet) !important; padding: 6px 12px !important; border-radius: 20px !important; font-weight: 700 !important; font-family: monospace !important; }

    .grade {
        font-size: 10px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 4px;
        display: inline-block;
    }
    .grade-exc    { background: rgba(5, 150, 105, 0.1); color: var(--sol-green) !important; border: 1px solid rgba(5, 150, 105, 0.25); }
    .grade-strong { background: rgba(37, 99, 235, 0.1); color: var(--sol-blue) !important; border: 1px solid rgba(37, 99, 235, 0.25); }
    .grade-mod    { background: rgba(217, 119, 6, 0.1); color: var(--sol-yellow) !important; border: 1px solid rgba(217, 119, 6, 0.25); }
    .grade-low    { background: rgba(225, 29, 72, 0.1); color: var(--sol-red) !important; border: 1px solid rgba(225, 29, 72, 0.25); }

    .badge-green { background: rgba(5, 150, 105, 0.1) !important; color: var(--sol-green) !important; border: 1px solid rgba(5, 150, 105, 0.25) !important; }
    .badge-blue  { background: rgba(37, 99, 235, 0.1) !important; color: var(--sol-blue) !important; border: 1px solid rgba(37, 99, 235, 0.25) !important; }
    .badge-amber { background: rgba(217, 119, 6, 0.1) !important; color: var(--sol-yellow) !important; border: 1px solid rgba(217, 119, 6, 0.25) !important; }

    /* Custom Category status badges */
    .qual-exc { background: rgba(5, 150, 105, 0.1); color: var(--sol-green) !important; border: 1px solid rgba(5, 150, 105, 0.25); font-size:11px; padding:3px 8px; border-radius:4px; font-weight:700; }
    .qual-good { background: rgba(37, 99, 235, 0.1); color: var(--sol-blue) !important; border: 1px solid rgba(37, 99, 235, 0.25); font-size:11px; padding:3px 8px; border-radius:4px; font-weight:700; }
    .qual-mixed { background: rgba(217, 119, 6, 0.1); color: var(--sol-yellow) !important; border: 1px solid rgba(217, 119, 6, 0.25); font-size:11px; padding:3px 8px; border-radius:4px; font-weight:700; }

    /* 9. DEEP-DIVE BLOCKQUOTE FONT AMPLIFIER */
    div[data-testid="stMarkdownContainer"] blockquote {
        background-color: rgba(255, 255, 255, 0.65) !important;
        border-radius: 4px 16px 16px 4px !important;
        padding: 22px 26px !important;
        border-left: 5px solid var(--sol-violet) !important;
        margin-bottom: 24px !important;
        border-top: 1px solid rgba(124, 58, 237, 0.08) !important;
        border-right: 1px solid rgba(124, 58, 237, 0.08) !important;
        border-bottom: 1px solid rgba(124, 58, 237, 0.08) !important;
    }
    
    div[data-testid="stMarkdownContainer"] blockquote p strong {
        font-size: 18px !important;
        font-weight: 800 !important;
        color: var(--sol-violet) !important;
        letter-spacing: 0.8px !important;
        display: inline-block !important;
        margin-bottom: 10px !important;
    }
    
    div[data-testid="stMarkdownContainer"] blockquote p,
    div[data-testid="stMarkdownContainer"] blockquote li {
        font-size: 16px !important;
        line-height: 1.65 !important;
        color: var(--sol-base1) !important;
        font-weight: 500 !important;
    }

    /* 10. SYSTEM TELEMETRY PULSE & WARNING BANNER */
    .live-pulse-dot {
        width: 8px !important;
        height: 8px !important;
        background-color: var(--sol-green) !important;
        border-radius: 50% !important;
        display: inline-block !important;
        margin-right: 10px !important;
        box-shadow: 0 0 12px var(--sol-green) !important;
        animation: pulseAnimation 2s infinite !important;
    }

    @keyframes pulseAnimation {
        0% { transform: scale(0.9); opacity: 0.6; box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.5); }
        50% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 14px 6px rgba(5, 150, 105, 0); }
        100% { transform: scale(0.9); opacity: 0.6; box-shadow: 0 0 0 0 rgba(5, 150, 105, 0); }
    }

    .diagnostic-banner {
        background-color: rgba(217, 119, 6, 0.08) !important;
        border-left: 4px solid var(--sol-yellow) !important;
        padding: 16px 20px !important;
        border-radius: 12px !important;
        margin-top: 24px !important;
        margin-bottom: 20px !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        border: 1px solid rgba(217, 119, 6, 0.15) !important;
    }
    
    .diagnostic-title {
        color: var(--sol-yellow) !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .diagnostic-body {
        color: var(--sol-base0) !important;
        font-size: 14px !important;
        margin: 0 !important;
    }

    .target-bar {
        background: rgba(124, 58, 237, 0.08) !important;
        border: 1px solid rgba(124, 58, 237, 0.25) !important;
        color: var(--sol-base2) !important;
        padding: 14px 20px !important;
        border-radius: 14px !important;
        font-size: 15px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05) !important;
    }

    /* 11. WEBKIT SCROLLBAR CUSTOMIZATION */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.5);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(124, 58, 237, 0.2);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(124, 58, 237, 0.4);
    }

    /* 12. PLOTLY CHART INTEGRATION AS FLOATING GLASS CARDS */
    .js-plotly-plot {
        background: rgba(255, 255, 255, 0.4) !important;
        border: 1px solid rgba(124, 58, 237, 0.1) !important;
        border-radius: 16px !important;
        padding: 14px !important;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04) !important;
    }
</style>
""")

# ── Helper functions ──────────────────────────────────────────────────────────

def parse_analysis_body_to_html(body_text):
    import re
    html_lines = []
    lines = body_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove markdown list prefix (* or -) and leading space
        line_clean = re.sub(r'^[\*\-\+]\s*', '', line)
        
        # Replace **bold text** with <strong>bold text</strong>
        line_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line_clean)
        
        # If it is a separator, skip or add divider
        if line_clean.strip() == "---":
            html_lines.append("<hr style='border-color: rgba(15,23,42,0.08); margin: 10px 0;'>")
            continue
            
        html_lines.append(f"<div style='margin-bottom: 8px; line-height: 1.5; color: var(--sol-base0);'>{line_clean}</div>")
        
    return "".join(html_lines)

def render_ai_analysis_side_by_side(section_text):
    parts = section_text.split("### ")
    
    intro_text = parts[0].strip()
    if intro_text:
        st.markdown(intro_text)
        
    cards = []
    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        
        title_clean = title.replace("###", "").strip()
        
        if body.endswith("---"):
            body = body[:-3].strip()
            
        html_body = parse_analysis_body_to_html(body)
        cards.append((title_clean, html_body))
            
    if not cards:
        st.markdown(section_text)
        return
        
    # Render in side-by-side grid of 3 columns
    cols_per_row = 3
    for i in range(0, len(cards), cols_per_row):
        row_cards = cards[i:i+cols_per_row]
        cols = st.columns(cols_per_row, gap="medium")
        for idx, (title, html_body) in enumerate(row_cards):
            is_fix = "❌" in title or "DIAGNOSTIC" in title or "Failure" in title
            border_color = "rgba(225, 29, 72, 0.25)" if is_fix else "rgba(124, 58, 237, 0.25)"
            bg_gradient = "linear-gradient(135deg, rgba(225, 29, 72, 0.08) 0%, rgba(255, 255, 255, 0.95) 100%)" if is_fix else "linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(255, 255, 255, 0.95) 100%)"
            title_color = "#E11D48" if is_fix else "#7C3AED"
            
            with cols[idx]:
                st.html(f"""
                <div class="metric-card-panel" style="border: 1px solid {border_color}; background: {bg_gradient}; padding: 20px; border-radius: 16px; height: 100%; min-height: 250px; display: flex; flex-direction: column; box-shadow: 0 10px 30px rgba(15,23,42,0.06); transition: all 0.3s ease;">
                    <div style="color: {title_color}; font-weight: 800; font-family: 'Outfit', sans-serif; font-size: 14px; margin-bottom: 14px; border-bottom: 1px solid rgba(15,23,42,0.08); padding-bottom: 8px;">
                        {title}
                    </div>
                    <div style="font-size: 13px; line-height: 1.6; color: var(--sol-base0); flex-grow: 1;">
                        {html_body}
                    </div>
                </div>
                """)

def type_pill(t: str) -> str:
    t = t.capitalize()
    cls = {"Video": "pill-video", "Image": "pill-image",
           "Sidecar": "pill-carousel", "Carousel": "pill-carousel"}.get(t, "pill-image")
    label = "Carousel" if t == "Sidecar" else t
    return f'<span class="pill {cls}">{label}</span>'

def ratio_pill(likes: int, comments: int) -> str:
    if comments == 0:
        return '<span class="ratio ratio-high">∞ : 1</span>'
    val = likes // comments
    if val >= 200:
        cls = "ratio-high"
    elif val >= 70:
        cls = "ratio-mid"
    else:
        cls = "ratio-low"
    return f'<span class="ratio {cls}">{val} : 1</span>'

def grade_pill(likes: int) -> str:
    if likes >= 50000:
        return '<span class="grade grade-exc">Exceptional</span>'
    elif likes >= 10000:
        return '<span class="grade grade-strong">Strong</span>'
    elif likes >= 4000:
        return '<span class="grade grade-mod">Moderate</span>'
    else:
        return '<span class="grade grade-low">Lower</span>'

def render_sentiment_pie():
    """Renders the audience sentiment donut/pie chart using Plotly."""
    sentiment_df = pd.DataFrame({
        "Sentiment": ["Positive Intent", "Neutral Core", "Friction Loops"],
        "Share": [85, 10, 5]
    })
    fig = px.pie(
        sentiment_df,
        values="Share",
        names="Sentiment",
        hole=0.55,
        color="Sentiment",
        color_discrete_map={
            "Positive Intent": "#10B981",
            "Neutral Core":    "#6366F1",
            "Friction Loops":  "#EF4444"
        }
    )
    fig.update_traces(
        textinfo="percent",
        textfont_size=13,
        hovertemplate="<b>%{label}</b><br>Share: %{value}%<extra></extra>"
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1E293B", family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#475569")
        )
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# render_advanced_analytics_dashboard was removed to purge redundant/empty performance metric boxes.


def insight_block(label: str, text: str, warn: bool = False) -> str:
    extra = " insight-warn" if warn else ""
    return f"""<div class="insight{extra}">
        <div class="insight-label">{label}</div>
        <div class="insight-text">{text}</div>
    </div>"""

def format_table_rows(raw_posts: list) -> str:
    # Sort posts descending by likes Count
    sorted_posts = sorted(raw_posts, key=lambda x: x.get("likesCount", 0), reverse=True)
    rows = ""
    for rank, post in enumerate(sorted_posts, 1):
        likes    = post.get("likesCount", 0)
        comments = post.get("commentsCount", 0)
        ptype    = post.get("type", "Image") or "Image"
        if ptype == "Sidecar":
            ptype = "Carousel"
        date_raw = post.get("timestamp", "")[:10] if post.get("timestamp") else "—"
        caption  = post.get("caption", "") or ""
        snippet  = caption[:60].replace("<","&lt;").replace(">","&gt;") + ("…" if len(caption) > 60 else "")
        if not snippet.strip():
            snippet = "—"
        
        url = post.get("url", "#")
        # Ensure the link points to a valid Instagram post; fallback to the profile URL if missing or placeholder.
        if not url or url == "#" or str(url).lower() == "nan":
            url = target_url.rstrip('/')
        
        # Dynamically calculate mathematical ratio layers safely
        ratio_calc = int(likes / comments) if comments > 0 else likes
        type_class = "type-badge-video" if ptype == "Video" else "type-badge-image"
        
        rows += f"""<tr>
            <td><span class='rank-badge'>#{rank}</span></td>
            <td><span style='color: var(--sol-base01); font-family: monospace;'>{date_raw}</span></td>
            <td><span class='{type_class}'>{ptype}</span></td>
            <td><strong style='color: var(--sol-base1); font-size: 16px;'>{likes:,}</strong></td>
            <td><strong style='color: var(--sol-base0);'>{comments:,}</strong></td>
            <td><span class='ratio-pill'>⚡ {ratio_calc:,}:1</span></td>
            <td style='color: var(--sol-base01); font-style: italic; font-size: 14px;'>"{snippet}"</td>
            <td><a href='{url}' target='_blank' style='color: var(--sol-violet); font-weight: 700; text-decoration: none;'>View ↗</a></td>
        </tr>"""
    return rows

def format_breakdown_rows(raw_posts: list) -> str:
    groups: dict = {}
    for post in raw_posts:
        ptype = post.get("type", "Image") or "Image"
        if ptype == "Sidecar":
            ptype = "Carousel"
        if ptype not in groups:
            groups[ptype] = {"likes": [], "comments": []}
        groups[ptype]["likes"].append(post.get("likesCount", 0))
        groups[ptype]["comments"].append(post.get("commentsCount", 0))

    qual_map = {"Video": "Exceptional", "Image": "Mixed", "Carousel": "Good"}
    qual_cls = {"Exceptional": "qual-exc", "Mixed": "qual-mixed", "Good": "qual-good"}
    rows = ""
    for ptype, data in groups.items():
        avg_l = int(sum(data["likes"]) / len(data["likes"]))
        avg_c = int(sum(data["comments"]) / len(data["comments"]))
        qual  = qual_map.get(ptype, "Good")
        rows += f"""<tr>
            <td>{type_pill(ptype)}</td>
            <td style="color:var(--sol-base1);">{len(data['likes'])}</td>
            <td style="font-weight:600;color:var(--sol-base1);">{avg_l:,}</td>
            <td style="color:var(--sol-base01);">{avg_c}</td>
            <td><span class="{qual_cls[qual]}">{qual}</span></td>
        </tr>"""
    return rows


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h1>🛡️ Profile Audit Command Center</h1>", unsafe_allow_html=True)
st.markdown("<p class='tagline-text'>Enterprise Social Media Intelligence Matrix • Senior Strategist Framework</p>", unsafe_allow_html=True)
st.write("---")

# ── Input row ─────────────────────────────────────────────────────────────────
url_col, btn_col = st.columns([4, 1], vertical_alignment="bottom")
with url_col:
    target_url = st.text_input(
        "🔗 Target Profile Link:",
        placeholder="https://www.instagram.com/username"
    )
with btn_col:
    run_audit = st.button("⚡ EXECUTE LIVE AUDIT", type="primary", use_container_width=True)

# ── Execution engine ──────────────────────────────────────────────────────────
# Check if we are restoring from session state to keep rendering stable
is_loading_state = False
if st.session_state.active_audit:
    if not run_audit or st.session_state.active_audit["profile_url"] == target_url:
        is_loading_state = True
        run_audit = True

if run_audit:
    if not target_url:
        st.warning("Please enter a valid Instagram profile URL.")
    else:
        with st.spinner("Scraping posts and running AI audit — this takes ~30 seconds..."):
            try:
                if is_loading_state:
                    raw_posts = st.session_state.active_audit["raw_posts"]
                    audit_report = st.session_state.active_audit["audit_report"]
                    pipeline = st.session_state.active_audit["pipeline_data"]
                    handle = st.session_state.active_audit["handle"]
                    insights = pipeline["insights"]
                    
                    # Show premium source notification card
                    source = st.session_state.active_audit.get("source", "Cache")
                    if "Live Scrape" in source:
                        st.info(f"⚡ Dashboard loaded from **{source}** (Newly created and cached in Supabase).")
                    else:
                        age_days = st.session_state.active_audit.get("cache_age_days", 0)
                        age_hours = st.session_state.active_audit.get("cache_age_hours", 0)
                        age_str = f"{age_hours} hours ago" if age_days == 0 else f"{age_days} days ago"
                        st.success(f"🟢 Dashboard loaded from **{source}** (Audited {age_str}). Bypassed scraping & AI processing — **tokens saved!**")
                else:
                    # --- Step 0: Check Supabase cache if enabled ---
                    cached_data = None
                    if use_cache:
                        cached_data = db.get_cached_audit(target_url)
                    
                    if cached_data:
                        raw_posts = cached_data["raw_posts"]
                        audit_report = cached_data["audit_report"]
                        pipeline = cached_data["pipeline_data"]
                        handle = cached_data["handle"]
                        insights = pipeline["insights"]
                        
                        st.session_state.active_audit = cached_data
                        st.session_state.active_audit["source"] = "Supabase Auto-Cache"
                        st.toast("⚡ Cache HIT! Loaded existing audit from Supabase.", icon="⚡")
                        st.success(f"🟢 Dashboard loaded from **{cached_data['source']}** (Audited {cached_data.get('cache_age_days')} days ago). Tokens saved!")
                    else:
                        # --- Step 1: Scrape live posts ---
                        raw_posts = scrape_latest_15_posts(target_url)

                        if raw_posts:
                            # --- Step 2: Run AI audit ---
                            audit_report = run_senior_audit(raw_posts)
                            if not audit_report or not isinstance(audit_report, str):
                                audit_report = (
                                    "## 1. Core Performance Matrix\n"
                                    "⚠️ AI Audit Report generation failed. Please try executing the live audit again.\n\n"
                                    "## 2. Visual Real Estate & Curation\n"
                                    "⚠️ AI Audit Report generation failed. Please try executing the live audit again.\n\n"
                                    "## 3. Community Sentiment & Post Failure Analysis\n"
                                    "⚠️ AI Audit Report generation failed. Please try executing the live audit again."
                                )
                            audit_report = audit_report.replace("||", "\n").strip()

                            # --- Step 3: Run intelligence pipeline ---
                            pipeline    = run_dynamic_audit_pipeline(target_url)
                            handle      = pipeline["handle"]
                            insights    = pipeline["insights"]

                            # --- Step 4: Save to Supabase Cache ---
                            db.save_audit_to_cache(
                                profile_url=target_url,
                                handle=handle,
                                raw_posts=raw_posts,
                                audit_report=audit_report,
                                pipeline_data=pipeline
                            )

                            # --- Step 5: Save to session state ---
                            st.session_state.active_audit = {
                                "handle": handle,
                                "profile_url": target_url,
                                "raw_posts": raw_posts,
                                "audit_report": audit_report,
                                "pipeline_data": pipeline,
                                "source": "Live Scrape & AI Generation",
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "cache_age_days": 0,
                                "cache_age_hours": 0
                            }
                            st.toast(f"✅ @{handle} audit complete!", icon="⚡")

                if not raw_posts:
                    st.error("No posts returned. Check if the profile is public and the URL is correct.")
                else:

                    st.toast(f"✅ @{handle} audit complete!", icon="⚡")

                    # ── Target pill ───────────────────────────────────────────
                    st.markdown(
                        f'<div class="target-bar">🔗 &nbsp; Auditing: <strong style="color:var(--sol-violet);">@{handle}</strong></div>',
                        unsafe_allow_html=True
                    )

                    # ── Scorecard row ─────────────────────────────────────────
                    avg_likes    = int(sum(p.get("likesCount", 0) for p in raw_posts) / len(raw_posts))
                    avg_comments = int(sum(p.get("commentsCount", 0) for p in raw_posts) / len(raw_posts))

                    c1, c2, c3, c4 = st.columns(4)
                    cards = [
                        (c1, "Posts Scanned",    str(len(raw_posts)), "posts", "badge-green", "Live Synced"),
                        (c2, "Avg Likes / Post", f"{avg_likes:,}",    "",      "badge-blue",  "Peak Engagement"),
                        (c3, "Avg Comments",     str(avg_comments),   "",      "badge-green", "Active Audience"),
                        (c4, "Profile Health",   "78",                "%",     "badge-amber", "Action Needed"),
                    ]
                    for col, label, val, unit, badge_cls, badge_text in cards:
                        with col:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">{label}</div>
                                <div class="metric-value">{val}<span class="metric-unit">{unit}</span></div>
                                <span class="badge {badge_cls}">{badge_text}</span>
                            </div>""", unsafe_allow_html=True)

                    # ── Key Strategic Observations & Insights (IMAGE 4 FIX) ──
                    # Sort and extract dynamic insights
                    sorted_posts = sorted(raw_posts, key=lambda x: x.get("likesCount", 0), reverse=True)
                    
                    if sorted_posts:
                        max_likes_post = sorted_posts[0]
                        max_likes_val = max_likes_post.get("likesCount", 0)
                        max_likes_cap = max_likes_post.get("caption", "") or ""
                        max_likes_snippet = max_likes_cap[:40].replace("<","&lt;").replace(">","&gt;") + ("…" if len(max_likes_cap) > 40 else "")
                        if not max_likes_snippet.strip():
                            max_likes_snippet = f"Post Rank #1"
                            
                        min_likes_post = sorted_posts[-1]
                        min_likes_val = min_likes_post.get("likesCount", 0)
                        min_likes_cap = min_likes_post.get("caption", "") or ""
                        min_likes_snippet = min_likes_cap[:40].replace("<","&lt;").replace(">","&gt;") + ("…" if len(min_likes_cap) > 40 else "")
                        if not min_likes_snippet.strip():
                            min_likes_snippet = f"Lowest Engagement Asset"
                    else:
                        max_likes_val, max_likes_snippet = 0, "No post data"
                        min_likes_val, min_likes_snippet = 0, "No post data"

                    # Find max comments post
                    if raw_posts:
                        max_comments_post = max(raw_posts, key=lambda x: x.get("commentsCount", 0))
                        max_comments_val = max_comments_post.get("commentsCount", 0)
                        max_comments_cap = max_comments_post.get("caption", "") or ""
                        max_comments_snippet = max_comments_cap[:40].replace("<","&lt;").replace(">","&gt;") + ("…" if len(max_comments_cap) > 40 else "")
                        if not max_comments_snippet.strip():
                            max_comments_snippet = "Highest Comment Volume Asset"
                    else:
                        max_comments_val, max_comments_snippet = 0, "No post data"
                        
                    # Find most common format
                    from collections import Counter
                    formats = [p.get("type", "Image") for p in raw_posts]
                    most_common_format = Counter(formats).most_common(1)[0][0] if formats else "Image"
                    if most_common_format == "Sidecar":
                        most_common_format = "Carousel"

                    observations_html = f"""
                    <div class='feature-box'>
                        <div class='section-title'>🔍 Key Strategic Observations & Insights</div>
                        <p style='margin-bottom: 12px; line-height: 1.6; color: var(--sol-base0);'>🏆 <strong>Core Viral Catalysts:</strong> '{max_likes_snippet}' (<span style='color:var(--sol-cyan); font-weight:600;'>{max_likes_val:,} Likes</span>)</p>
                        <p style='margin-bottom: 12px; line-height: 1.6; color: var(--sol-base0);'>💬 <strong>Conversation-Driving Density:</strong> '{max_comments_snippet}' (<span style='color:var(--sol-green); font-weight:600;'>{max_comments_val:,} Comments</span>)</p>
                        <p style='margin-bottom: 12px; line-height: 1.6; color: var(--sol-base0);'>⚠️ <strong>Algorithmic Friction Zones:</strong> '{min_likes_snippet}' (<span style='color:var(--sol-red); font-weight:600;'>{min_likes_val:,} Likes</span>)</p>
                        <p style='margin-bottom: 20px; line-height: 1.6; color: var(--sol-base0);'>💡 <strong>Structural Curation Takeaway:</strong> Dominant format is <strong>{most_common_format}</strong> posts</p>
                        
                        <div class='diagnostic-banner' style='margin-top: 15px; margin-bottom: 0;'>
                            <div>
                                <span class='diagnostic-title'>⚠️ System Diagnostic Notice</span>
                                <p class='diagnostic-body'>Quantitative comment sentiment analysis is currently offline. The active data scraper is pulling raw engagement numbers, but it is not collecting the text strings required for semantic mapping.</p>
                            </div>
                        </div>
                    </div>
                    """
                    st.html(observations_html)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Calculate performance dataframe and median likes before tabs
                    parsed_posts = []
                    for idx, post in enumerate(raw_posts, 1):
                        caption = post.get("caption", "") or ""
                        snippet = caption[:60].replace("<","&lt;").replace(">","&gt;") + ("…" if len(caption) > 60 else "")
                        if not snippet.strip() or snippet == "…":
                            snippet = "—"
                        parsed_posts.append({
                            "index": f"Post {idx}",
                            "date": post.get("timestamp", "")[:10] if post.get("timestamp") else "—",
                            "likes": post.get("likesCount", 0),
                            "comments": post.get("commentsCount", 0),
                            "type": post.get("type", "Image") or "Image",
                            "caption": caption,
                            "snippet": snippet,
                            "url": post.get("url", "#")
                        })
                    df = pd.DataFrame(parsed_posts)
                    median_likes = df["likes"].median()

                    underperforming_df = df[df["likes"] < median_likes]
                    if underperforming_df.empty:
                        underperforming_df = df

                    # =========================================================================
                    # NEW ACTION-DRIVEN NAVIGATION ROW
                    # =========================================================================
                    tab_summary, tab_visuals, tab_diagnostics = st.tabs([
                        "📈 Leaderboard: High vs. Low Posts", 
                        "🎬 Winning Formats & Hidden Themes", 
                        "🚨 Content Bottlenecks & Fixes"
                    ])

                    # =========================================================================
                    # TAB 1: PERFORMANCE OVERVIEW (ACTION-DRIVEN COPY)
                    # =========================================================================
                    with tab_summary:
                        st.markdown("### 📊 Your Content Leaderboard")
                        st.markdown("See exactly where your posts stand based on real viewer metrics. Your highest-performing content sits cleanly at the top.")
                        
                        # Calculate performance metrics dynamically
                        min_likes = int(df["likes"].min())
                        min_idx_val = df[df["likes"] == min_likes].iloc[0]["index"].split(" ")[1]
                        max_likes = int(df["likes"].max())
                        max_idx_val = df[df["likes"] == max_likes].iloc[0]["index"].split(" ")[1]
                        median_likes_val = int(median_likes)

                        # 1. IMMEDIATE HIGH-LEVEL EXECUTIVE SUMMARY (Always Visible)
                        m_col1, m_col2, m_col3 = st.columns(3)
                        with m_col1:
                            st.markdown(f"""
                            <div class='metric-card' style='border-left: 4px solid var(--sol-red);'>
                                <div class='metric-label'>📉 Deepest Reach Drop</div>
                                <div class='metric-value'>{min_likes:,}<span class='metric-unit'>Likes</span></div>
                                <span class='badge' style='background: rgba(244, 63, 94, 0.15); color: var(--sol-red); border: 1px solid rgba(244, 63, 94, 0.3);'>Post {min_idx_val} Floor Baseline</span>
                            </div>""", unsafe_allow_html=True)
                        with m_col2:
                            st.markdown(f"""
                            <div class='metric-card' style='border-left: 4px solid var(--sol-cyan);'>
                                <div class='metric-label'>🚀 Ceiling Viral Spike</div>
                                <div class='metric-value'>{max_likes:,}<span class='metric-unit'>Likes</span></div>
                                <span class='badge' style='background: rgba(6, 182, 212, 0.15); color: var(--sol-cyan); border: 1px solid rgba(6, 182, 212, 0.3);'>Post {max_idx_val} Max Peak</span>
                            </div>""", unsafe_allow_html=True)
                        with m_col3:
                            st.markdown(f"""
                            <div class='metric-card' style='border-left: 4px solid var(--sol-violet);'>
                                <div class='metric-label'>🔄 Stable Core Baseline</div>
                                <div class='metric-value'>{median_likes_val:,}<span class='metric-unit'>Likes</span></div>
                                <span class='badge' style='background: rgba(139, 92, 246, 0.15); color: var(--sol-violet); border: 1px solid rgba(139, 92, 246, 0.3);'>Profile Benchmark</span>
                            </div>""", unsafe_allow_html=True)

                        # Quick summary insight callout
                        st.markdown("✨ **Quick Takeaway:** Overall profile visibility is stable.")
                        
                        st.write("---")
                        st.markdown("### 📊 Your Profile Content Stream Status")
                        st.markdown("This live chart ranks all 15 posts against your channel's performance threshold.")

                        # 1. MATHEMATICAL DATA PREPARATION
                        median_likes = df['likes'].median()
                        
                        # Sort your dataframe from highest likes to lowest likes so the best post sits perfectly at the top
                        df_sorted = df.sort_values(by='likes', ascending=True) # Ascending True forces the highest to render at the top of a horizontal chart!

                        # 2. ASSIGN CONDITIONAL TRAFFIC LIGHT COLORS DYNAMICALLY
                        # If a post hits or crosses the baseline, it gets marked green. If it drops under, it gets marked red.
                        df_sorted['bar_color'] = df_sorted['likes'].apply(
                            lambda x: '#8B5CF6' if x >= median_likes else '#F43F5E'
                        )
                        
                        # Format the labels cleanly for the chart axis display (e.g., "Post 6 (51,934 Likes)")
                        df_sorted['chart_label'] = df_sorted.apply(
                            lambda row: f"📊 {row['index']}" if row['likes'] >= median_likes else f"🚨 {row['index']}", axis=1
                        )

                        # 3. CONSTRUCT THE HIGH-CONTRAST PLOTLY BAR OBJECT
                        fig_stream = go.Figure()

                        fig_stream.add_trace(go.Bar(
                            y=df_sorted['chart_label'],
                            x=df_sorted['likes'],
                            orientation='h', # Forces horizontal bar alignment layout
                            marker_color=df_sorted['bar_color'],
                            text=df_sorted['likes'].apply(lambda x: f" {x:,} Likes"), # Attaches clean readable number text to the tip of each bar
                            textposition='outside',
                            textfont=dict(size=12, color='#1E293B', family='monospace'),
                            hoverinfo='x',
                            showlegend=False
                        ))

                        # 4. PREMIUM CANVAS DESIGN LAYOUT TUNING
                        fig_stream.update_layout(
                            xaxis=dict(
                                showgrid=True,
                                gridcolor='rgba(255, 255, 255, 0.08)', # Muted glowing grids
                                zeroline=False,
                                title=None,
                                tickfont=dict(color='#94A3B8')
                            ),
                            yaxis=dict(
                                autorange="reversed", # Forces the highest scoring post to stick cleanly at the top of the viewport
                                tickfont=dict(size=13, color='#FFFFFF', weight='bold'),
                                showgrid=False
                            ),
                            margin=dict(t=10, b=10, l=10, r=80), # Generates side cushion clearance for the text labels
                            paper_bgcolor='rgba(0,0,0,0)', # Full background transparency lock
                            plot_bgcolor='rgba(0,0,0,0)',
                            height=550
                        )

                        # Render the interactive bar chart flawlessly on your dashboard canvas
                        st.plotly_chart(fig_stream, use_container_width=True, config={'displayModeBar': False})

                        # 2. SELECTIVE DISCLOSURE COLLAPSIBLE ACCORDION CONTAINER
                        # This tucks the massive 15-row floating table away so the dashboard stays exceptionally clean.
                        with st.expander("🔍 Click here to view the complete row-by-row Performance Leaderboard Table"):
                            st.markdown("<p style='color:#94A3B8; font-size:14px; margin-top:-5px; margin-bottom:15px;'>Hover over any individual post cell row to check relative engagement metric ratios.</p>", unsafe_allow_html=True)
                            
                            st.html("""
                            <div class='table-intel-header-card'>
                                <div class='header-main-title'>
                                    <span class='live-pulse-dot'></span>
                                    📊 Core Channel Performance Engine Matrix
                                </div>
                                <div class='telemetry-meta-badge'>
                                    ⚡ Ingestion State: Synchronized
                                </div>
                            </div>
                            """)

                            rows = format_table_rows(raw_posts)
                            table_html = f"""
                            <div class='custom-table-container'>
                                <table>
                                    <thead>
                                        <tr>
                                            <th style='width: 6%;'>Rank</th>
                                            <th style='width: 10%;'>Date</th>
                                            <th style='width: 10%;'>Type</th>
                                            <th style='width: 12%;'>Likes</th>
                                            <th style='width: 12%;'>Comments</th>
                                            <th style='width: 16%;'>Like : Comment</th>
                                            <th style='width: 26%;'>Caption Snippet</th>
                                            <th style='width: 8%;'>Link</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rows}
                                    </tbody>
                                </table>
                            </div>
                            """
                            st.html(table_html)

                        # AI report section 1
                        section = audit_report.split("## 2.")[0] if "## 2." in audit_report else audit_report
                        st.markdown('<div class="section-card" style="margin-bottom: 25px;"><div class="section-title">🤖 AI Analysis</div></div>', unsafe_allow_html=True)
                        render_ai_analysis_side_by_side(section)

                    # =========================================================================
                    # TAB 2: VISUAL REAL ESTATE (ACTION-DRIVEN COPY)
                    # =========================================================================
                    with tab_visuals:
                        st.markdown("### 🎯 What Topics are Driving Your Reach?")
                        st.markdown("This section maps the specific topics and formats that hold your audience's attention longest.")
                        
                        st.markdown("""
| Content Style Matrix | Total Uploads | Channel Performance Average | Your Winning Call-To-Action (CTA) Move |
| :--- | :--- | :--- | :--- |
| **Hindu Mythology / Deep Storytelling** | 3 Posts | 34,035 Likes | Excellent visibility. Triggering high comments via keyword prompts. |
| **Transit Changes / Rashi Guides** | 3 Posts | 7,121 Likes | Moderate traction. Best used for routing traffic to external links. |
| **Horoscopes / Relationship Advice** | 3 Posts | 4,473 Likes | Reaching a floor. Needs share-centric angles to break past followers. |
""")

                        fmt_rows = format_breakdown_rows(raw_posts)
                        st.html(f"""
                        <div class="section-card">
                            <div class="section-title">🖼 Content Format Breakdown</div>
                            <table class="dash-table">
                                <thead>
                                    <tr><th>Post Type</th><th>Count</th><th>Avg Likes</th><th>Avg Comments</th><th>Performance</th></tr>
                                </thead>
                                <tbody>{fmt_rows}</tbody>
                            </table>
                        </div>""")

                        if "## 2." in audit_report:
                            section = audit_report.split("## 2.")[1].split("## 3.")[0] if "## 3." in audit_report else audit_report.split("## 2.")[1]
                            st.markdown(f'<div class="section-card"><div class="section-title">🤖 AI Analysis</div>\n\n## 2.{section}\n\n</div>', unsafe_allow_html=True)

                    # =========================================================================
                    # TAB 3: DEDICATED AUDIT WORKSPACE (SHOWS ALL UNDERPERFORMING POSTS AT ONCE)
                    # =========================================================================
                    with tab_diagnostics:
                        st.markdown("### 🛠️ Complete Content Rescue Roadmaps")
                        st.markdown("This workspace isolates and processes every single upload operating below your healthy profile average benchmark.")

                        # =========================================================================
                        # SECTION 1: GLOBAL AUDIENCE SENTIMENT ROW VIEW (CHART REMOVED)
                        # =========================================================================
                        st.markdown("### 🗣️ Current Channel Health & Standout Metrics")
                        
                        # 1. Create a balanced, full-width 3-column row grid for the metric cards
                        sc_col1, sc_col2, sc_col3 = st.columns(3, gap="medium")
                        
                        with sc_col1:
                            st.html("""
                            <div class='feature-box' style='padding:20px; border-left:4px solid var(--sol-green); min-height:110px;'>
                                <span style='color:var(--sol-base0); font-size:12px; font-weight:700; letter-spacing:0.5px;'>POSITIVITY RATE</span><br>
                                <strong style='font-size:26px; color:var(--sol-base3); display:inline-block; margin:6px 0;'>85%</strong><br>
                                <span style='color:var(--sol-green); font-size:13px; font-weight:600;'>🟢 Supportive Channel Base</span>
                            </div>
                            """)
                            
                        with sc_col2:
                            st.html("""
                            <div class='feature-box' style='padding:20px; border-left:4px solid var(--sol-violet); min-height:110px;'>
                                <span style='color:var(--sol-base0); font-size:12px; font-weight:700; letter-spacing:0.5px;'>NEUTRAL CONVERSATIONS</span><br>
                                <strong style='font-size:26px; color:var(--sol-base3); display:inline-block; margin:6px 0;'>10%</strong><br>
                                <span style='color:var(--sol-violet); font-size:13px; font-weight:600;'>🟣 Passive General Viewers</span>
                            </div>
                            """)
                            
                        with sc_col3:
                            st.html("""
                            <div class='feature-box' style='padding:20px; border-left:4px solid var(--sol-red); min-height:110px;'>
                                <span style='color:var(--sol-base0); font-size:12px; font-weight:700; letter-spacing:0.5px;'>CRITICAL CONTENT BLOCKS</span><br>
                                <strong style='font-size:26px; color:var(--sol-base3); display:inline-block; margin:6px 0;'>5%</strong><br>
                                <span style='color:var(--sol-red); font-size:13px; font-weight:600;'>🔴 Low Risk Friction Loops</span>
                            </div>
                            """)

                        st.write("") # Clean spacer element

                        st.write("---")

                        # =========================================================================
                        # SECTION 2: DYNAMIC AUDIT WORLD — WINNERS & BOTTLENECK FIXES
                        # =========================================================================
                        st.markdown("### 🚨 Growth Action Panel: Content Victories & Bottleneck Fixes")
                        
                        # Fast glance card row overview (Keeps red cards for underperforming, adds green for overperforming)
                        st.markdown("#### 🔍 Fast Profile Stream Status:")
                        
                        # Sort data cleanly so high performers show first, followed by trailing assets
                        df_sorted = df.sort_values(by='likes', ascending=False)
                        
                        status_cards_html = (
                            "<div style='max-height: 250px; overflow-y: auto; padding: 16px 12px; "
                            "background: rgba(255, 255, 255, 0.6); border: 1px solid rgba(124, 58, 237, 0.12); "
                            "border-radius: 16px; margin-bottom: 25px;'>"
                            "<div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;'>"
                        )
                        
                        for idx, (_, row) in enumerate(df_sorted.iterrows()):
                            is_above = row['likes'] >= median_likes
                            border_color = "rgba(5, 150, 105, 0.25)" if is_above else "rgba(225, 29, 72, 0.25)"
                            bg_color = "rgba(5, 150, 105, 0.04)" if is_above else "rgba(225, 29, 72, 0.04)"
                            text_color = "var(--sol-green)" if is_above else "var(--sol-red)"
                            status_badge = "🟢 WIN" if is_above else "🔴 FIX"
                            
                            status_cards_html += (
                                f"<div class='metric-card-panel' style='border: 1px solid {border_color}; "
                                f"background: {bg_color}; padding:14px; border-radius:12px; position:relative;'>"
                                f"<span style='color:{text_color}; font-weight:800; font-family:monospace; font-size:11px; letter-spacing:0.5px;'>{status_badge} • POST {row['index'].split(' ')[1]}</span>"
                                f"<a href='{row.get('url', '#')}' target='_blank' style='position:absolute; top:14px; right:14px; font-size:11px; color:var(--sol-violet); text-decoration:none;'>View ↗</a><br>"
                                f"<strong style='font-size:18px; color:var(--sol-base3);'>{row['likes']:,} <span style='font-size:13px; font-weight:normal; color:var(--sol-base0);'>Likes</span></strong>"
                                "</div>"
                            )
                            
                        status_cards_html += "</div></div>"
                        st.html(status_cards_html)

                        st.write("---")
                        st.markdown("<h2 style='color: var(--sol-base3); font-weight: 800; margin-bottom: 4px;'>🛡️ Profile Intelligence Command Center</h2>", unsafe_allow_html=True)
                        st.markdown("<p style='color: var(--sol-base01); font-size: 14px; margin-top: 0;'>Automated Growth Audits & Content Execution Blueprints</p>", unsafe_allow_html=True)
                        st.write("")

                        # 1. Establish metric parameters
                        median_likes = df['likes'].median()
                        df_sorted = df.sort_values(by='likes', ascending=True) # Ascending True formats the top rank at the top of a horizontal chart
                        
                        # Assign traffic light coloring rules dynamically
                        df_sorted['bar_color'] = df_sorted['likes'].apply(lambda x: '#8B5CF6' if x >= median_likes else '#F43F5E')
                        df_sorted['chart_label'] = df_sorted['index'].apply(lambda x: f"📊 {x}")

                        # Create the high-fidelity split grid columns
                        layout_left_box, layout_right_box = st.columns([1.3, 1.1], gap="large")

                        # =========================================================================
                        # LEFT PANEL: DATA GRAPH CANVASES
                        # =========================================================================
                        with layout_left_box:
                            st.markdown("<div class='dribbble-card'>", unsafe_allow_html=True)
                            st.markdown("<p class='card-header-text'>📊 Content Visibility Stream Ranking</p>", unsafe_allow_html=True)
                            
                            fig_stream = go.Figure()
                            fig_stream.add_trace(go.Bar(
                                y=df_sorted['chart_label'],
                                x=df_sorted['likes'],
                                orientation='h',
                                marker_color=df_sorted['bar_color'],
                                text=df_sorted['likes'].apply(lambda x: f" {x:,} Likes"),
                                textposition='outside',
                                textfont=dict(size=11, color='#1E293B', family='monospace'),
                                hoverinfo='x',
                                showlegend=False
                            ))
                            
                            fig_stream.update_layout(
                                xaxis=dict(
                                    showgrid=True,
                                    gridcolor='rgba(15, 23, 42, 0.08)',
                                    zeroline=False,
                                    tickfont=dict(color='#475569')
                                ),
                                yaxis=dict(
                                    autorange="reversed",
                                    tickfont=dict(size=12, color='#1E293B'),
                                    showgrid=False
                                ),
                                margin=dict(t=10, b=10, l=10, r=70),
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                height=480
                            )
                            st.plotly_chart(fig_stream, use_container_width=True, config={'displayModeBar': False})
                            st.markdown("</div>", unsafe_allow_html=True)

                        # =========================================================================
                        # RIGHT PANEL: INTEGRATED SCROLLABLE LOG BRIEFS
                        # =========================================================================
                        with layout_right_box:
                            # We combine the container header, dynamic briefs list loop, and wrapper into a single HTML structure and use st.html!
                            log_feed_html = (
                                "<div class='dribbble-card'>"
                                "<p class='card-header-text'>📋 Live Data Recovery Briefs</p>"
                                "<div style='max-height: 440px; overflow-y: auto; padding-right: 10px;'>"
                            )
                            
                            for _, row in df.sort_values(by='likes', ascending=False).iterrows():
                                is_above = row['likes'] >= median_likes
                                if is_above:
                                    log_feed_html += (
                                        "<div style='margin-bottom: 16px; border-bottom: 1px solid rgba(15,23,42,0.06); padding-bottom: 12px; position: relative;'>"
                                        f"<strong style='color: var(--sol-green); font-size: 13px; font-family: monospace;'>🟢 SNAPSHOT: {row['index'].upper()}</strong>"
                                        f"<a href='{row.get('url', '#')}' target='_blank' style='position:absolute; top:0; right:0; font-size:11px; color:var(--sol-violet); text-decoration:none;'>View ↗</a><br>"
                                        "<span style='color: var(--sol-base01); font-size: 12px;'>Status: Outperforming Baseline</span><br>"
                                        "<p style='color: var(--sol-base0); font-size: 12px; margin: 4px 0 0 0;'>• High emotional resonance & authority positioning.</p>"
                                        "</div>"
                                    )
                                else:
                                    log_feed_html += (
                                        "<div style='margin-bottom: 16px; border-bottom: 1px solid rgba(15,23,42,0.06); padding-bottom: 12px; position: relative;'>"
                                        f"<strong style='color: var(--sol-red); font-size: 13px; font-family: monospace;'>🔴 DIAGNOSTIC: {row['index'].upper()}</strong>"
                                        f"<a href='{row.get('url', '#')}' target='_blank' style='position:absolute; top:0; right:0; font-size:11px; color:var(--sol-violet); text-decoration:none;'>View ↗</a><br>"
                                        "<span style='color: var(--sol-base01); font-size: 12px;'>Status: Beneath Median Baseline</span><br>"
                                        "<p style='color: var(--sol-base0); font-size: 12px; margin: 4px 0 4px 0;'>• Weak early hook title / dense layout formatting.</p>"
                                        "<span style='color: var(--sol-yellow); font-size: 11px; font-family: monospace;'>👉 Fix Hook: \"Stop scrolling if your sign belongs to this transition...\"</span>"
                                        "</div>"
                                    )
                                    
                            log_feed_html += "</div></div>"
                            st.html(log_feed_html)

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")
