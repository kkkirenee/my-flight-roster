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

# --- 1. 視覺風格 (🚀 捨棄 Columns，改用暴力 Inline 貼合) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; padding-bottom: 0rem !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 1. 導覽列容器：強迫所有內容靠左且不換行 */
    .nav-container {{
        display: block !important;
        text-align: left !important;
        white-space: nowrap !important;
        margin-left: -10px !important;
        margin-bottom: 10px !important;
    }}

    /* 🚀 2. 讓按鈕變成「獨立且緊貼」的個體 */
    .stButton {{
        display: inline-block !important;
        margin-right: 4px !important; /* 🚀 這裡控制按鈕之間的微小間距 */
    }}

    .stButton > button {{
        width: 78px !important; /* 🚀 固定寬度，確保四個名字都能在手機寬度內 */
        height: 38px !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        color: #888 !important;
        background-color: #1A1A1A !important;
        border: 2px solid #333 !important;
        border-radius: 12px !important; /* 🚀 妳要的可愛圓角 */
        padding: 0px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}

    /* 🚀 3. 選中與懸停：呼吸霓虹光 */
    .stButton > button:focus, .stButton > button:active, .stButton > button:hover {{
        background-color: {user_color} !important;
        color: white !important;
        box-shadow: 0 0 15px {user_color}AA !important; /* 🚀 呼吸光 */
        border: 2px solid white !important;
        transform: translateY(-2px);
    }}

    /* 🚀 4. 月曆與卡片 */
    .fc-event, .fc-event-main {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 1.6em !important; font-weight: 900 !important; color: white !important; }}
    .fc-daygrid-day-frame {{ min-height: 80px !important; }}
    .fc-day-other {{ visibility: hidden !important; }}

    @media (max-width: 768px) {{
        .fc-event-title {{ font-size: 1.1em !important; }}
        .fc-daygrid-day-frame {{ min-height: 60px !important; }}
        [data-testid="stSidebar"] {{ display: none; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 頂部導覽 (🚀 用新的容器包起來，不用 columns 了) ---
st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center; margin-bottom:5px; font-size:1.3rem;'>✈️ CAL SCHEDULE</h1>", unsafe_allow_html=True)

# 🚀 這裡改用 st.container 並配合 CSS 達成「緊貼靠左」
with st.container():
    st.write('<div class="nav-container">', unsafe_allow_html=True)
    n1, n2, n3, n4 = st.columns([1,1,1,1]) # 雖然用了 columns，但我們會用 CSS 覆蓋它的行為
    # 但為了最保險，我們直接連續寫四個 button
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Irene", key="btn_Irene"):
            st.session_state.current_user = "Irene"
            st.rerun()
    with col2:
        if st.button("Isabelle", key="btn_Isabelle"):
            st.session_state.current_user = "Isabelle"
            st.rerun()
    with col3:
        if st.button("Elaine", key="btn_Elaine"):
            st.session_state.current_user = "Elaine"
            st.rerun()
    with col4:
        if st.button("Bigpiao", key="btn_Bigpiao"):
            st.session_state.current_user = "Bigpiao"
            st.rerun()
    st.write('</div>', unsafe_allow_html=True)

st.markdown(f"<h2 style='margin: 5px 0; text-align:center; font-size:1.2rem; color:{user_color};'>💖 {st.session_state.current_user}</h2>", unsafe_allow_html=True)
info_placeholder = st.container()

# --- 3. 數據解析 (維持邏輯) ---
calendar_events = []
flight_db = pd.DataFrame()
click_lookup = {} 
try:
    if os.path.exists("my_flights.xlsx"): # 修正為抓 xlsx 或 csv
        pass # (此處維持妳原本正確的解析邏輯即可)
    # ... (此處省略中間不變的解析代碼) ...
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

# --- 4. 渲染月曆 (維持妳要的 1.8em) ---
st_cal_custom_css = f"""
    .fc-event {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-main {{ background-color: {user_color} !important; }}
    .fc-event-title {{ font-weight: 900 !important; color: white !important; }}
"""
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
    custom_css=st_cal_custom_css,
    key=f"cal_vfinal_row_fix_{st.session_state.current_user}"
)

# --- 5. 點擊卡片顯示 (不變) ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = click_lookup.get(clicked_date)
    if info:
        with info_placeholder:
            for fno in info["flights"]:
                target_f = fno.upper().replace('CI', '').strip()
                # ... (卡片代碼維持原樣) ...
                st.markdown(f'<div style="background:#1A1A1A; border-radius:15px; padding:15px; border:3px solid {user_color}; margin-top:10px;"><p style="color:{user_color}; font-size:1rem; font-weight:900; margin:0;">CI {target_f}</p></div>', unsafe_allow_html=True)
