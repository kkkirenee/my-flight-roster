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

# --- 1. 成員配色 ---
CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 2. 暴力大字 CSS (簡化版) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    /* 這裡只管顏色，不管大小 */
    .fc-event {{ 
        background-color: {user_color} !important; 
        border: none !important; 
    }}
    /* 強制讓月曆格子撐高，否則大字會被切掉 */
    .fc-daygrid-event-harness {{ min-height: 60px !important; }}
    .fc-daygrid-day-frame {{ min-height: 100px !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. 數據讀取與「大字注入」 ---
calendar_events = []
try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        
        # 🚀 關鍵：直接在標題加入大字樣式，繞過外層限制
        big_title = f"{row['班號']}"
        
        calendar_events.append({
            "title": big_title,
            "start": clean_date,
            "end": clean_date,
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color
        })
except Exception as e:
    st.sidebar.warning(f"尚未找到 {st.session_state.current_user} 的分頁")

# --- 4. 側邊欄 ---
with st.sidebar:
    st.markdown(f"### ✈️ Crew Menu")
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    details_placeholder = st.empty()

# --- 5. 月曆設定 (加入自定義大字邏輯) ---
st.title(f"💖 {st.session_state.current_user}")

calendar_options = {
    "initialDate": today_str,
    "contentHeight": 750,
    "eventContent": { "html": f"<div style='font-size:35px; font-weight:900; text-align:center; width:100%; color:white;'>CONTENT</div>" }, # 🚀 這是絕招，直接定義 HTML 內容
}

# 修正：將 CONTENT 換成實際的班號
for ev in calendar_events:
    ev["extendedProps"] = {"fno": ev["title"]}
    
# 重新定義 options 的 HTML 內容來抓取數據
custom_options = {
    "initialDate": today_str,
    "contentHeight": 750,
    "eventContent": { "html": "<b></b>" } # 這裡我們用 Python 端的預設渲染
}

# 最終嘗試：利用 FullCalendar 的強大屬性
state = calendar(
    events=calendar_events, 
    options={
        "initialDate": today_str,
        "contentHeight": 700,
        "eventDidMount": "function(info) { info.el.style.fontSize = '40px'; info.el.style.fontWeight = '900'; }" # 🚀 JavaScript 直接改
    }, 
    key=f"cal_{st.session_state.current_user}"
)

# --- 6. 詳情 ---
if state.get("eventClick"):
    t = state["eventClick"]["event"]["title"].strip()
    match = flight_db[flight_db['班號'] == t]
    if not match.empty:
        r = match.iloc[0]
        with details_placeholder.container():
            st.markdown(f"<div style='background:#1F1F1F; padding:15px; border-radius:10px; border:2px solid {user_color};'><h2>CI {t}</h2><p>📍 {r['目的地']}</p></div>", unsafe_allow_html=True)
