import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz
import re

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")
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

# --- 1. 視覺風格 (卡片樣式) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    /* 這裡只管側邊欄和卡片，月曆交給 JS */
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 20px;
        border: 2px solid {user_color}; margin-top: 10px;
    }}
    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
    }}
    div.stButton > button:hover {{ border-color: {user_color}; color: {user_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊導覽 ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color}; font-weight:900;'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.divider()
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
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
            "title": str(row['班號']), "start": clean_date, "end": clean_date, "allDay": True,
            "backgroundColor": user_color, "borderColor": user_color # 鎖定底色
        })
except Exception as e:
    st.sidebar.error(f"找不到 {st.session_state.current_user} 的班表")

# --- 4. 主月曆 (暴力 JS 注入) ---
st.title(f"💖 {st.session_state.current_user}'s Roster")

# 🚀 這裡是關鍵：eventContent 裡面寫 JavaScript 暴力換字體
calendar_options = {
    "initialDate": today_str,
    "contentHeight": 750,
    "displayEventTime": False,
    "dayMaxEvents": False,
    # 暴力大字術：強制將文字層（.fc-event-title）的字體設為 35px，並刪除不需要的點點和時間
    "eventContent": {
        "html": f"<div style='font-size:35px; font-weight:900; text-align:center; color:white; width:100%;'>{{{{title}}}}</div>"
    },
}

state = calendar(events=calendar_events, options=calendar_options, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示 ---
if state.get("eventClick"):
    full_title = state["eventClick"]["event"]["title"].strip()
    
    if st.session_state.current_user == "Isabelle":
        stay_list = ["150", "771", "721", "761"]
    else:
        stay_list = ["150", "130", "731", "721"]

    flight_numbers = re.findall(r'\d+', full_title)
    
    with details_container.container():
        for fno in flight_numbers:
            match = flight_db[flight_db['班號'] == fno]
            if not match.empty:
                r = match.iloc[0]
                # 判定 STAY / GO / RTN
                if fno in stay_list:
                    tag = "STAY"
                else:
                    tag = "GO" if (len(flight_numbers) > 1 and fno == flight_numbers[0]) else ("RTN" if len(flight_numbers) > 1 else "STAY")
                
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{user_color}; margin:0;'>CI {fno}</h2>
                            <span style='background:{user_color}; color:white; padding:2px 8px; border-radius:5px; font-size:0.8rem;'>{tag}</span>
                        </div>
                        <p style='margin:10px 0 5px 0; font-size:1.3rem; font-weight:800;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.1rem; margin:2px 0;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:10px 0;'>
                        <p style='font-size:0.9rem; color:#AAA; margin:0;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
else:
    details_container.write("✨ 點擊班號看詳情")
