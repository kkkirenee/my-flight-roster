import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz
import re
import os

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

# 定義成員配色
CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 (最強權限 CSS) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    /* 🚀 去藍變粉/紫：強制覆蓋月曆所有 Event 標籤 */
    div.fc-event, div.fc-event-main, div.fc-daygrid-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        background: {user_color} !important;
    }}
    
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {user_color}; box-shadow: 0 0 20px rgba(0,0,0,0.5);
        margin-bottom: 15px;
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
    details_container = st.empty()

# --- 3. 數據讀取 ---
calendar_events = []
flight_db = pd.DataFrame()
roster_lookup = {}

roster_path = "CAL_Roster.xlsx"
flight_db_path = "my_flights.csv"

try:
    if os.path.exists(flight_db_path):
        flight_db = pd.read_csv(flight_db_path, encoding='utf-8-sig')
        flight_db.columns = flight_db.columns.str.strip()
        flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    if os.path.exists(roster_path):
        user_df = pd.read_excel(roster_path, sheet_name=st.session_state.current_user)
        user_df.columns = user_df.columns.str.strip()
        
        for _, row in user_df.iterrows():
            raw_date = row['日期']
            clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
            f_no = str(row['班號']).strip()
            memo = str(row.get('備註', '')).strip()
            roster_lookup[clean_date] = {"fno": f_no, "memo": memo}
            
            # 在 Event 資料裡也塞入顏色資訊，雙重保險
            calendar_events.append({
                "title": f_no, 
                "start": clean_date, 
                "end": clean_date, 
                "allDay": True,
                "backgroundColor": user_color,
                "borderColor": user_color,
                "textColor": "white"
            })
except Exception as e:
    st.sidebar.error(f"讀取出錯：{str(e)}")

# --- 4. 主月曆 (鎖死大字與配色) ---
st.title(f"💖 {st.session_state.current_user}'s Roster")

# 這裡的 custom_css 必須包含動態的 user_color
calendar_custom_css = f"""
    .fc-event-title {{ 
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        text-align: center !important; 
        color: white !important; 
    }}
    .fc-event {{ 
        background-color: {user_color} !important; 
        border: none !important; 
    }}
"""

state = calendar(
    events=calendar_events, 
    options={"contentHeight": "auto", "displayEventTime": False, "dayMaxEvents": False}, 
    custom_css=calendar_custom_css, 
    key=f"cal_{st.session_state.current_user}"
)

# --- 5. 詳情顯示邏輯 (100% 聽備註的話) ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = roster_lookup.get(clicked_date, {})
    main_f = info.get("fno", "")
    memo = str(info.get("memo", ""))
    
    display_list = [main_f]
    memo_fnos = re.findall(r'\d+', memo)
    for f in memo_fnos:
        if f not in display_list: display_list.append(f)

    with details_container.container():
        for t in display_list:
            match = flight_db[flight_db['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                is_stay = any(x in memo for x in ["過夜", "Stay", "stay"])
                tag = "STAY" if is_stay else ("GO" if (len(display_list) > 1 and t == display_list[0]) else ("RTN" if len(display_list) > 1 else "FLY"))
                
                st.markdown(f"""
                    <div class="report-card">
                        <h2 style='color:{user_color}; margin:0;'>CI {t} <span style='font-size:0.8rem; background:{user_color}; color:white; padding:2px 8px; border-radius:5px; vertical-align:middle;'>{tag}</span></h2>
                        <p style='margin:10px 0; font-size:1.3rem; font-weight:800;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.1rem;'>⏰ 報到: {r.get('報到時間','--:--')}</p>
                        <hr style='border-color:#444;'>
                        <p style='font-size:0.9rem; color:#AAA;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
else:
    details_container.write("✨ 點擊班號看詳情")
