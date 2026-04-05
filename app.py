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

# --- 1. 視覺風格 (1.8em 鎖死 + 消除所有間距) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 讓色塊像膠帶一樣貼滿，完全不留白 */
    .fc-daygrid-event-harness {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        border-radius: 0px !important; 
        margin: 0 !important;
        min-height: 3.2em !important;
        display: flex !important;
        align-items: center !important;
        box-shadow: none !important;
    }}
    
    /* 🚀 字體大小加粗強勢回歸 */
    .fc-event-title, .fc-event-main {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        color: white !important;
        width: 100%;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
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

# --- 3. 數據解析 (長班與回程邏輯強化) ---
calendar_events = []
try:
    xl = pd.ExcelFile("CAL_Roster.xlsx")
    df = pd.read_excel(xl, sheet_name=CREW_CONFIG[st.session_state.current_user]["sheet"])
    df.columns = df.columns.str.strip()

    for _, row in df.iterrows():
        if pd.isna(row['日期']): continue
        # 處理日期，確保相容性
        try:
            start_dt = pd.to_datetime(row['日期'])
        except:
            continue
            
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()

        # 🚀 精準抓取備註裡的日期與回程班號
        end_dt = start_dt
        rtn_fno = ""
        
        # 尋找 2026-04-11 這種格式
        date_pattern = re.search(r'(\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}})', memo)
        if date_pattern:
            try:
                end_dt = pd.to_datetime(date_pattern.group(1))
                # 抓取回程字眼後的數字
                rtn_match = re.search(r'回程\s*(\d+)', memo)
                if rtn_match: rtn_fno = rtn_match.group(1)
            except: pass

        # 1. 建立「去程長色塊」：確保連貫性
        calendar_events.append({
            "title": f_no,
            "start": start_dt.strftime('%Y-%m-%d'),
            "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'), # FullCalendar end 是 exclusive
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color
        })

        # 2. 建立「回程加蓋」：確保最後一天有大班號
        if end_dt > start_dt and rtn_fno:
            calendar_events.append({
                "title": rtn_fno,
                "start": end_dt.strftime('%Y-%m-%d'),
                "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                "allDay": True,
                "backgroundColor": "transparent", # 透明背景，不疊加顏色
                "borderColor": "transparent",
                "overlap": True
            })
except Exception as e:
    st.sidebar.error(f"讀取錯誤：{e}")

# --- 4. 渲染月曆 ---
st.title(f"💖 {st.session_state.current_user}")

# 內外部 CSS 雙重鎖定 1.8em
cal_custom_css = """
    .fc-event-title { font-size: 1.8em !important; font-weight: 900 !important; }
    .fc-daygrid-event { margin: 0 !important; }
"""

calendar(
    events=calendar_events, 
    options={
        "initialDate": "2026-04-01", 
        "contentHeight": "auto", 
        "displayEventTime": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    }, 
    custom_css=cal_custom_css,
    key=st.session_state.current_user + "_final_cal"
)
