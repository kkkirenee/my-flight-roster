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

# --- 1. 視覺風格 (最強暴力字體鎖定) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 讓色塊像油漆一樣完全填滿 */
    .fc-daygrid-event-harness {{ 
        margin: 0 !important; 
        padding: 0 !important;
    }}
    .fc-daygrid-day-events {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        border-radius: 0px !important; 
        margin: 0 !important;
        min-height: 4.5em !important; 
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    /* 🚀 字體絕對加粗 + 放大 (2em + Scale 強化) */
    .fc-event-title {{
        font-size: 2em !important; 
        font-weight: 900 !important; 
        color: white !important;
        text-align: center !important;
        width: 100% !important;
        display: block !important;
        transform: scale(1.1); 
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}

    .fc-daygrid-day-frame {{
        min-height: 120px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{user_color}'>✈️ SCHEDULE</h2>", unsafe_allow_html=True)
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

        end_dt = start_dt
        rtn_fno = ""
        date_pattern = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', memo)
        
        if date_pattern:
            try:
                end_dt = pd.to_datetime(date_pattern.group(1))
                rtn_match = re.search(r'回程\s*(\d+)', memo)
                if rtn_match: rtn_fno = rtn_match.group(1)
            except: pass

        if end_dt > start_dt:
            calendar_events.append({
                "title": f_no,
                "start": start_dt.strftime('%Y-%m-%d'),
                "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                "allDay": True
            })
            if (end_dt - start_dt).days > 1:
                calendar_events.append({
                    "title": " ", 
                    "start": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "end": end_dt.strftime('%Y-%m-%d'),
                    "allDay": True
                })
            if rtn_fno:
                calendar_events.append({
                    "title": rtn_fno,
                    "start": end_dt.strftime('%Y-%m-%d'),
                    "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "allDay": True
                })
        else:
            calendar_events.append({
                "title": f_no,
                "start": start_dt.strftime('%Y-%m-%d'),
                "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                "allDay": True
            })
except Exception as e:
    st.sidebar.error(f"讀取錯誤：{e}")

# --- 4. 渲染月曆 ---
st.title(f"💖 {st.session_state.current_user}")

cal_custom_css = f"""
    .fc-event {{ 
        background-color: {user_color} !important; 
        border: none !important;
        margin: 0 !important;
    }}
    .fc-event-title {{ 
        font-size: 2em !important; 
        font-weight: 900 !important; 
        transform: scale(1.1);
    }}
"""

# 🚀 修正後的語法：把多餘的大括號去掉了
calendar(
    events=calendar_events, 
    options={
        "initialDate": "2026-04-01", 
        "contentHeight": "auto", 
        "displayEventTime": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    }, 
    custom_css=cal_custom_css,
    key=st.session_state.current_user + "_v_final_fixed"
)
