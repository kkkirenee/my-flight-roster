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

# --- 1. 暴力 CSS 最終加強版 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 暴力去藍：連點點（Dot）都要變粉紅 */
    .fc-event, .fc-event-main, .fc-daygrid-event, .fc-daygrid-event-dot {{
        background-color: {user_color} !important;
        border: none !important;
        background: {user_color} !important;
        color: white !important;
    }}

    /* 🚀 核心修正：取消點點模式，強制變成整條顯示，字體 40px */
    .fc-daygrid-event {{
        display: block !important;
        padding: 5px !important;
    }}
    
    .fc-event-title, .fc-event-main {{
        font-size: 40px !important; 
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
        line-height: 1 !important;
    }}

    /* 撐開格子高度，防止大字重疊 */
    .fc-daygrid-event-harness {{ min-height: 70px !important; margin-bottom: 5px !important; }}
    .fc-daygrid-day-frame {{ min-height: 130px !important; }}
    
    /* 姓名按鈕縮小 */
    div.stButton > button {{ font-size: 0.9rem !important; height: 2.5em !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
calendar_events = []
try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 根據 st.session_state.current_user 的名字去讀分頁
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        
        calendar_events.append({
            "title": str(row['班號']),
            "start": clean_date,
            "end": clean_date,
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color,
            "display": "block" # 🚀 強制讓它以長條顯示，不要變成點點
        })
except Exception as e:
    st.sidebar.warning(f"尚未找到 {st.session_state.current_user} 的資料")

# --- 3. 介面呈現 ---
with st.sidebar:
    st.markdown(f"### ✈️ Crew Menu")
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    details_placeholder = st.empty()

st.title(f"💖 {st.session_state.current_user}")

state = calendar(
    events=calendar_events, 
    options={
        "initialDate": today_str,
        "contentHeight": 850,
        "displayEventTime": False,
        "dayMaxEventRows": False, # 🚀 這一行最重要！防止它變成點點或 "+ more"
    }, 
    key=f"cal_{st.session_state.current_user}"
)

# --- 4. 詳情顯示 ---
if state.get("eventClick"):
    t = state["eventClick"]["event"]["title"].strip()
    match = flight_db[flight_db['班號'] == t]
    if not match.empty:
        r = match.iloc[0]
        with details_placeholder.container():
            st.markdown(f"""
                <div style='background:#1F1F1F; padding:15px; border-radius:12px; border:2px solid {user_color};'>
                    <h2 style='color:{user_color}; margin:0;'>CI {t}</h2>
                    <p style='font-size:1.4rem; font-weight:700; margin:10px 0;'>📍 {r['目的地']}</p>
                </div>
            """, unsafe_allow_html=True)
