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

# --- 1. 成員與顏色配置 ---
st.set_page_config(page_title="CAL Crew Hub", page_icon="✈️", layout="wide")

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# 🎨 暴力 CSS：全面攔截預設藍色，強制注入粉紅與大字
st.markdown(f"""
    <style>
    /* 整體背景 */
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 暴力攔截所有月曆 Event 的顏色 (標籤、背景、邊框全部鎖死) */
    .fc-daygrid-event, .fc-v-event, .fc-event, .fc-event-main, .fc-event-title-container {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        background: {user_color} !important;
        box-shadow: none !important;
    }}

    /* 🚀 班號文字：超級粗大 2.0rem，置中對齊 */
    .fc-event-title, .fc-event-main {{
        font-size: 2.0rem !important; 
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 100% !important;
    }}

    /* 調整左邊姓名按鈕：回歸正常大小 */
    div.stButton > button {{
        font-size: 1rem !important;
        font-weight: 700 !important;
        height: 2.8em !important;
        border-radius: 10px;
        border: 1px solid #444;
    }}
    div.stButton > button:hover {{
        border-color: {user_color};
        color: {user_color} !important;
    }}

    /* 詳情卡片加強 */
    .report-card {{ 
        background: #1F1F1F; border-radius: 15px; padding: 20px; 
        border: 3px solid {user_color}; 
        box-shadow: 0 0 15px {user_color}33;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
calendar_events = []
try:
    # 航班詳情
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 讀取 Excel (分頁連動)
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        if isinstance(raw_date, datetime):
            clean_date = raw_date.strftime('%Y-%m-%d')
        else:
            clean_date = str(raw_date).split()[0]
        
        # 💡 在資料端也強制寫入顏色屬性，雙重保險
        calendar_events.append({
            "title": str(row['班號']),
            "start": clean_date,
            "end": clean_date,
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color,
            "textColor": "white"
        })
except Exception as e:
    st.sidebar.warning(f"尚未在 Excel 找到 {st.session_state.current_user} 的分頁")

# --- 3. 側邊欄導航 ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center;'>✈️ Crew Hub</h3>", unsafe_allow_html=True)
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 Flight Details")
    details_placeholder = st.empty()

# --- 4. 主頁面月曆 ---
st.title(f"💖 {st.session_state.current_user}")

# 設置月曆選項
calendar_options = {
    "initialDate": today_str,
    "contentHeight": "auto",
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
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
                        <p style='font-size:1.1rem;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                    </div>
                """, unsafe_allow_html=True)
