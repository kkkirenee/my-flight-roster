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

# --- 1. 視覺風格 (最強暴力鎖定) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    .fc-daygrid-event-harness {{ margin: 0 !important; padding: 0 !important; }}
    .fc-daygrid-day-events {{ margin: 0 !important; padding: 0 !important; }}
    
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        border-radius: 0px !important; 
        margin: 0 !important;
        min-height: 4.2em !important; 
        display: flex !important;
        align-items: center !important;
        cursor: pointer !important;
    }}
    
    .fc-event-title {{
        font-size: 2em !important; 
        font-weight: 900 !important; 
        color: white !important;
        text-align: center !important;
        width: 100% !important;
        transform: scale(1.1); 
    }}

    .fc-daygrid-day-frame {{ min-height: 120px !important; }}

    /* 🚀 航班資訊卡片樣式 */
    .flight-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {user_color}; margin-top: 20px;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
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
    st.divider()
    # 🚀 準備詳情顯示區
    info_placeholder = st.empty()

# --- 3. 數據解析 (長班拆解 + 詳情對照表) ---
calendar_events = []
flight_db = pd.DataFrame()
roster_lookup = {} # 🚀 用來存點擊時要顯示的資訊

try:
    # 讀取航班資料庫
    if os.path.exists("my_flights.csv"):
        flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig')
        flight_db.columns = flight_db.columns.str.strip()
        flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()

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

        # 🚀 存入查找表
        date_key = start_dt.strftime('%Y-%m-%d')
        roster_lookup[date_key] = {"fno": f_no, "memo": memo}
        if end_dt > start_dt and rtn_fno:
            roster_lookup[end_dt.strftime('%Y-%m-%d')] = {"fno": rtn_fno, "memo": "回程航班"}

        # 建立事件
        if end_dt > start_dt:
            calendar_events.append({"title": f_no, "start": date_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
            if (end_dt - start_dt).days > 1:
                calendar_events.append({"title": " ", "start": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "end": end_dt.strftime('%Y-%m-%d'), "allDay": True})
            if rtn_fno:
                calendar_events.append({"title": rtn_fno, "start": end_dt.strftime('%Y-%m-%d'), "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
        else:
            calendar_events.append({"title": f_no, "start": date_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})

except Exception as e:
    st.sidebar.error(f"讀取錯誤：{e}")

# --- 4. 渲染月曆 ---
st.title(f"💖 {st.session_state.current_user}")

cal_custom_css = f".fc-event {{ background-color: {user_color} !important; }} .fc-event-title {{ font-size: 2em !important; font-weight: 900 !important; }}"

state = calendar(
    events=calendar_events, 
    options={
        "initialDate": "2026-04-01", 
        "contentHeight": "auto", 
        "displayEventTime": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    }, 
    custom_css=cal_custom_css,
    key=st.session_state.current_user + "_final_complete"
)

# --- 5. 🚀 點擊事件顯示 ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = roster_lookup.get(clicked_date)
    if info:
        target_f = info['fno']
        # 從 csv 找資料
        match = flight_db[flight_db['班號'] == target_f] if not flight_db.empty else pd.DataFrame()
        
        with info_placeholder.container():
            if not match.empty:
                r = match.iloc[0]
                st.markdown(f"""
                    <div class="flight-card">
                        <h2 style='color:{user_color}; margin:0;'>CI {target_f}</h2>
                        <p style='font-size:1.5rem; font-weight:800; margin:10px 0;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.2rem;'>⏰ 報到時間: {r.get('報到時間','--:--')}</p>
                        <p style='color:#888; font-size:0.9rem; margin-top:10px;'>備註: {info['memo']}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="flight-card">
                        <h2 style='color:{user_color};'>{target_f}</h2>
                        <p>未在 CSV 中找到此航班詳情</p>
                        <p style='color:#888;'>備註: {info['memo']}</p>
                    </div>
                """, unsafe_allow_html=True)
else:
    info_placeholder.info("✨ 點擊上方班號查看詳細資訊")
