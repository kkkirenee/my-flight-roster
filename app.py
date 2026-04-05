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

# --- 1. 視覺風格 (🚀 手機頂部按鈕補丁) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; padding-bottom: 0rem !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 讓手機版的按鈕不要太擠 */
    .stButton > button {{
        width: 100% !important; height: 45px !important;
        font-size: 1rem !important; font-weight: 800 !important;
        color: white !important; background-color: #1A1A1A !important;
        border-radius: 10px !important; border: 2px solid transparent !important; 
        background: linear-gradient(#1A1A1A, #1A1A1A) padding-box,
                    linear-gradient(135deg, {user_color}88, #0E0E0E) border-box !important;
    }}

    /* 🚀 手機版 RWD 調整 */
    @media (max-width: 768px) {{
        .fc-event-title {{ font-size: 1.1em !important; }}
        .fc-daygrid-day-frame {{ min-height: 60px !important; }}
        /* 隱藏側邊欄的提示，因為我們把按鈕移到主畫面了 */
        [data-testid="stSidebar"] {{ display: none; }}
    }}

    /* 月曆與卡片基礎樣式 */
    .fc-daygrid-day-frame {{ min-height: 80px !important; }}
    .fc-day-other {{ visibility: hidden !important; }}
    div.fc-event {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 1.6em !important; font-weight: 900 !important; text-align: center !important; }}
    .fc .fc-button-primary {{ background-color: transparent !important; border: 2px solid {user_color} !important; color: {user_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 頂部導覽區 (🚀 取代側邊欄，讓手機直接選人) ---
# 在主頁面最上方放一排按鈕
st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center; margin-bottom:5px; font-size:1.5rem;'>✈️ CAL SCHEDULE</h1>", unsafe_allow_html=True)

# 使用 columns 做出橫向按鈕列
cols = st.columns(4)
names = list(CREW_CONFIG.keys())
for i, name in enumerate(names):
    if cols[i].button(name, key=f"top_btn_{name}"):
        st.session_state.current_user = name
        st.rerun()

st.markdown(f"<h2 style='margin: 10px 0; text-align:center;'>💖 {st.session_state.current_user}</h2>", unsafe_allow_html=True)
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
    st.error(f"數據讀取失敗：{e}")

# --- 4. 渲染月曆 ---
state = calendar(
    events=calendar_events, 
    options={
        "initialDate": "2026-04-01",
        "displayEventTime": False,
        "headerToolbar": {"left": "prev,next", "center": "title", "right": ""},
        "fixedWeekCount": False,
        "showNonCurrentDates": False,
        "height": "auto"
    }, 
    custom_css=f".fc-event-title {{ font-weight: 900 !important; }}",
    key=f"cal_vfinal_mobile_top_{st.session_state.current_user}"
)

# --- 5. 點擊顯示 (卡片邏輯) ---
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
                    arr_t = get_v(['落地時間', '降落時間', '落地'])
                    st.markdown(f"""
                        <div class="flight-card" style="background:#1A1A1A; border-radius:15px; padding:15px; border:3px solid {user_color}; margin-top:10px;">
                            <p style="color:{user_color}; font-size:1rem; font-weight:900; margin:0;">CI {target_f}</p>
                            <p style="font-size:1.5rem; font-weight:950; margin:5px 0;">📍 {dest}</p>
                            <div style="display:flex; justify-content:space-between; background:#262626; padding:8px; border-radius:10px;">
                                <div style="text-align:center;"><p style="font-size:0.6rem; color:#888; margin:0;">起飛</p><p style="font-size:1.1rem; font-weight:800; color:white; margin:0;">{dep_t}</p></div>
                                <div style="text-align:center;"><p style="font-size:0.6rem; color:#888; margin:0;">落地</p><p style="font-size:1.1rem; font-weight:800; color:white; margin:0;">{arr_t}</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
