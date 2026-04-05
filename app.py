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
    st.session_state.current_user = "Irene"

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 (暴力消除縫隙 + 加粗) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 讓色塊 100% 填滿格子的核心 CSS */
    .fc-daygrid-event-harness {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        border-radius: 0px !important; 
        margin: 0 !important;
        padding: 0 !important;
        min-height: 2.8em !important;
        display: flex !important;
        align-items: center !important;
    }}
    .fc-event-title {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; /* 👈 超級加粗 */
        color: white !important;
        width: 100%;
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊欄 ---
with st.sidebar:
    st.title("✈️ SCHEDULE")
    for name in CREW_CONFIG.keys():
        if st.button(name):
            st.session_state.current_user = name
            st.rerun()

# --- 3. 數據讀取 (長班邏輯強化) ---
calendar_events = []
try:
    xl = pd.ExcelFile("CAL_Roster.xlsx")
    df = pd.read_excel(xl, sheet_name=CREW_CONFIG[st.session_state.current_user]["sheet"])
    df.columns = df.columns.str.strip()

    for _, row in df.iterrows():
        if pd.isna(row['日期']): continue
        start_dt = pd.to_datetime(row['日期'])
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()

        # 🚀 強化版結束日期抓取：支援 2026-4-10 或 4/10 或 4-10
        end_dt = start_dt
        rtn_fno = ""
        
        # 尋找備註中的日期
        date_pattern = re.search(r'(\d{4}[-/])?(\d{1,2})[-/](\d{1,2})', memo)
        if date_pattern:
            try:
                m, d = int(date_pattern.group(2)), int(date_pattern.group(3))
                end_dt = datetime(start_dt.year, m, d)
                # 抓取日期後面的班號 (例如 058 或 074)
                rtn_match = re.search(r'回程\s*(\d+)', memo)
                if rtn_match: rtn_fno = rtn_match.group(1)
            except: pass

        # 1. 加入主長色塊 (從 7 號刷到 11 號)
        calendar_events.append({
            "title": f_no,
            "start": start_dt.strftime('%Y-%m-%d'),
            "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
            "allDay": True,
            "backgroundColor": user_color
        })

        # 2. 如果是長班，在最後一天補上回程班號
        if end_dt > start_dt and rtn_fno:
            calendar_events.append({
                "title": rtn_fno,
                "start": end_dt.strftime('%Y-%m-%d'),
                "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                "allDay": True,
                "backgroundColor": user_color,
                "overlap": True
            })
except Exception as e:
    st.sidebar.error(f"讀取錯誤：{e}")

# --- 4. 顯示月曆 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")
calendar(
    events=calendar_events, 
    options={"initialDate": "2026-04-06", "contentHeight": "auto", "displayEventTime": False}, 
    key=st.session_state.current_user
)
