import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- CONFIG ---
st.set_page_config(page_title="ATHAR Cloud Platform", page_icon="☁️", layout="wide")

# ⚠️⚠️⚠️ ضـــــــــع مــــفـــــاتـــــيـــــحــــك الـــصـــحـــيـــحـــة هـــــــــنـــــــــا ⚠️⚠️⚠️
SUPABASE_URL = "https://ygfjtmotowdsfkohxfmw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnZmp0bW90b3dkc2Zrb2h4Zm13Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgyNTk1NzMsImV4cCI6MjA4MzgzNTU3M30.wx2wc3rJ7VZ1V-ZIea5pBlX60vybbItxBiTYBl1R45c"

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
        email = st.text_input("Email", "admin@Audi.com")
        password = st.text_input("Password", type="password")
        if st.button("Sign In"):
            login(email, password)
    
    st.stop()

# ==========================================
# MAIN DASHBOARD (ONLY FOR LOGGED IN USERS)
# ==========================================
user = st.session_state.user
company_id = user['company_id']

# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.title(f"🚀 ATHAR | {user['name']} Dashboard")
with c2:
    if st.button("Log Out"):
        logout()

st.markdown("---")

# 1. FETCH DATA (FOR THIS COMPANY ONLY)
def get_company_data():
    try:
        # Get Locations
        locs = supabase.table('locations').select('id, name').eq('company_id', company_id).execute()
        loc_ids = [l['id'] for l in locs.data]
        
        if not loc_ids: return pd.DataFrame()
        
        # Get Logs
        logs = supabase.table('traffic_logs').select('*').in_('location_id', loc_ids).order('timestamp', desc=True).limit(500).execute()
        
        df = pd.DataFrame(logs.data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Convert to Local Time (Optional)
            # df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Riyadh') 
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
    # نفصل البيانات: زوار vs تفاعل موظفين
    guests = df[df['visitor_type'] == 'Guest']
    
    # تصحيح: قد يكون الاسم Staff_Interaction أو interaction
    # نبحث عن أي شيء فيه كلمة Staff
    staff_interactions = df[df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]

    # --- KPIs ---
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("🛒 Total Visitors", len(guests))
    k2.metric("👔 Staff Interactions", len(staff_interactions))
    
    avg_time = guests['duration'].mean() if not guests.empty else 0
    k3.metric("⏱️ Avg. Dwell Time", f"{avg_time:.1f} s")
    
    # Top Zone
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
        with c2:
            st.subheader("Recent Activity")
            st.dataframe(guests[['timestamp', 'zone_name', 'duration']].head(10), use_container_width=True)

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
            st.info("No staff interactions recorded yet. Go be a boss!")