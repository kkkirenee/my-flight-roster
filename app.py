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

if "current_user" not in st.session_state:
    st.session_state.current_user = "Elaine"

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 (🚀 拔除 Today + 版面極致上移) ---
st.markdown(f"""
    <style>
    /* 🚀 極致縮減頂部空白 */
    .stApp {{ background-color: #0E0E0E; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; padding-bottom: 0rem !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
/* 🚀 姓名按鈕 - 炫炮漸層 */
    .stButton > button {{
        width: 100% !important; height: 50px !important;
        font-size: 1.2rem !important; font-weight: 800 !important;
        color: white !important; background-color: #1A1A1A !important;
        border-radius: 12px !important; border: 2px solid transparent !important; 
        background: linear-gradient(#1A1A1A, #1A1A1A) padding-box,
                    linear-gradient(135deg, {user_color}88, #0E0E0E) border-box !important;
        margin-bottom: 10px !important;
    }}

    /* 🚀 1. 新增：月曆格子縮小 (注意這裡也是雙大括號) */
    .fc-daygrid-day-frame {{ 
        min-height: 85px !important; 
    }}

    /* 🚀 2. 月曆自定義：隱記非本月的格子 */
    .fc-day-other {{
        visibility: hidden !important; 
    }}
    
    .fc .fc-toolbar-title {{ font-size: 1.5rem !important; font-weight: 800; }}
    
    /* 🚀 導覽按鈕配色 (僅保留 < >) */
    .fc .fc-button-primary {{
        background-color: transparent !important;
        border: 2px solid {user_color} !important;
        color: {user_color} !important;
        font-weight: 800 !important;
    }}
    
    /* 事件樣式 */
    div.fc-event {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 1.8em !important; font-weight: 900 !important; }}

    /* 航班卡片 */
    .flight-card {{
        background: #1A1A1A; border-radius: 20px; padding: 15px !important;
        border: 3px solid {user_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center; margin-bottom:10px;'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    for name in CREW_CONFIG.keys():
        if st.button(name, key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    info_placeholder = st.container()

# --- 3. 數據解析 (維持邏輯) ---
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
        start_dt = pd.to_datetime(row['日期'])
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()
        d_key = start_dt.strftime('%Y-%m-%d')
        flight_list = [f_no]
        rtn_fno = ""
        date_pattern = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', memo)
        rtn_match = re.search(r'回程\s*(\d+)', memo)
        if rtn_match:
            rtn_fno = rtn_match.group(1)
            if not date_pattern: flight_list.append(rtn_fno)
        click_lookup[d_key] = {"flights": flight_list, "memo": memo}
        calendar_events.append({"title": f_no, "start": d_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
        if date_pattern:
            try:
                end_dt = pd.to_datetime(date_pattern.group(1))
                if end_dt > start_dt:
                    if (end_dt - start_dt).days > 1:
                        calendar_events.append({"title": " ", "start": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "end": end_dt.strftime('%Y-%m-%d'), "allDay": True})
                    r_key = end_dt.strftime('%Y-%m-%d')
                    click_lookup[r_key] = {"flights": [rtn_fno], "memo": f"回程自 {start_dt.strftime('%m/%d')} CI{f_no}"}
                    calendar_events.append({"title": rtn_fno, "start": r_key, "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
            except: pass
except Exception as e:
    st.sidebar.error(f"錯誤：{e}")

# --- 4. 渲染月曆 (🚀 取消 Today + 隱藏非本月日期) ---
st.markdown(f"<h2 style='margin-bottom:0px; margin-top:0px;'>💖 {st.session_state.current_user}</h2>", unsafe_allow_html=True)

cal_options = {
    "initialDate": "2026-04-01",
    "displayEventTime": False,
    "headerToolbar": {"left": "prev,next", "center": "title", "right": ""}, # 🚀 移除 today
    "fixedWeekCount": False, # 🚀 自動調整週數，不顯示多餘的週
    "showNonCurrentDates": False, # 🚀 不顯示非本月的日期數字
}

cal_css = f"""
    .fc-event-main {{ background-color: {user_color} !important; }}
    .fc-event-title {{ font-size: 1.8em !important; font-weight: 900 !important; }}
"""

state = calendar(
    events=calendar_events, 
    options=cal_options, 
    custom_css=cal_css,
    key=f"cal_vfinal_clean_{st.session_state.current_user}"
)

# --- 5. 點擊顯示 (略，維持現有卡片邏輯) ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = click_lookup.get(clicked_date)
    if info:
        with info_placeholder:
            for fno in info["flights"]:
                target_f = fno.upper().replace('CI', '').strip()
                match = flight_db[flight_db['f_clean'] == target_f] if not flight_db.empty else pd.DataFrame()
                if not match.empty:
                    r = match.iloc[0]
                    def get_v(keys):
                        for k in keys:
                            if k in r and str(r[k]).strip() != "": return str(r[k]).strip()
                        return "--:--"
                    dest = get_v(['目的地', '地點'])
                    report = get_v(['報到時間', '報到'])
                    dep_t = get_v(['起飛時間', '起飛'])
                    arr_t = get_v(['落地時間', '降落時間', '降落', 'ARR'])
                    st.markdown(f"""
                        <div class="flight-card">
                            <p style="color:{user_color}; font-size:1.2rem; font-weight:900; margin:0;">CI {target_f}</p>
                            <p style="font-size:1.6rem; font-weight:950; margin:5px 0;">📍 {dest}</p>
                            <p style="font-size:0.9rem; color:#BBB; margin-bottom:5px;">⏰ 報到: {report}</p>
                            <div style="display:flex; justify-content:space-between; background:#262626; padding:10px; border-radius:10px;">
                                <div style="text-align:center;"><p style="font-size:0.7rem; color:#888; margin:0;">起飛</p><p style="font-size:1.2rem; font-weight:800; color:white; margin:0;">{dep_t}</p></div>
                                <div style="text-align:center;"><p style="font-size:0.7rem; color:#888; margin:0;">落地</p><p style="font-size:1.2rem; font-weight:800; color:white; margin:0;">{arr_t}</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
