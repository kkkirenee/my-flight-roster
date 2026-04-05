import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 時區校準 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

HOT_PINK = "#F07699"
BG_BLACK = "#0E0E0E"

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 強制鎖死月曆內部的顏色與字體 */
    .fc-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        color: white !important;
        background: {user_color} !important;
    }}
    
    .report-card {{
        background: #1A1A1A; border-radius: 15px; padding: 20px;
        border: 2px solid {user_color}; box-shadow: 0 0 15px rgba(240,118,153,0.2);
        margin-top: 10px;
    }}

    /* 側邊欄按鈕 */
    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.2em;
        font-size: 1rem; transition: 0.2s; margin-bottom: 5px;
    }}
    div.stButton > button:hover {{ border-color: {user_color}; color: {user_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊導覽列 (SCHEDULE) ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color};'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.write("---")
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.write("---")
    st.subheader("📋 Flight Details")
    # 預留顯示詳細資訊的地方
    info_area = st.empty()

# --- 3. 讀取資料 ---
calendar_events = []
flight_db = pd.DataFrame()

try:
    # 讀取 CSV 航班字典
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 讀取 Excel 對應分頁
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        calendar_events.append({
            "title": str(row['班號']), "start": clean_date, "end": clean_date,
            "backgroundColor": user_color, "borderColor": user_color, "allDay": True
        })
except Exception as e:
    info_area.error(f"讀取 {st.session_state.current_user} 班表失敗")

# --- 4. 顯示主月曆 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")

calendar_options = {
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
    "initialView": "dayGridMonth",
    "initialDate": today_str,
    "contentHeight": 700,
    "displayEventTime": False,
    "dayMaxEvents": False
}

# 🚀 妳最愛的超大粗體白色字
custom_css = ".fc-event-title { font-size: 1.8em !important; font-weight: 900 !important; text-align: center !important; color: white !important; }"

state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示邏輯 (修復資訊消失問題) ---
if state.get("eventClick"):
    # 取得點擊的班號
    fno = state["eventClick"]["event"]["title"].strip()
    
    # 從 CSV 尋找詳細資訊
    match = flight_db[flight_db['班號'] == fno]
    
    if not match.empty:
        r = match.iloc[0]
        # 在左側 info_area 顯示完整資訊
        info_area.markdown(f"""
            <div class="report-card">
                <h2 style='color:{user_color}; margin:0;'>CI {fno}</h2>
                <p style='margin:10px 0; font-size:1.3rem; font-weight:800;'>📍 {r['目的地']}</p>
                <p style='font-size:1.1rem; margin:5px 0;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                <hr style='border-color:#444; margin:10px 0;'>
                <p style='font-size:1rem; color:#AAA; margin:0;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        info_area.warning(f"找不到班號 {fno} 的詳細資訊")
else:
    info_area.write("✨ 點擊月曆班號看詳情")
