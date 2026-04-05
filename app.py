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

# --- 1. 視覺風格 (CSS 權限最強鎖定) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    /* 🚀 暴力去藍：強制覆蓋月曆所有 Event 標籤 */
    .fc-event, .fc-event-main, .fc-daygrid-event, .fc-event-title-container {{
        background-color: {user_color} !important;
        border: none !important;
        background: {user_color} !important;
        color: white !important;
    }}
    
    /* 🚀 班號文字：1.8em 白色大粗體 */
    .fc-event-title {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        text-align: center !important; 
        color: white !important;
    }}

    .fc-daygrid-event-harness {{ min-height: 60px !important; margin-bottom: 3px !important; }}

    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 20px;
        border: 2px solid {user_color}; box-shadow: 0 0 15px rgba(240,118,153,0.2);
        margin-top: 10px;
    }}
    .tag {{
        background: {user_color}; color: white; padding: 4px 10px;
        border-radius: 6px; font-size: 0.8rem; font-weight: 900;
    }}

    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.2em;
    }}
    div.stButton > button:hover {{ border-color: {user_color}; color: {user_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊導覽 (SCHEDULE) ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color}; font-weight:900;'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.divider()
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    details_container = st.empty()

# --- 3. 數據讀取 (含備註解析) ---
calendar_events = []
flight_db = pd.DataFrame()
roster_lookup = {} # 存放日期對應的班號與備註

try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()
        
        # 建立索引
        roster_lookup[clean_date] = {"fno": f_no, "memo": memo}
        
        calendar_events.append({
            "title": f_no, "start": clean_date, "end": clean_date, "allDay": True,
            "backgroundColor": user_color, "borderColor": user_color
        })
except Exception as e:
    st.sidebar.error(f"讀取 {st.session_state.current_user} 失敗，請檢查 Excel 分頁與欄位")

# --- 4. 主月曆 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")

cal_options = {
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
    "initialDate": today_str,
    "contentHeight": 750,
    "displayEventTime": False,
    "dayMaxEvents": False
}

state = calendar(events=calendar_events, options=cal_options, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示 (精準抓取備註班號) ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = roster_lookup.get(clicked_date, {})
    main_f = info.get("fno", "")
    memo = info.get("memo", "")
    
    # 🚀 從主班號和備註中提取所有數字
    # 例如：主班號 116，備註 117。我們會抓出 ['116', '117']
    flight_list = [main_f]
    memo_fnos = re.findall(r'\d+', memo)
    for f in memo_fnos:
        if f not in flight_list: flight_list.append(f)

    with details_container.container():
        for t in flight_list:
            match = flight_db[flight_db['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                # 判定 STAY 標籤
                is_stay = any(x in memo.lower() for x in ["stay", "過夜", "150", "771", "721", "761"])
                tag = "STAY" if is_stay else ("GO" if t == flight_list[0] and len(flight_list) > 1 else ("RTN" if len(flight_list) > 1 else "FLY"))
                
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{user_color}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:10px 0; font-size:1.3rem; font-weight:800;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.1rem; margin:2px 0;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:10px 0;'>
                        <p style='font-size:0.9rem; color:#AAA; margin:0;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
else:
    details_container.write("✨ 點擊月曆班號看詳情")
