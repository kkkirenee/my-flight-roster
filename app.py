import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 初始化 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

# --- 1. 配置 ---
st.set_page_config(page_title="CAL Crew Hub", page_icon="✈️", layout="wide")

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# 🎨 核心：極致大字 CSS (這版針對內層容器)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 暴力去藍變粉：覆蓋所有可能的 class */
    .fc-event, .fc-event-main, .fc-daygrid-event, .fc-v-event, .fc-event-title-container {{
        background-color: {user_color} !important;
        border: none !important;
        background: {user_color} !important;
    }}

    /* 🚀 班號文字：鎖定標題，強制 4.0rem 並取消所有縮放限制 */
    .fc-event-title, div.fc-event-main, .fc-event-title-container {{
        font-size: 4.0rem !important; 
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
        line-height: 1.2 !important;
        overflow: visible !important;
        white-space: normal !important;
    }}
    
    /* 🚀 讓格子長高到足以裝下巨型數字 */
    .fc-daygrid-day-frame, .fc-daygrid-day-events, .fc-daygrid-event-harness {{
        min-height: 100px !important;
        height: auto !important;
    }}

    /* 按鈕大小 */
    div.stButton > button {{
        font-size: 1rem !important;
        height: 3em !important;
    }}
    
    .report-card {{ 
        background: #1F1F1F; border-radius: 15px; padding: 20px; 
        border: 3px solid {user_color}; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
calendar_events = []
try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        
        # 💡 資料端的大絕招：直接把 title 寫成 HTML 粗體
        # 雖然有些元件會過濾 HTML，但這是最後的保險
        calendar_events.append({
            "title": str(row['班號']), 
            "start": clean_date,
            "end": clean_date,
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color,
            "display": "block"
        })
except Exception as e:
    st.sidebar.warning(f"尚未找到 {st.session_state.current_user} 分頁")

# --- 3. 側邊欄 ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center; color:{user_color};'>✈️ Crew Menu</h3>", unsafe_allow_html=True)
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    details_placeholder = st.empty()

# --- 4. 主頁面月曆 ---
st.title(f"💖 {st.session_state.current_user}")

# 🚀 這裡增加一組重要設定，取消所有自動縮放
calendar_options = {
    "initialView": "dayGridMonth",
    "initialDate": today_str,
    "contentHeight": 800, # 🚀 強制月曆撐開高度，不要縮成一團
    "displayEventTime": False,
    "dayMaxEvents": False,
}

state = calendar(events=calendar_events, options=calendar_options, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情連動 ---
overnight_flights = ["130", "731", "150", "761", "721", "771"]
if state.get("eventClick"):
    target = state["eventClick"]["event"]["title"].strip()
    with details_placeholder.container():
        s_list = [target]
        if target not in overnight_flights:
            try: s_list.append(str(int(target) + 1))
            except: pass
        for t in s_list:
            match = flight_db[flight_db['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                st.markdown(f"""
                    <div class="report-card">
                        <h2 style='color:{user_color}; margin:0; font-size:2rem;'>CI {t}</h2>
                        <p style='font-size:1.4rem; font-weight:700;'>📍 {r['目的地']}</p>
                    </div>
                """, unsafe_allow_html=True)
