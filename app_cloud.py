import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- CONFIG ---
st.set_page_config(page_title="ATHAR Cloud Platform", page_icon="☁️", layout="wide")

# ✅ الكود النظيف (يقرأ من Secrets فقط)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Connect to DB
@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase = init_connection()

# --- AUTHENTICATION LOGIC ---
if 'user' not in st.session_state:
    st.session_state.user = None

def login(email, password):
    try:
        response = supabase.table('app_users').select("*").eq('email', email).eq('password', password).execute()
        if len(response.data) > 0:
            st.session_state.user = response.data[0]
            st.success(f"Welcome back, {response.data[0]['name']}!")
            st.rerun()
        else:
            st.error("Incorrect email or password")
    except Exception as e:
        st.error(f"Login Error: {e}")

def logout():
    st.session_state.user = None
    st.rerun()

# --- LOGIN SCREEN ---
if not st.session_state.user:
    st.title("🔒 ATHAR Portal Login")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Sign In"):
            login(email, password)
    
    st.stop()

# ==========================================
# MAIN DASHBOARD (HEADER & CONTROLS)
# ==========================================
user = st.session_state.user
company_id = user['company_id']

# --- تصميم الهيدر الجديد (أزرار في الأعلى يمين) ---
# قسمنا الشاشة: 5 أجزاء للعنوان | جزئين للتحكم | جزء للخروج
c_title, c_control, c_logout = st.columns([5, 2, 1])

with c_title:
    st.title(f"🚀 ATHAR | {user['name']}")

# --- REMOTE CONTROL (TOP RIGHT) ---
with c_control:
    try:
        # 1. جلب الحالة الحالية
        control_data = supabase.table('device_control').select('status').eq('location_id', 1).execute()
        if control_data.data:
            current_status = control_data.data[0]['status']
            
            # عرض الزر بناءً على الحالة
            if current_status == "START":
                # إذا كان شغال -> اعرض زر إيقاف أحمر
                if st.button("⛔ STOP CAM", use_container_width=True):
                    supabase.table('device_control').update({'status': 'STOP'}).eq('location_id', 1).execute()
                    st.rerun()
            else:
                # إذا كان طافي -> اعرض زر تشغيل أخضر
                if st.button("▶️ START CAM", use_container_width=True):
                    supabase.table('device_control').update({'status': 'START'}).eq('location_id', 1).execute()
                    st.rerun()
            
            # مؤشر حالة صغير
            if current_status == "START":
                st.caption("🟢 System is Live")
            else:
                st.caption("🔴 System is Offline")
    except:
        st.warning("Connecting...")

# --- LOGOUT BUTTON (FAR RIGHT) ---
with c_logout:
    if st.button("Log Out", use_container_width=True):
        logout()

st.markdown("---")

# 1. FETCH DATA
def get_company_data():
    try:
        locs = supabase.table('locations').select('id, name').eq('company_id', company_id).execute()
        loc_ids = [l['id'] for l in locs.data]
        
        if not loc_ids: return pd.DataFrame()
        
        logs = supabase.table('traffic_logs').select('*').in_('location_id', loc_ids).order('timestamp', desc=True).limit(500).execute()
        
        df = pd.DataFrame(logs.data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

if st.button("🔄 Refresh Data"):
    st.rerun()

df = get_company_data()

if df.empty:
    st.info("No data available for your company yet.")
else:
    # --- DATA PROCESSING ---
    staff_interactions = df[df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]
    guests = df[~df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]

    # --- KPIs ---
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("🛒 Total Visitors", len(guests))
    k2.metric("👔 Staff Interactions", len(staff_interactions))
    
    avg_time = guests['duration'].mean() if not guests.empty else 0
    k3.metric("⏱️ Avg. Dwell Time", f"{avg_time:.1f} s")
    
    top_zone = guests['zone_name'].mode()[0] if not guests.empty else "N/A"
    k4.metric("🔥 Hot Zone", top_zone)

    st.markdown("---")

    # --- CHARTS ---
    tab1, tab2 = st.tabs(["📊 Traffic Analysis", "👔 Staff Audit"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Traffic by Zone")
            if not guests.empty:
                fig_bar = px.bar(guests['zone_name'].value_counts(), 
                                 title="Where do customers stop?", 
                                 color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No guest data.")
                
        with c2:
            st.subheader("Recent Activity (Live Feed)")
            st.dataframe(guests[['timestamp', 'visitor_type', 'zone_name', 'duration']].head(10), use_container_width=True)

    with tab2:
        if not staff_interactions.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Response Speed")
                fig_perf = px.box(staff_interactions, x='staff_name', y='response_time', 
                                  title="Response Time Range", color='staff_name')
                st.plotly_chart(fig_perf, use_container_width=True)
            with c2:
                st.subheader("Leaderboard")
                if 'staff_name' in staff_interactions.columns and 'response_time' in staff_interactions.columns:
                    leaderboard = staff_interactions.groupby('staff_name')['response_time'].mean().reset_index().sort_values('response_time')
                    st.dataframe(leaderboard, use_container_width=True)
        else:
            st.info("No staff interactions recorded yet.")

# --- ADMIN ZONE ---
st.markdown("---")
with st.expander("🚨 Admin Settings (Danger Zone)"):
    st.write("⚠️ **Warning:** This action cannot be undone.")
    secret_code = st.text_input("Enter Security Code", type="password")
    
    if st.button("🗑️ Clear All History"):
        if secret_code == "2030":
            try:
                locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
                loc_ids = [l['id'] for l in locs.data]
                if loc_ids:
                    supabase.table('traffic_logs').delete().in_('location_id', loc_ids).execute()
                    st.success("✅ Wiped!")
                    time.sleep(1)
                    st.rerun()
            except: st.error("Error clearing data.")
        else:
            st.error("❌ Wrong Code")
