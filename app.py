import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz
import re

# --- 0. 基本設定 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 (維持 1.8em 大字) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    .fc-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        background: {user_color} !important;
        color: white !important;
    }}
    
    .fc-event-title {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        text-align: center !important; 
    }}

    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 20px;
        border: 2px solid {user_color}; margin-top: 10px;
    }}
    
    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
        font-size: 1.1rem;
    }}
    div.stButton > button:hover {{ border-color: {user_color}; color: {user_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊導覽 ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color};'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.write("---")
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 Flight Details")
    details_container = st.empty()

# --- 3. 數據讀取 ---
calendar_events = []
flight_db = pd.DataFrame()

try:
    # 讀取航班字典
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 讀取 Excel
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        
        # 🚀 這裡不再猜！直接把 Excel 儲存格裡的內容當作標題
        # 如果 Excel 寫 116/117，月曆就會顯示 116/117
        calendar_events.append({
            "title": str(row['班號']), 
            "start": clean_date, 
            "end": clean_date, 
            "allDay": True
        })
except Exception as e:
    st.sidebar.error(f"讀取 {st.session_state.current_user} 班表失敗")

# --- 4. 主畫面 ---
st.title(f"💖 {st.session_state.current_user}")
state = calendar(events=calendar_events, options={"contentHeight": "auto", "displayEventTime": False, "dayMaxEvents": False}, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示邏輯 (精準拆解標題) ---
if state.get("eventClick"):
    full_title = state["eventClick"]["event"]["title"].strip()
    
    # 🚀 拆解邏輯：把 "116/117" 或 "116 117" 拆成獨立的班號
    flight_numbers = re.findall(r'\d+', full_title)
    
    with details_container.container():
        for fno in flight_numbers:
            match = flight_db[flight_db['班號'] == fno]
            if not match.empty:
                r = match.iloc[0]
                # 如果只有一個號碼就是 STAY，多個就標 GO/RTN
                tag = "STAY" if len(flight_numbers) == 1 else ("GO" if fno == flight_numbers[0] else "RTN")
                
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
