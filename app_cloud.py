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
    st.error("⚠️ Secrets not found! Check .streamlit/secrets.toml")
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
        st.error("⚠️ Connection Failed")
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
        if st.button("Log In", use_container_width=True): login(email, password)
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
    st.caption(f"Role: {user.get('role', 'Manager')}")
    st.markdown("---")
    page = st.radio("Navigate", ["🏠 Home & Vision", "📊 Live Dashboard", "⚙️ System Control"])
    st.markdown("---")
    if st.button("🚪 Log Out", use_container_width=True): logout()

# ==========================================
# PAGE 1: HOME
# ==========================================
if page == "🏠 Home & Vision":
    st.title("🚀 ATHAR Insight")
    st.markdown("### *Transforming Showrooms into Smart Data Hubs*")
    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("💡 The Concept")
        st.write("""
        **ATHAR Insight** solves the biggest blind spot in physical retail: **"What happens before the sale?"**
        Using advanced AI, we track:
        * **Customer Journey:** Identifies which zones attract the most attention.
        * **True Dwell Time:** Measures actual engagement, not just footfall.
        * **Staff Performance:** Audits response times automatically.
        """)
    with c2:
        st.warning("⚠️ Traditional vs. ATHAR")
        st.dataframe(pd.DataFrame({
            "Traditional": ["Head count only", "Hardware sensors", "No Staff filter"],
            "ATHAR AI": ["Behavior Analytics", "Computer Vision", "Staff Filtering"]
        }), hide_index=True)

# ==========================================
# PAGE 2: DASHBOARD (UPDATED WITH MORE CHARTS) 📊
# ==========================================
elif page == "📊 Live Dashboard":
    st.title("📊 Operational Dashboard")
    if st.button("🔄 Sync Data"): st.rerun()

    def get_data():
        try:
            locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
            loc_ids = [l['id'] for l in locs.data]
            if not loc_ids: return pd.DataFrame()
            logs = supabase.table('traffic_logs').select('*').in_('location_id', loc_ids).order('timestamp', desc=True).limit(1000).execute()
            df = pd.DataFrame(logs.data)
            if not df.empty: df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except: return pd.DataFrame()

    df = get_data()

    if df.empty:
        st.info("Waiting for live data feed...")
    else:
        # Data Splitting
        staff_df = df[df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]
        guest_df = df[~df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]

        # --- TOP METRICS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🛒 Unique Visitors", len(guest_df))
        m2.metric("👔 Staff Actions", len(staff_df))
        avg_dwell = guest_df['duration'].mean() if not guest_df.empty else 0
        m3.metric("⏱️ Avg Engagement", f"{avg_dwell:.1f} sec")
        hot_zone = guest_df['zone_name'].mode()[0] if not guest_df.empty else "N/A"
        m4.metric("🔥 Hot Zone", hot_zone)

        st.markdown("---")

        # --- TABS FOR CHARTS ---
        tab1, tab2 = st.tabs(["📈 Traffic Analysis", "👔 Staff Audit"])
        
        with tab1:
            # Row 1: Zone Interest + Engagement Distribution
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📍 Interest by Zone")
                if not guest_df.empty:
                    fig = px.bar(guest_df['zone_name'].value_counts(), orientation='h', color_discrete_sequence=['#00CC96'])
                    st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.subheader("⏳ Engagement Time (Seconds)")
                if not guest_df.empty:
                    # رسم بياني يوضح توزيع الأوقات (هل الناس يطولون ولا يمشون بسرعة؟)
                    fig_hist = px.histogram(guest_df, x="duration", nbins=15, title="How long do they stay?", color_discrete_sequence=['#FF4B4B'])
                    st.plotly_chart(fig_hist, use_container_width=True)

            # Row 2: Peak Hours Analysis (NEW)
            st.subheader("🌊 Peak Hours (Activity over Time)")
            if not guest_df.empty:
                # استخراج الساعة من الوقت
                guest_df['Hour'] = guest_df['timestamp'].dt.hour
                hourly_counts = guest_df.groupby('Hour').size().reset_index(name='Visitors')
                fig_line = px.area(hourly_counts, x='Hour', y='Visitors', markers=True, color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig_line, use_container_width=True)

            # Row 3: Data Table
            st.subheader("📋 Recent Visitor Log")
            st.dataframe(guest_df[['timestamp', 'visitor_type', 'zone_name', 'duration']].head(10), use_container_width=True)

        with tab2:
            # Row 1: Response Speed + Most Active Staff
            c1, c2 = st.columns(2)
            if not staff_df.empty:
                with c1:
                    st.subheader("⚡ Response Speed")
                    fig2 = px.box(staff_df, x='staff_name', y='response_time', color='staff_name')
                    st.plotly_chart(fig2, use_container_width=True)
                with c2:
                    st.subheader("🏆 Most Active Staff")
                    # رسم بياني للموظف الأكثر عملاً
                    staff_counts = staff_df['staff_name'].value_counts().reset_index()
                    staff_counts.columns = ['Name', 'Interactions']
                    fig_bar_staff = px.bar(staff_counts, x='Name', y='Interactions', color='Interactions', color_continuous_scale='Blues')
                    st.plotly_chart(fig_bar_staff, use_container_width=True)
                
                # Row 2: Logs
                st.subheader("📋 Staff Interaction Log")
                st.dataframe(staff_df[['timestamp', 'staff_name', 'zone_name', 'response_time']].head(10), use_container_width=True)
            else:
                st.info("No staff interactions recorded yet.")

# ==========================================
# PAGE 3: SYSTEM CONTROL
# ==========================================
elif page == "⚙️ System Control":
    st.title("⚙️ Admin Control Center")
    st.markdown("### 📡 Remote Camera Access")
    
    c_ctrl, c_info = st.columns([1, 2])
    with c_ctrl:
        current_status = "UNKNOWN"
        try:
            res = supabase.table('device_control').select('status').eq('location_id', 1).execute()
            if res.data: current_status = res.data[0]['status']
        except: pass

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
    with c_info:
        st.info("Instructions: Ensure the on-site PC is running the main.py script.")

    st.markdown("---")
    with st.expander("🚨 Danger Zone"):
        pin = st.text_input("Admin PIN", type="password")
        if st.button("Wipe Data"):
            if pin == "2030":
                try:
                    locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
                    ids = [l['id'] for l in locs.data]
                    if ids:
                        supabase.table('traffic_logs').delete().in_('location_id', ids).execute()
                        st.success("Cleared!")
                        time.sleep(1); st.rerun()
                except: st.error("Failed.")
            else: st.error("Wrong PIN")
