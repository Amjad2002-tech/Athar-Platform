import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ATHAR Insight | AI Retail Analytics", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SECRETS CONNECTION ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets not found. Please configure .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = init_connection()

# --- AUTHENTICATION STATE ---
if 'user' not in st.session_state: st.session_state.user = None

# --- LOGIN FUNCTIONS ---
def login(email, password):
    try:
        response = supabase.table('app_users').select("*").eq('email', email).eq('password', password).execute()
        if len(response.data) > 0:
            st.session_state.user = response.data[0]
            st.rerun()
        else: st.error("❌ Incorrect email or password")
    except: st.error("⚠️ Connection Error")

def logout():
    st.session_state.user = None
    st.rerun()

# ==========================================
# 🔒 LOGIN SCREEN (The Gate)
# ==========================================
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚀 ATHAR Insight")
        st.markdown("### Intelligent Retail Analytics Platform")
        st.info("Please sign in to access the secure dashboard.")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True): 
            login(email, password)
    st.stop()

# ==========================================
# 📂 APP NAVIGATION (SIDEBAR)
# ==========================================
user = st.session_state.user
company_id = user['company_id']

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50) # شعار افتراضي
    st.title(f"Welcome, {user['name']}")
    st.markdown(f"**Role:** {user['role']}")
    st.markdown("---")
    
    # القائمة الجانبية للتنقل
    selected_page = st.radio(
        "Navigate", 
        ["🏠 Home", "📊 Dashboard", "⚙️ Settings & Control"],
        index=0
    )
    
    st.markdown("---")
    if st.button("🚪 Log Out", use_container_width=True):
        logout()

# ==========================================
# 🏠 PAGE 1: HOME (About & Vision)
# ==========================================
if selected_page == "🏠 Home":
    # Hero Section
    st.title("🚀 ATHAR Insight")
    st.markdown("### *Redefining Customer Experience with AI Vision*")
    st.markdown("---")

    # The Idea
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("💡 The Idea")
        st.write("""
        **ATHAR Insight** is a cutting-edge Computer Vision solution designed for automotive showrooms and high-end retail. 
        Unlike traditional counters, ATHAR doesn't just count people; it understands **behavior**.
        
        Using advanced AI, we track:
        * **Customer Journey:** Where do they go? Which car attracts them most?
        * **Staff Performance:** How fast do employees react to new customers?
        * **True Engagement:** Differentiating between a 'glance' and 'deep interest'.
        """)
    
    with c2:
        st.info("🎯 **Our Mission:** To transform raw video data into actionable business intelligence, helping managers make data-driven decisions in real-time.")

    st.markdown("---")

    # Key Features
    st.subheader("✨ Key Features")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("#### 👁️ AI Tracking")
        st.caption("Recognizes customers vs. staff and tracks movement seamlessly.")
    with f2:
        st.markdown("#### ⏱️ Smart Timing")
        st.caption("Calculates precise dwell time and staff response speed.")
    with f3:
        st.markdown("#### ☁️ Cloud Sync")
        st.caption("Real-time data upload to a secure cloud dashboard.")

# ==========================================
# 📊 PAGE 2: DASHBOARD (The Data)
# ==========================================
elif selected_page == "📊 Dashboard":
    st.title("📊 Live Operations Dashboard")
    
    # زر التحديث
    if st.button("🔄 Refresh Data"): st.rerun()

    # جلب البيانات
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
        st.warning("No data available yet. Start the camera system.")
    else:
        # معالجة البيانات
        staff = df[df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]
        guests = df[~df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🛒 Total Visitors", len(guests))
        k2.metric("👔 Staff Interactions", len(staff))
        avg = guests['duration'].mean() if not guests.empty else 0
        k3.metric("⏱️ Avg. Dwell Time", f"{avg:.1f}s")
        top = guests['zone_name'].mode()[0] if not guests.empty else "N/A"
        k4.metric("🔥 Hot Zone", top)

        st.markdown("---")

        # Charts
        tab1, tab2 = st.tabs(["📈 Traffic Analysis", "👔 Staff Performance"])
        
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Traffic by Zone")
                if not guests.empty:
                    fig = px.bar(guests['zone_name'].value_counts(), color_discrete_sequence=['#00CC96'])
                    st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.subheader("Live Activity Log")
                st.dataframe(guests[['timestamp', 'visitor_type', 'zone_name', 'duration']].head(10), use_container_width=True)

        with tab2:
            if not staff.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Response Times")
                    fig2 = px.box(staff, x='staff_name', y='response_time', color='staff_name')
                    st.plotly_chart(fig2, use_container_width=True)
                with c2:
                    st.subheader("Interaction Logs")
                    st.dataframe(staff[['timestamp', 'staff_name', 'zone_name', 'response_time']].head(10), use_container_width=True)
            else:
                st.info("No staff interactions recorded yet.")

# ==========================================
# ⚙️ PAGE 3: SETTINGS & CONTROL (Admin)
# ==========================================
elif selected_page == "⚙️ Settings & Control":
    st.title("⚙️ System Control Center")
    
    # 1. Camera Control
    st.subheader("📡 Camera Remote Control")
    c_ctrl, c_info = st.columns([1, 2])
    
    with c_ctrl:
        current_status = "UNKNOWN"
        try:
            res = supabase.table('device_control').select('status').eq('location_id', 1).execute()
            if res.data: current_status = res.data[0]['status']
        except: pass

        if current_status == "START":
            st.success("🟢 System is **ONLINE**")
            if st.button("⛔ STOP CAMERA", type="primary", use_container_width=True):
                supabase.table('device_control').update({'status': 'STOP'}).eq('location_id', 1).execute()
                st.rerun()
        else:
            st.error("🔴 System is **OFFLINE**")
            if st.button("▶️ START CAMERA", type="primary", use_container_width=True):
                supabase.table('device_control').update({'status': 'START'}).eq('location_id', 1).execute()
                st.rerun()

    with c_info:
        st.info("Use this switch to remotely turn the showroom camera ON or OFF. Changes reflect within seconds.")

    st.markdown("---")

    # 2. Database Management
    st.subheader("🗑️ Data Management")
    with st.expander("🚨 Danger Zone (Clear Data)"):
        st.warning("This action will permanently delete all visitor and staff logs.")
        secret_code = st.text_input("Enter Admin PIN to confirm:", type="password")
        
        if st.button("Confirm Wipe"):
            if secret_code == "2030":
                try:
                    locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
                    ids = [l['id'] for l in locs.data]
                    if ids: 
                        supabase.table('traffic_logs').delete().in_('location_id', ids).execute()
                        st.success("✅ Database Wiped Successfully!")
                        time.sleep(1)
                        st.rerun()
                except: st.error("Failed to clear data.")
            else:
                st.error("❌ Incorrect PIN.")
