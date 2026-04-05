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

# 🎨 核心：CSS 暴力覆蓋藍色
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 強制殺掉所有藍色背景，換成成員專屬色 */
    .fc-v-event, .fc-daygrid-event, .fc-event, .fc-event-main {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        background: {user_color} !important;
    }}
    
    /* 🚀 班號文字：超級大字 + 粗體 */
    .fc-event-title, .fc-event-main-frame {{
        font-size: 1.8rem !important; 
        font-weight: 800 !important;
        color: white !important;
        text-align: center !important;
    }}

    /* 調整左邊按鈕大小 */
    div.stButton > button {{
        font-size: 1rem !important;
        height: 2.8em !important;
        border-radius: 10px;
    }}
    
    .report-card {{ 
        background: #1F1F1F; border-radius: 15px; padding: 20px; 
        border: 2px solid {user_color}; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
calendar_events = []
try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        
        # 💡 在 event 裡面也強制帶入顏色參數
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
    st.markdown("### ✈️ Crew Menu")
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    details_placeholder = st.empty()

# --- 4. 月曆 ---
st.title(f"💖 {st.session_state.current_user}")

# 🚀 這裡增加一個自定義 CSS 的設定
calendar_options = {
    "initialDate": today_str,
    "contentHeight": "auto",
    "eventTextColor": "white",
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
                        <h2 style='color:{user_color}; margin:0;'>CI {t}</h2>
                        <p style='font-size:1.4rem; font-weight:700;'>📍 {r['目的地']}</p>
                        <p>⏰ 報到: {r.get('報到時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
