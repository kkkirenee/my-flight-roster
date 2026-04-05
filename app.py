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

# --- 1. 視覺風格 (🚀 左炫炮、右純色、Today 按鈕功能修復) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 姓名按鈕 - 橫向炫炮漸層 */
    .stButton > button {{
        width: 100% !important;
        height: 50px !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        color: white !important;
        background-color: #1A1A1A !important;
        border-radius: 12px !important;
        border: 2px solid transparent !important; 
        transition: all 0.3s ease-in-out !important;
        background-clip: padding-box; 
        margin-bottom: 10px !important;
        background: linear-gradient(#1A1A1A, #1A1A1A) padding-box,
                    linear-gradient(135deg, {user_color}88, #0E0E0E) border-box !important;
    }}
    .stButton > button:hover {{
        background: linear-gradient(#262626, #262626) padding-box,
                    linear-gradient(135deg, white, {user_color}) border-box !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 0 15px {user_color}88 !important;
    }}

    /* 🚀 月曆事件純色 */
    div.fc-event, .fc-daygrid-event, .fc-event-main {{
        background-color: {user_color} !important; border: none !important;
    }}
    .fc-event-title {{ font-size: 1.8em !important; font-weight: 900 !important; }}

    /* 🚀 Today 按鈕視覺與點擊優化 */
    .fc .fc-today-button, .fc-button-primary {{
        background-color: transparent !important;
        background-image: none !important;
        border: 2px solid {user_color} !important;
        color: {user_color} !important;
        font-weight: 800 !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        z-index: 999 !important;
    }}
    .fc .fc-today-button:hover {{
        background-color: {user_color}33 !important;
        color: white !important;
    }}

    /* 🚀 航班資訊卡片 */
    .flight-card {{
        background: #1A1A1A; border-radius: 20px; padding: 20px !important;
        border: 3px solid {user_color} !important; margin-top: 15px;
    }}
    .card-title {{ color: {user_color}; font-size: 1.5rem !important; font-weight: 900; }}
    .card-dest {{ font-size: 2rem !important; font-weight: 950; margin: 10px 0; }}
    .time-val {{ font-size: 1.5rem !important; font-weight: 800; color: white; }}
    .time-box {{ display: flex; justify-content: space-between; background: #262626; padding: 15px; border-radius: 12px; margin: 10px 0; border: 1px solid #333; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center; margin-bottom:20px;'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    for name in CREW_CONFIG.keys():
        if st.button(name, key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    info_placeholder = st.container()

# --- 3. 數據解析 ---
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

# --- 4. 渲染月曆 (🚀 修正後的單大括號語法) ---
st.title(f"💖 {st.session_state.current_user}")
cal_css = f"""
    .fc-event, .fc-event-main {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 1.8em !important; font-weight: 900 !important; }}
"""
state = calendar(
    events=calendar_events, 
    options={
        "initialDate": "2026-04-01", 
        "displayEventTime": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""}
    }, 
    custom_css=cal_css,
    key=f"cal_vfinal_stable_{st.session_state.current_user}"
)

# --- 5. 點擊顯示 ---
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
                            <p class="card-title">CI {target_f}</p>
                            <p class="card-dest">📍 {dest}</p>
                            <p style="font-size:1rem; color:#BBB; margin-bottom:10px;">⏰ 報到時間: {report}</p>
                            <div class="time-box">
                                <div style="text-align:center;"><p class="time-label">起飛 DEP</p><p class="time-val">{dep_t}</p></div>
                                <div style="align-self:center; color:#555; font-size:1.5rem;">✈️</div>
                                <div style="text-align:center;"><p class="time-label">落地 ARR</p><p class="time-val">{arr_t}</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            st.caption(f"💡 資訊：{info['memo']}")
