import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import pytz
import re
import os

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸", "sheet": "Irene"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤", "sheet": "Isabelle"},
    "Elaine": {"color": "#76C9F0", "icon": "👤", "sheet": "Elaine"},
    "Bigpiao": {"color": "#F0B476", "icon": "👤", "sheet": "Bigpiao"}
}

if "current_user" not in st.session_state or st.session_state.current_user not in CREW_CONFIG:
    st.session_state.current_user = "Irene"

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 (暴力填滿縫隙) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    /* 🚀 核心：消除所有縫隙，讓色塊 100% 填滿格子 */
    .fc-daygrid-event-harness {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        background: {user_color} !important;
        border-radius: 0px !important; /* 長班用直角看起來更連貫 */
        margin: 0 !important;
        padding: 2px 0 !important;
        min-height: 2.5em !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    .fc-event-title {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        color: white !important;
        width: 100%;
        text-align: center;
    }}

    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {user_color}; margin-bottom: 15px;
    }}
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
    details_container = st.empty()

# --- 3. 數據讀取與長班邏輯 ---
calendar_events = []
roster_lookup = {}

try:
    xl = pd.ExcelFile("CAL_Roster.xlsx")
    target_sheet = CREW_CONFIG[st.session_state.current_user]["sheet"]
    real_sheet = next((s for s in xl.sheet_names if target_sheet.lower() in s.lower().strip()), None)
    
    if real_sheet:
        user_df = pd.read_excel(xl, sheet_name=real_sheet)
        user_df.columns = user_df.columns.str.strip()
        
        for _, row in user_df.iterrows():
            if pd.isna(row['日期']): continue
            try:
                start_dt = pd.to_datetime(row['日期'])
                f_no = str(row['班號']).strip()
                memo = str(row.get('備註', '')).strip()
                
                # 判定長班終點
                end_dt = start_dt
                rtn_fno = ""
                date_match = re.search(r'(\d+)/(\d+)', memo)
                if date_match:
                    try:
                        m, d = int(date_match.group(1)), int(date_match.group(2))
                        end_dt = datetime(start_dt.year, m, d)
                        rtn_match = re.search(r'\d+/\d+\s+(\d+)', memo)
                        if rtn_match: rtn_fno = rtn_match.group(1)
                    except: pass

                # 1. 主長色塊 (確保全天事件)
                calendar_events.append({
                    "title": f_no,
                    "start": start_dt.strftime('%Y-%m-%d'),
                    "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "allDay": True,
                    "backgroundColor": user_color,
                    "borderColor": user_color
                })

                # 2. 回程日加蓋字樣
                if end_dt > start_dt and rtn_fno:
                    calendar_events.append({
                        "title": rtn_fno,
                        "start": end_dt.strftime('%Y-%m-%d'),
                        "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                        "allDay": True,
                        "backgroundColor": user_color,
                        "borderColor": user_color,
                        "overlap": True
                    })

                roster_lookup[start_dt.strftime('%Y-%m-%d')] = {"fno": f_no, "memo": memo}
            except: continue
except Exception as e:
    st.sidebar.error(f"讀取錯誤：{str(e)}")

# --- 4. 主月曆 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")
calendar(
    events=calendar_events, 
    options={
        "initialDate": today_str, 
        "contentHeight": "auto", 
        "displayEventTime": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    }, 
    custom_css=f".fc-event {{ background-color: {user_color} !important; }} .fc-event-title {{ font-size: 1.8em !important; }}",
    key=f"cal_{st.session_state.current_user}"
)
