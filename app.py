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

# 初始化當前使用者
if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

HOT_PINK = "#F07699"
BG_BLACK = "#0E0E0E"

# 定義成員與對應顏色
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
    
    /* 🚀 暴力鎖死月曆內部的顏色與大字 */
    .fc-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        color: white !important;
        background: {user_color} !important;
    }}
    
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {user_color}; box-shadow: 0 0 20px rgba(240,118,153,0.3);
        margin-bottom: 15px;
    }}
    .tag {{
        background: {user_color}; color: white; padding: 4px 12px;
        border-radius: 6px; font-size: 0.9rem; font-weight: 900;
    }}

    /* 側邊欄按鈕樣式 */
    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
        font-size: 1.1rem; transition: 0.3s; margin-bottom: 10px;
    }}
    div.stButton > button:hover {{
        border-color: {user_color}; color: {user_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊導覽列 (SCHEDULE Frame) ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color};'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.write("---")
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.write("---")
    st.subheader("📋 Flight Details")
    details_container = st.empty()

# --- 3. 數據讀取 ---
calendar_events = []
flight_db = pd.DataFrame()

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
            "title": str(row['班號']), "start": clean_date, "end": clean_date,
            "backgroundColor": user_color, "borderColor": user_color, "allDay": True
        })
except Exception as e:
    st.sidebar.error(f"找不到 {st.session_state.current_user} 的班表")

# --- 4. 顯示主畫面 ---
st.title(f"💖 {st.session_state.current_user}")

col1, col2 = st.columns([2.5, 0.1]) 

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "initialDate": today_str,
        "contentHeight": "auto",
        "displayEventTime": False,
        "dayMaxEvents": False
    }
    # 🚀 妳最滿意的 1.8em 大字
    custom_css = ".fc-event-title { font-size: 1.8em !important; font-weight: 900 !important; text-align: center !important; color: white !important; }"
    state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示邏輯 (針對 Belle 修正過夜班) ---
if state.get("eventClick"):
    clicked_fno = state["eventClick"]["event"]["title"].strip()
    
    # 🚀 根據使用者切換過夜班清單
    if st.session_state.current_user == "Isabelle":
        # Belle 的過夜班
        stay_list = ["150", "771", "721", "761"]
    else:
        # Irene 與其他人的預設過夜班
        stay_list = ["150", "130", "731", "721"]
    
    search_list = [clicked_fno]
    
    # 如果點擊的班號不在「過夜班」清單中，且是偶數去程，才自動抓回程
    if clicked_fno not in stay_list:
        try:
            if int(clicked_fno) % 2 == 0:
                search_list.append(str(int(clicked_fno) + 1))
        except: pass

    with details_container.container():
        for t in search_list:
            match = flight_db[flight_db['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                tag = "GO" if (len(search_list)>1 and t==clicked_fno) else ("RTN" if len(search_list)>1 else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{user_color}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:15px 0 5px 0; font-size:1.3rem;'>📍 <b>{r['目的地']}</b></p>
                        <p style='font-size:1.1rem; margin:2px 0;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:10px 0;'>
                        <p style='font-size:1rem; color:#AAA; margin:0;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
else:
    details_container.write("✨ 點擊班號看詳情")
