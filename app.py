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

# --- 1. 視覺風格 (2em 大字 + 無縫填滿) ---
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
        min-height: 4.5em !important; 
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
    }}

    .fc-daygrid-day-frame {{ min-height: 120px !important; }}

    .flight-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {user_color}; margin-top: 20px;
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
    info_placeholder = st.empty()

# --- 3. 數據解析 (建立對照表) ---
calendar_events = []
flight_db = pd.DataFrame()
roster_lookup = {} 

try:
    if os.path.exists("my_flights.csv"):
        flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig')
        flight_db.columns = flight_db.columns.str.strip()
        # 清洗 CSV 班號：CI112 -> 112
        flight_db['班號_clean'] = flight_db['班號'].astype(str).str.upper().str.replace('CI', '').str.strip()

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

        # 去程資訊
        d_key = start_dt.strftime('%Y-%m-%d')
        roster_lookup[d_key] = {"fno": f_no, "memo": memo}

        if end_dt > start_dt:
            calendar_events.append({"title": f_no, "start": d_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
            if (end_dt - start_dt).days > 1:
                calendar_events.append({"title": " ", "start": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "end": end_dt.strftime('%Y-%m-%d'), "allDay": True})
            if rtn_fno:
                r_key = end_dt.strftime('%Y-%m-%d')
                roster_lookup[r_key] = {"fno": rtn_fno, "memo": f"回程航班 {rtn_fno} (去程 CI{f_no})"}
                calendar_events.append({"title": rtn_fno, "start": r_key, "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
        else:
            calendar_events.append({"title": f_no, "start": d_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})

except Exception as e:
    st.sidebar.error(f"讀取錯誤：{e}")

# --- 4. 渲染月曆 (使用固定 Key 確保點擊有效) ---
st.title(f"💖 {st.session_state.current_user}")
cal_custom_css = f".fc-event-title {{ font-size: 2em !important; font-weight: 900 !important; }}"

state = calendar(
    events=calendar_events, 
    options={
        "initialDate": "2026-04-01", "contentHeight": "auto", "displayEventTime": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    }, 
    custom_css=cal_custom_css,
    key="fixed_calendar_v100" # 🚀 固定 Key，不准亂跳！
)

# --- 5. 點擊顯示 (最強修復邏輯) ---
if state.get("eventClick"):
    # 修正：直接從 event 對象抓取日期
    try:
        clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
        info = roster_lookup.get(clicked_date)
        
        if info:
            target_f = str(info['fno']).upper().replace('CI', '').strip()
            match = flight_db[flight_db['班號_clean'] == target_f] if not flight_db.empty else pd.DataFrame()
            
            with info_placeholder.container():
                if not match.empty:
                    r = match.iloc[0]
                    st.markdown(f"""
                        <div class="flight-card">
                            <h2 style='color:{user_color}; margin:0;'>CI {target_f}</h2>
                            <p style='font-size:1.8rem; font-weight:900; margin:15px 0;'>📍 {r['目的地']}</p>
                            <p style='font-size:1.3rem; margin-bottom:10px;'>⏰ 報到時間: {r.get('報到時間','--:--')}</p>
                            <hr style='border: 0.5px solid #444;'>
                            <p style='color:#AAA; font-size:1rem;'>資訊：{info['memo']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="flight-card">
                            <h2 style='color:{user_color}; margin:0;'>CI {target_f}</h2>
                            <p style='margin:20px 0; font-size:1.2rem;'>⚠️ CSV 找不到 {target_f} 資訊</p>
                            <hr style='border: 0.5px solid #444;'>
                            <p style='color:#AAA; font-size:1rem;'>資訊：{info['memo']}</p>
                        </div>
                    """, unsafe_allow_html=True)
    except:
        info_placeholder.error("解析點擊資料失敗，請重新 Reboot")
else:
    info_placeholder.info("✨ 點擊上方班號查看詳細資訊")
