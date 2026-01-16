import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- CONFIG ---
st.set_page_config(
    page_title="ATHAR Insight", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONNECT ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets not found!")
    st.stop()

@st.cache_resource
def init_connection():
    try: return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = init_connection()

# --- AUTH ---
if 'user' not in st.session_state: st.session_state.user = None

def login(email, password):
    if not supabase: return
    try:
        response = supabase.table('app_users').select("*").eq('email', email).eq('password', password).execute()
        if len(response.data) > 0:
            st.session_state.user = response.data[0]
            st.rerun()
        else: st.error("❌ Invalid")
    except: st.error("⚠️ Error")

def logout():
    st.session_state.user = None
    st.rerun()

if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚀 ATHAR Insight")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Log In", use_container_width=True): login(email, password)
    st.stop()

# ==========================================
# APP
# ==========================================
user = st.session_state.user
company_id = user.get('company_id', 1)

with st.sidebar:
    # ✅ LOGO CHANGED TO CAMERA
    st.image("https://cdn-icons-png.flaticon.com/512/3687/3687412.png", width=60)
    st.title(f"Welcome, {user.get('name', 'User')}")
    st.caption(f"Role: {user.get('role', 'Manager')}")
    st.markdown("---")
    page = st.radio("Navigate", ["🏠 Home", "📊 Dashboard", "⚙️ Control"])
    st.markdown("---")
    if st.button("🚪 Log Out", use_container_width=True): logout()

if page == "🏠 Home":
    st.title("🚀 ATHAR Insight")
    st.write("Welcome to the future of retail analytics.")

elif page == "📊 Dashboard":
    st.title("📊 Dashboard")
    if st.button("🔄 Sync"): st.rerun()

    def get_data():
        try:
            locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
            ids = [l['id'] for l in locs.data]
            if not ids: return pd.DataFrame()
            logs = supabase.table('traffic_logs').select('*').in_('location_id', ids).order('timestamp', desc=True).limit(1000).execute()
            df = pd.DataFrame(logs.data)
            if not df.empty: df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except: return pd.DataFrame()

    df = get_data()

    if df.empty:
        st.info("No data.")
    else:
        staff_df = df[df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]
        guest_df = df[~df['visitor_type'].astype(str).str.contains('Staff', case=False, na=False)]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Visitors", len(guest_df))
        m2.metric("Staff Actions", len(staff_df))
        m3.metric("Avg Engagement", f"{guest_df['duration'].mean():.1f}s" if not guest_df.empty else "0s")
        m4.metric("Hot Zone", guest_df['zone_name'].mode()[0] if not guest_df.empty else "N/A")

        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Traffic", "Staff"])
        
        with tab1:
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.subheader("📍 Interest by Zone")
                if not guest_df.empty:
                    chart_data = guest_df['zone_name'].value_counts().reset_index()
                    chart_data.columns = ['Zone', 'Visitors']
                    fig = px.bar(chart_data, x='Zone', y='Visitors', color_discrete_sequence=['#00CC96'])
                    # ✅ CLICKABLE CHART
                    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
            
            with c2:
                # ✅ DRILL DOWN LOGIC (NO CLEAR BUTTON)
                if 'selection' in event and event.selection and len(event.selection['points']) > 0:
                    sel = event.selection['points'][0]['x']
                    st.subheader(f"🔎 Details: {sel}")
                    # Click outside chart to clear filter (Implicit)
                    st.dataframe(guest_df[guest_df['zone_name'] == sel][['timestamp', 'visitor_type', 'duration']], use_container_width=True, hide_index=True)
                else:
                    st.subheader("📋 Recent")
                    st.dataframe(guest_df[['timestamp', 'visitor_type', 'zone_name', 'duration']].head(10), use_container_width=True, hide_index=True)

            st.markdown("---")
            
            c3, c4 = st.columns([1.5, 1])
            with c3:
                st.subheader("⏳ Engagement Time")
                if not guest_df.empty:
                    # ✅ CLICKABLE HISTOGRAM
                    fig_h = px.histogram(guest_df, x="duration", nbins=15, title="Distribution", color_discrete_sequence=['#FF4B4B'])
                    event_h = st.plotly_chart(fig_h, use_container_width=True, on_select="rerun")
            
            with c4:
                # ✅ DRILL DOWN FOR HISTOGRAM
                if 'selection' in event_h and event_h.selection and len(event_h.selection['point_indices']) > 0:
                    st.subheader("🔎 Filtered Visitors")
                    indices = event_h.selection['point_indices']
                    st.dataframe(guest_df.iloc[indices][['timestamp', 'visitor_type', 'duration']], use_container_width=True, hide_index=True)
                else:
                    st.subheader("📋 Details")
                    st.dataframe(guest_df[['timestamp', 'visitor_type', 'duration']].head(10), use_container_width=True, hide_index=True)

        with tab2:
            st.dataframe(staff_df)

elif page == "⚙️ Control":
    st.title("Control")
    c1, c2 = st.columns([1,2])
    with c1:
        st.write("Camera Control")
        curr = "UNKNOWN"
        try:
            res = supabase.table('device_control').select('status').eq('location_id', 1).execute()
            if res.data: curr = res.data[0]['status']
        except: pass
        
        if curr == "START":
            if st.button("⛔ STOP", type="primary", use_container_width=True):
                supabase.table('device_control').update({'status': 'STOP'}).eq('location_id', 1).execute(); st.rerun()
        else:
            if st.button("▶️ START", type="primary", use_container_width=True):
                supabase.table('device_control').update({'status': 'START'}).eq('location_id', 1).execute(); st.rerun()
    
    with st.expander("Danger Zone"):
        if st.button("Wipe Data"):
            try:
                locs = supabase.table('locations').select('id').eq('company_id', company_id).execute()
                ids = [l['id'] for l in locs.data]
                if ids: supabase.table('traffic_logs').delete().in_('location_id', ids).execute(); st.success("Done")
            except: st.error("Error")
