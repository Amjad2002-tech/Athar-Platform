import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ATHAR Insight | Retail AI", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SECURE CONNECTION ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets not found! Please check your .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = init_connection()

# --- 3. AUTHENTICATION LOGIC ---
if 'user' not in st.session_state: st.session_state.user = None

def login(email, password):
    if not supabase:
        st.error("⚠️ Database Connection Failed")
        return
        
    try:
        response = supabase.table('app_users').select("*").eq('email', email).eq('password', password).execute()
        if len(response.data) > 0:
            st.session_state.user = response.data[0]
            st.rerun()
        else: st.error("❌ Invalid Credentials")
    except Exception as e: st.error(f"⚠️ Error: {e}")

def logout():
    st.session_state.user = None
    st.rerun()

# --- 4. LOGIN SCREEN ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚀 ATHAR Insight")
        st.markdown("##### The Future of In-Store Analytics")
        st.info("Please sign in to access the management console.")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Log In", use_container_width=True):
            login(email, password)
    st.stop()

# ==========================================
# 🌟 MAIN APPLICATION
# ==========================================
user = st.session_state.user
company_id = user.get('company_id', 1)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=50)
    st.title(f"Welcome, {user.get('name', 'User')}")
    
    user_role = user.get('role', 'Manager') 
    st.caption(f"Role: {user_role}")
    
    st.markdown("---")
    page = st.radio("Navigate", ["🏠 Home & Vision", "📊 Live Dashboard", "⚙️ System Control"])
    st.markdown("---")
    if st.button("🚪 Log Out", use_container_width=True):
        logout()

# ==========================================
# PAGE 1: HOME & VISION
# ==========================================
if page == "🏠 Home & Vision":
    st.title("🚀 ATHAR Insight")
    st.markdown("### *Transforming Showrooms into Smart Data Hubs*")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("💡 The Concept")
        st.write("""
        **ATHAR Insight** solves the biggest blind spot in physical retail: **"What happens before the sale?"**
        While e-commerce tracks every click, physical showrooms have been flying blind. Not anymore.
        Our AI-powered Computer Vision system provides:
        * **Customer Journey Tracking:** Identifies which zones attract the most attention.
        * **True Dwell Time:** Measures actual engagement, not just footfall.
        * **Staff Performance:** Audits response times automatically.
        """)
    with col2:
        st.warning("⚠️ Traditional Counters vs. ATHAR")
        st.dataframe(pd.DataFrame({
            "Traditional": ["Counts heads only", "Dumb sensors", "No Staff filtering", "Offline Data"],
            "ATHAR AI": ["Tracks Behavior", "Computer Vision", "Filters Staff", "Real-time Cloud"]
        }), hide_index=True)

# ==========================================
# PAGE 2: DASHBOARD (FIXED & INTERACTIVE)
# ==========================================
elif page == "📊 Live Dashboard":
    st.title("📊 Operational Dashboard")
    
    if st.button("🔄 Sync Data"): st.rerun()

    def get_data():
        try:
            locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
            loc_ids = [l['id'] for l in locs.data]
            if not loc_ids: return pd.DataFrame()
            logs = supabase.table('traffic_logs').select('*').in_('location_id', loc_ids).order('timestamp', desc=True).limit(500).execute()
            df = pd.DataFrame(logs.data)
            if not df.empty: df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except: return pd.DataFrame()

    df = get_data()

    if df.empty:
        st.info("Waiting for live data feed...")
    else:
        staff_df = df[df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]
        guest_df = df[~df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🛒 Unique Visitors", len(guest_df))
        m2.metric("👔 Staff Actions", len(staff_df))
        avg_dwell = guest_df['duration'].mean() if not guest_df.empty else 0
        m3.metric("⏱️ Avg Engagement", f"{avg_dwell:.1f} sec")
        hot_zone = guest_df['zone_name'].mode()[0] if not guest_df.empty else "N/A"
        m4.metric("🔥 Hot Zone", hot_zone)

        st.markdown("---")

        tab1, tab2 = st.tabs(["📈 Traffic Analysis", "👔 Staff Audit"])
        
        with tab1:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("📍 Interest by Zone (
