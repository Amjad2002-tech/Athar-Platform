import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

st.set_page_config(page_title="ATHAR Cloud Platform", page_icon="☁️", layout="wide")

# --- SECRETS ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = init_connection()

# --- AUTH ---
if 'user' not in st.session_state: st.session_state.user = None

def login(email, password):
    try:
        response = supabase.table('app_users').select("*").eq('email', email).eq('password', password).execute()
        if len(response.data) > 0:
            st.session_state.user = response.data[0]
            st.rerun()
        else: st.error("Wrong email/pass")
    except: st.error("Login Failed")

def logout():
    st.session_state.user = None
    st.rerun()

if not st.session_state.user:
    st.title("🔒 ATHAR Login")
    c1, c2 = st.columns([1,2])
    with c1:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"): login(e, p)
    st.stop()

# --- DASHBOARD ---
user = st.session_state.user
company_id = user['company_id']

# Header
c_title, c_control, c_logout = st.columns([5, 2, 1])
with c_title: st.title(f"🚀 ATHAR | {user['name']}")

# --- FIX: ROBUST BUTTON LOGIC ---
with c_control:
    # 1. Get Status (Safe Mode)
    current_status = "UNKNOWN"
    try:
        res = supabase.table('device_control').select('status').eq('location_id', 1).execute()
        if res.data: current_status = res.data[0]['status']
    except: pass

    # 2. Render Button based on status
    if current_status == "START":
        # System is ON -> Show STOP button
        if st.button("⛔ STOP CAM", use_container_width=True, key="stop_btn"):
            supabase.table('device_control').update({'status': 'STOP'}).eq('location_id', 1).execute()
            st.rerun() # Force refresh immediately
    else:
        # System is OFF -> Show START button
        if st.button("▶️ START CAM", use_container_width=True, key="start_btn"):
            supabase.table('device_control').update({'status': 'START'}).eq('location_id', 1).execute()
            st.rerun() # Force refresh immediately

with c_logout:
    if st.button("Log Out"): logout()

st.markdown("---")

# Data Fetching
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

if st.button("🔄 Refresh Data"): st.rerun()

df = get_data()

if df.empty:
    st.info("No Data Yet.")
else:
    staff = df[df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]
    guests = df[~df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Visitors", len(guests))
    k2.metric("Staff Interactions", len(staff))
    avg = guests['duration'].mean() if not guests.empty else 0
    k3.metric("Avg Dwell Time", f"{avg:.1f}s")
    top = guests['zone_name'].mode()[0] if not guests.empty else "N/A"
    k4.metric("Hot Zone", top)

    t1, t2 = st.tabs(["Traffic", "Staff"])
    with t1:
        c1, c2 = st.columns(2)
        if not guests.empty:
            c1.plotly_chart(px.bar(guests['zone_name'].value_counts(), title="Traffic by Zone", color_discrete_sequence=['#00CC96']), use_container_width=True)
            c2.dataframe(guests[['timestamp', 'visitor_type', 'zone_name', 'duration']].head(10), use_container_width=True)
    with t2:
        if not staff.empty:
            st.dataframe(staff[['timestamp', 'staff_name', 'zone_name', 'response_time']].head(10), use_container_width=True)

# Admin
with st.expander("🚨 Admin Danger Zone"):
    code = st.text_input("Security Code", type="password")
    if st.button("Clear All Data"):
        if code == "2030":
            try:
                locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
                ids = [l['id'] for l in locs.data]
                if ids: supabase.table('traffic_logs').delete().in_('location_id', ids).execute()
                st.success("Wiped!")
                time.sleep(1)
                st.rerun()
            except: st.error("Error")
