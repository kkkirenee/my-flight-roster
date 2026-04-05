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

# --- 1. 視覺風格 (最強力字體鎖定) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 全域強制字體加粗與放大 */
    .fc-event-title, .fc-event-main, .fc-event {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        color: white !important;
        line-height: 1.2 !important;
    }}
    
    .fc-daygrid-event-harness {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        border-radius: 0px !important; 
        margin: 0 !important;
        min-height: 3.5em !important;
        display: flex !important;
        align-items: center !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: #151515;
        border-right: 2px solid {user_color};
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

# --- 3. 數據解析 ---
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

        # 解析長班日期與回程班號
        end_dt = start_dt
        rtn_fno = ""
        date_pattern = re.search(r'(\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}})', memo)
        if date_pattern:
            try:
                end_dt = pd.to_datetime(date_pattern.group(1))
                rtn_match = re.search(r'回程\s*(\d+)', memo)
                if rtn_match: rtn_fno = rtn_match.group(1)
            except: pass

        # 1. 繪製長色塊
        calendar_events.append({
            "title": f_no,
            "start": start_dt.strftime('%Y-%m-%d'),
            "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color
        })

        # 2. 回程日補上大字
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
except Exception as e:
    st.sidebar.error(f"讀取錯誤：{e}")

# --- 4. 渲染月曆 (這裡也灌入 CSS) ---
st.title(f"💖 {st.session_state.current_user}")

# 🚀 這裡的 custom_css 是搶回主導權的關鍵
custom_css = """
    .fc-event-title { 
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
    }
    .fc-event {
        border-radius: 0px !important;
    }
"""

calendar(
    events=calendar_events, 
    options={
        "initialDate": "2026-04-01", 
        "contentHeight": "auto", 
        "displayEventTime": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    }, 
    custom_css=custom_css,
    key=st.session_state.current_user + "_cal"
)
