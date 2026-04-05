import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import re
import os

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL SCHEDULE", layout="wide")

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "sheet": "Irene"},
    "Isabelle": {"color": "#A28CF0", "sheet": "Isabelle"},
    "Elaine": {"color": "#76C9F0", "sheet": "Elaine"},
    "Bigpiao": {"color": "#F0B476", "sheet": "Bigpiao"}
}

# 初始化狀態，防止跳掉
if "current_user" not in st.session_state:
    st.session_state.current_user = "Elaine"
if "clicked_info" not in st.session_state:
    st.session_state.clicked_info = None

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 (🚀 這次把 CSS 寫死，絕對不動到邏輯) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; padding-bottom: 0rem !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 橫向排排站 + 暴力靠左聚集 */
    div[data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        justify-content: flex-start !important;
        margin-left: -15px !important;
    }}
    [data-testid="column"] {{
        width: auto !important;
        flex: 0 0 auto !important;
        padding: 0 !important;
    }}

    /* 🚀 姓名按鈕：圓角 + 呼吸光 */
    .stButton > button {{
        width: 78px !important; height: 38px !important;
        font-size: 0.85rem !important; font-weight: 800 !important;
        color: #888 !important; background-color: #1A1A1A !important;
        border: 2px solid #333 !important; border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }}
    .stButton > button:focus, .stButton > button:active, .stButton > button:hover {{
        background-color: {user_color} !important;
        color: white !important;
        box-shadow: 0 0 15px {user_color}AA !important;
        border: 2px solid white !important;
    }}

    /* 月曆字體與顏色 */
    .fc-event {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 1.6em !important; font-weight: 900 !important; color: white !important; }}
    .fc-daygrid-day-frame {{ min-height: 80px !important; }}
    .fc-day-other {{ visibility: hidden !important; }}
    
    @media (max-width: 768px) {{
        .fc-event-title {{ font-size: 1.1em !important; }}
        .fc-daygrid-day-frame {{ min-height: 60px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 頂部導覽 (按鈕換人) ---
st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center; margin-bottom:5px; font-size:1.3rem;'>✈️ CAL SCHEDULE</h1>", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns([1,1,1,1,2])
for i, name in enumerate(CREW_CONFIG.keys()):
    with [c1, c2, c3, c4][i]:
        if st.button(name):
            st.session_state.current_user = name
            st.session_state.clicked_info = None # 換人時清空點擊資訊
            st.rerun()

st.markdown(f"<h2 style='margin: 5px 0; text-align:center; font-size:1.2rem; color:{user_color};'>💖 {st.session_state.current_user}</h2>", unsafe_allow_html=True)
info_box = st.container()

# --- 3. 數據讀取 (🚀 保證所有欄位解析都在) ---
calendar_events = []
flight_db = pd.DataFrame()
click_lookup = {}

try:
    if os.path.exists("my_flights.csv"):
        flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig').fillna("")
        flight_db.columns = flight_db.columns.str.strip()
        flight_db['f_clean'] = flight_db['班號'].astype(str).str.upper().str.replace('CI', '').str.strip()
    
    xl = pd.ExcelFile("CAL_Roster.xlsx")
    df = pd.read_excel(xl, sheet_name=CREW_CONFIG[st.session_state.current_user]["sheet"])
    df.columns = df.columns.str.strip()

    for _, row in df.iterrows():
        if pd.isna(row['日期']): continue
        d_str = pd.to_datetime(row['日期']).strftime('%Y-%m-%d')
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()
        
        click_lookup[d_str] = {"flights": [f_no], "memo": memo}
        calendar_events.append({"title": f_no, "start": d_str, "allDay": True})
        
        # 解析回程
        rtn_match = re.search(r'回程\s*(\d+)', memo)
        date_match = re.search(r'(\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}})', memo)
        if rtn_match and date_match:
            r_date = pd.to_datetime(date_match.group(1)).strftime('%Y-%m-%d')
            click_lookup[r_date] = {"flights": [rtn_match.group(1)], "memo": "回程"}
            calendar_events.append({"title": rtn_match.group(1), "start": r_date, "allDay": True})
except Exception as e:
    st.error(f"讀取失敗: {e}")

# --- 4. 月曆渲染 ---
cal_state = calendar(
    events=calendar_events,
    options={
        "initialDate": "2026-04-01",
        "headerToolbar": {"left": "prev,next", "center": "title", "right": ""},
        "fixedWeekCount": False, "showNonCurrentDates": False, "height": "auto"
    },
    custom_css=f".fc-event {{ background-color: {user_color} !important; }}",
    key=f"cal_{st.session_state.current_user}"
)

# 🚀 鎖定點擊資訊
if cal_state.get("eventClick"):
    st.session_state.clicked_info = cal_state["eventClick"]["event"]["start"].split('T')[0]

# --- 5. 顯示卡片 (🚀 從 Session State 抓，保證不跳掉) ---
if st.session_state.clicked_info:
    info = click_lookup.get(st.session_state.clicked_info)
    if info:
        with info_box:
            for fno in info["flights"]:
                target = fno.upper().replace('CI', '').strip()
                match = flight_db[flight_db['f_clean'] == target] if not flight_db.empty else pd.DataFrame()
                
                # 預設值
                dest, report, dep, arr = "??", "--:--", "--:--", "--:--"
                if not match.empty:
                    r = match.iloc[0]
                    dest = r.get('目的地', r.get('地點', '??'))
                    report = r.get('報到時間', r.get('報到', '--:--'))
                    dep = r.get('起飛時間', r.get('起飛', '--:--'))
                    arr = r.get('落地時間', r.get('落地', '--:--'))

                st.markdown(f"""
                    <div style="background:#1A1A1A; border-radius:15px; padding:15px; border:3px solid {user_color}; margin-top:10px;">
                        <p style="color:{user_color}; font-size:1rem; font-weight:900; margin:0;">CI {target}</p>
                        <p style="font-size:1.5rem; font-weight:950; margin:5px 0;">📍 {dest}</p>
                        <p style="font-size:0.8rem; color:#BBB;">⏰ 報到: {report}</p>
                        <div style="display:flex; justify-content:space-between; background:#262626; padding:10px; border-radius:10px;">
                            <div style="text-align:center;"><p style="font-size:0.7rem; color:#888; margin:0;">起飛</p><p style="font-size:1.2rem; font-weight:800; color:white; margin:0;">{dep}</p></div>
                            <div style="text-align:center;"><p style="font-size:0.7rem; color:#888; margin:0;">落地</p><p style="font-size:1.2rem; font-weight:800; color:white; margin:0;">{arr}</p></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
