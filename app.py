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

# --- 1. 視覺鎖定 CSS (強制班號變大) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 去藍變粉 */
    .fc-event, .fc-event-main, .fc-daygrid-event {{
        background-color: {user_color} !important;
        border: none !important;
    }}

    /* 🚀 班號字體放大：直接針對標題 */
    .fc-event-title {{
        font-size: 2.5rem !important; 
        font-weight: 900 !important;
        line-height: 1 !important;
        text-align: center !important;
        display: block !important;
        padding: 8px 0 !important;
    }}

    /* 讓月曆格子有高度 */
    .fc-daygrid-event-harness {{ min-height: 60px !important; }}
    
    /* 詳情資訊卡片 */
    .detail-card {{
        background: #1F1F1F;
        padding: 20px;
        border-radius: 15px;
        border: 3px solid {user_color};
        margin-top: 10px;
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
        })
except Exception as e:
    st.sidebar.warning(f"尚未找到 {st.session_state.current_user} 的資料")

# --- 3. 側邊導航 ---
with st.sidebar:
    st.markdown(f"### ✈️ Menu")
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 航班詳情")
    details_container = st.empty()

# --- 4. 主月曆 ---
st.title(f"💖 {st.session_state.current_user}")

state = calendar(
    events=calendar_events, 
    options={{
        "initialDate": today_str,
        "contentHeight": 650,
        "dayMaxEvents": False,
    }}, 
    key=f"cal_{st.session_state.current_user}"
)

# --- 5. 詳情顯示邏輯 ---
if state.get("eventClick"):
    clicked_fno = state["eventClick"]["event"]["title"].strip()
    match = flight_db[flight_db['班號'] == clicked_fno]
    if not match.empty:
        r = match.iloc[0]
        details_container.markdown(f"""
            <div class="detail-card">
                <h2 style='color:{user_color}; margin:0;'>CI {clicked_fno}</h2>
                <p style='font-size:1.5rem; font-weight:800; margin:10px 0;'>📍 {r['目的地']}</p>
                <p>⏰ 報到: {r.get('報到時間','--:--')}</p>
            </div>
        """, unsafe_allow_html=True)
else:
    details_container.write("✨ 點擊班號看詳情")
