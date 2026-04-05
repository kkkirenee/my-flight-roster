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

# 🎨 核心：超級巨無霸字體 CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 強制去藍變粉 */
    .fc-event, .fc-event-main, .fc-daygrid-event, .fc-v-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        background: {user_color} !important;
    }}

    /* 🚀 班號字體：直接上 3.0rem (超級大)，並強制撐開高度 */
    .fc-event-title, .fc-event-main {{
        font-size: 3.0rem !important; 
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
        line-height: 1 !important;
        padding: 5px 0 !important;
        display: block !important;
    }}
    
    /* 讓月曆格子可以容納這麼大的字 */
    .fc-daygrid-event-harness {{
        margin-top: 2px !important;
    }}

    /* 按鈕維持正常大小 */
    div.stButton > button {{
        font-size: 1rem !important;
        font-weight: 700 !important;
        height: 2.8em !important;
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
            "borderColor": user_color
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

# --- 4. 月曆 ---
st.title(f"💖 {st.session_state.current_user}")

# 設置月曆，拿掉縮放限制
calendar_options = {
    "initialDate": today_str,
    "contentHeight": "auto",
    "displayEventTime": False,
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
                        <p style='font-size:1.1rem;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                    </div>
                """, unsafe_allow_html=True)
