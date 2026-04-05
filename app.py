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

# 🎨 核心：打破所有限制的「超級巨無霸」CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 1. 暴力去藍：鎖定所有可能的層級 */
    .fc-event, .fc-event-main, .fc-daygrid-event, .fc-daygrid-event-harness, .fc-event-title-container {{
        background-color: {user_color} !important;
        border: none !important;
        background: {user_color} !important;
    }}

    /* 🚀 2. 班號字體：3.5rem (比剛才更大)，強制撐開所有外殼 */
    .fc-event-title, .fc-event-main, .fc-event-title-container {{
        font-size: 3.5rem !important; 
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
        line-height: 1.2 !important;
        display: block !important;
        height: auto !important; /* 解除高度限制 */
        min-height: 60px !important; /* 強制最低高度 */
    }}
    
    /* 🚀 3. 強制讓月曆格子長高，不然字會重疊 */
    .fc-daygrid-day-events {{
        min-height: 80px !important;
    }}
    
    .fc-daygrid-event-harness {{
        margin-top: 5px !important;
        margin-bottom: 5px !important;
    }}

    /* 按鈕稍微調小，不要擋路 */
    div.stButton > button {{
        font-size: 0.9rem !important;
        height: 2.5em !important;
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
        
        calendar_events.append({
            "title": str(row['班號']),
            "start": clean_date,
            "end": clean_date,
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color,
            "display": "block" # 🚀 強制以區塊顯示
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

calendar_options = {
    "initialDate": today_str,
    "contentHeight": "auto",
    "displayEventTime": False,
    "dayMaxEvents": False, # 🚀 防止出現 "+ more" 連結，全部顯示出來
}

state = calendar(events=calendar_events, options=calendar_options, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情 ---
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
