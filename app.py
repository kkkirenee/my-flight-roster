import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL Crew Hub", page_icon="✈️", layout="wide")
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 核心大字 CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 班表格子底色 */
    .fc-event, .fc-event-main, .fc-daygrid-event {{
        background-color: {user_color} !important;
        border: none !important;
    }}

    /* 🚀 核心：白色班號字體，超級大、超級粗 */
    .fc-event-title {{
        font-size: 3.0rem !important; 
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
        display: block !important;
        padding: 5px 0 !important;
    }}

    /* 確保格子撐得開 */
    .fc-daygrid-event-harness {{ min-height: 65px !important; }}
    
    /* 詳情卡片 */
    .detail-card {{
        background: #1F1F1F;
        padding: 15px;
        border-radius: 12px;
        border: 2px solid {user_color};
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
calendar_events = []
flight_db = pd.DataFrame()
try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        calendar_events.append({"title": str(row['班號']), "start": clean_date, "end": clean_date, "allDay": True})
except:
    st.sidebar.warning(f"請確認 Excel 分頁名稱是否為 {st.session_state.current_user}")

# --- 3. 側邊欄 (SCHEDULE) ---
with st.sidebar:
    # 🚀 改名為 SCHEDULE
    st.markdown(f"<h1 style='text-align:center; color:{user_color};'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    details_container = st.empty()

# --- 4. 主畫面 ---
st.title(f"💖 {st.session_state.current_user}")

cal_options = {
    "initialDate": today_str,
    "contentHeight": 700,
    "displayEventTime": False,
    "dayMaxEvents": False
}

state = calendar(events=calendar_events, options=cal_options, key=f"cal_{st.session_state.current_user}")

# --- 5. 點擊詳情 ---
if state.get("eventClick"):
    fno = state["eventClick"]["event"]["title"].strip()
    if not flight_db.empty:
        match = flight_db[flight_db['班號'] == fno]
        if not match.empty:
            r = match.iloc[0]
            details_container.markdown(f"""
                <div class="detail-card">
                    <h2 style='color:{user_color};'>CI {fno}</h2>
                    <p style='font-size:1.3rem; font-weight:800;'>📍 {r['目的地']}</p>
                </div>
            """, unsafe_allow_html=True)
