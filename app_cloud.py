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

# --- 2. SECURE CONNECTION (Fixed) ---
# تم إزالة المسافات الزائدة والعودة للطريقة المباشرة
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

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
        st.error("⚠️ Database connection failed. Check secrets.")
        return

    try:
        response = supabase.table('app_users').select("*").eq('email', email).eq('password', password).execute()
        if len(response.data) > 0:
            st.session_state.user = response.data[0]
            st.rerun()
        else: st.error("❌ Invalid Credentials")
    except Exception as e: 
        st.error(f"⚠️ Error: {e}")

def logout():
    st.session_state.user = None
    st.rerun()

# --- 4. LOGIN SCREEN (THE GATE) ---
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
# 🌟 MAIN APPLICATION (LOGGED IN)
# ==========================================
user = st.session_state.user
company_id = user['company_id']

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=50)
    st.title(f"Welcome, {user['name']}")
    st.caption(f"Role: {user['role']}")
    st.markdown("---")
    
    # القائمة الجانبية
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
        
        st.markdown("#### 🎯 Strategic Value")
        st.success("""
        * **Optimize Layouts:** Move high-margin cars to Hot Zones.
        * **Improve Service:** Alert staff when customers wait too long.
        * **Data-Driven Decisions:** Replace "gut feeling" with hard numbers.
        """)

    with col2:
        st.warning("⚠️ Traditional Counters vs. ATHAR")
        st.dataframe(pd.DataFrame({
            "Traditional": ["Counts heads only", "Dumb sensors", "No Staff filtering", "Offline Data"],
            "ATHAR AI": ["Tracks Behavior", "Computer Vision", "Filters Staff", "Real-time Cloud"]
        }), hide_index=True)

# ==========================================
# PAGE 2: LIVE DASHBOARD
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
                st.subheader("Interest by Zone")
                if not guest_df.empty:
                    fig = px.bar(guest_df['zone_name'].value_counts(), 
                                 orientation='h', 
                                 color_discrete_sequence=['#00CC96'])
                    st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.subheader("Live Feed")
                st.dataframe(guest_df[['timestamp', 'visitor_type', 'zone_name', 'duration']].head(8), use_container_width=True)

        with tab2:
            if not staff_df.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Response Speed Distribution")
                    fig2 = px.box(staff_df, x='staff_name', y='response_time', color='staff_name')
                    st.plotly_chart(fig2, use_container_width=True)
                with c2:
                    st.subheader("Interaction Logs")
                    st.dataframe(staff_df[['timestamp', 'staff_name', 'zone_name', 'response_time']].head(10))
            else:
                st.info("No staff interactions recorded yet.")

# ==========================================
# PAGE 3: SYSTEM CONTROL
# ==========================================
elif page == "⚙️ System Control":
    st.title("⚙️ Admin Control Center")
    
    st.markdown("### 📡 Remote Camera Access")
    
    col_switch, col_status = st.columns([1, 2])
    
    current_status = "UNKNOWN"
    try:
        res = supabase.table('device_control').select('status').eq('location_id', 1).execute()
        if res.data: current_status = res.data[0]['status']
    except: pass

    with col_switch:
        if current_status == "START":
            st.success("Status: **ONLINE** 🟢")
            if st.button("⛔ STOP CAMERA", type="primary", use_container_width=True):
                supabase.table('device_control').update({'status': 'STOP'}).eq('location_id', 1).execute()
                st.rerun()
        else:
            st.error("Status: **OFFLINE** 🔴")
            if st.button("▶️ START CAMERA", type="primary", use_container_width=True):
                supabase.table('device_control').update({'status': 'START'}).eq('location_id', 1).execute()
                st.rerun()
    
    with col_status:
        st.info("Instructions: Ensure the on-site PC is running the main.py script. Use this switch to start/stop the AI engine remotely.")

    st.markdown("---")
    
    st.markdown("### 🗑️ Data Management")
    with st.expander("🚨 Danger Zone (Clear Database)"):
        st.warning("This action cannot be undone.")
        pin = st.text_input("Enter Admin PIN", type="password")
        if st.button("Wipe All Data"):
            if pin == "2030":
                try:
                    locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
                    ids = [l['id'] for l in locs.data]
                    if ids:
                        supabase.table('traffic_logs').delete().in_('location_id', ids).execute()
                        st.success("Database Cleared!")
                        time.sleep(1)
                        st.rerun()
                except: st.error("Failed.")
            else:
                st.error("Incorrect PIN")
