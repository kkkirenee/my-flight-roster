import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

# 設定成員顏色
CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 暴力 CSS：去藍、大字、置中 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 徹底殺掉藍色，換成專屬底色 */
    .fc-event, .fc-event-main, .fc-daygrid-event, .fc-event-title-container {{
        background-color: {user_color} !important;
        border: none !important;
        background: {user_color} !important;
    }}

    /* 🚀 核心：白色班號超級大字 (4.0rem) */
    .fc-event-title {{
        font-size: 4.0rem !important; 
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
        display: block !important;
        line-height: 1.5 !important;
    }}

    /* 撐開格子高度以容納大字 */
    .fc-daygrid-event-harness {{ min-height: 80px !important; }}
    
    /* 側邊欄標題樣式 */
    .side-title {{ font-size: 2rem; font-weight: 900; color: {user_color}; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
calendar_events = []
try:
    # 讀取航班資料 (確保 my_flights.csv 在 GitHub)
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 讀取班表 (分頁連動)
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        calendar_events.append({
            "title": str(row['班號']), 
            "start": clean_date, 
            "end": clean_date, 
            "allDay": True,
            "backgroundColor": user_color, # 雙重去藍保險
            "borderColor": user_color
        })
except Exception as e:
    st.sidebar.warning(f"請確認 Excel 分頁名稱叫: {st.session_state.current_user}")

# --- 3. 側邊欄 (SCHEDULE) ---
with st.sidebar:
    st.markdown(f"<div class='side-title'>✈️ SCHEDULE</div>", unsafe_allow_html=True)
    st.divider()
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    details_placeholder = st.empty()

# --- 4. 主月曆 ---
st.title(f"💖 {st.session_state.current_user}")

# 設置月曆，強制不縮放
cal_options = {
    "initialDate": today_str,
    "contentHeight": 800,
    "displayEventTime": False,
    "dayMaxEvents": False
}

state = calendar(events=calendar_events, options=cal_options, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示 ---
if state.get("eventClick"):
    fno = state["eventClick"]["event"]["title"].strip()
    match = flight_db[flight_db['班號'] == fno]
    if not match.empty:
        r = match.iloc[0]
        with details_placeholder.container():
            st.markdown(f"""
                <div style='background:#1F1F1F; padding:15px; border-radius:10px; border:2px solid {user_color};'>
                    <h2 style='color:{user_color}; margin:0;'>CI {fno}</h2>
                    <p style='font-size:1.5rem; font-weight:800; margin:5px 0;'>📍 {r['目的地']}</p>
                </div>
            """, unsafe_allow_html=True)
