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

# --- 1. 視覺風格 (1.8em 大字) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    /* 🚀 長班主色塊樣式 */
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    
    /* 🚀 讓回程文字(透明背景)也能顯示大字 */
    .fc-event-title {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        text-align: center !important; 
        color: white !important;
        padding: 5px 0;
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

# --- 3. 數據讀取與「回程自動補字」邏輯 ---
calendar_events = []
flight_db = pd.DataFrame()
roster_lookup = {}

try:
    if os.path.exists("my_flights.csv"):
        flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig')
        flight_db.columns = flight_db.columns.str.strip()
        flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
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
                
                # 🚀 1. 建立主色塊 (長度依據備註日期)
                end_dt = start_dt
                rtn_fno = ""
                date_match = re.search(r'(\d+)/(\d+)', memo)
                if date_match:
                    try:
                        m, d = int(date_match.group(1)), int(date_match.group(2))
                        end_dt = datetime(start_dt.year, m, d)
                        # 抓取回程班號
                        rtn_match = re.search(r'/\d+\s+(\d+)', memo)
                        if rtn_match: rtn_fno = rtn_match.group(1)
                    except: pass

                # 存入查詢字典
                roster_lookup[start_dt.strftime('%Y-%m-%d')] = {"fno": f_no, "memo": memo}
                
                # 加入主長班色塊 (從去程開始畫)
                calendar_events.append({
                    "title": f_no,
                    "start": start_dt.strftime('%Y-%m-%d'),
                    "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "allDay": True,
                    "backgroundColor": user_color
                })

                # 🚀 2. 關鍵：如果這是一個長班，在「回程日」那天加蓋一個顯示回程班號的事件
                if end_dt > start_dt and rtn_fno:
                    calendar_events.append({
                        "title": rtn_fno,
                        "start": end_dt.strftime('%Y-%m-%d'),
                        "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                        "allDay": True,
                        "backgroundColor": "rgba(0,0,0,0)", # 透明背景，不重複蓋色
                        "borderColor": "transparent",
                        "display": "list-item" # 確保文字疊加顯示
                    })
            except: continue
except Exception as e:
    st.sidebar.error(f"讀取錯誤：{str(e)}")

# --- 4. 主月曆 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")
state = calendar(
    events=calendar_events, 
    options={"initialDate": today_str, "contentHeight": "auto", "displayEventTime": False, "dayMaxEvents": False}, 
    custom_css=".fc-event-title { font-size: 1.8em !important; font-weight: 900 !important; }",
    key=f"cal_{st.session_state.current_user}"
)

# --- 5. 詳情顯示 ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = roster_lookup.get(clicked_date, {})
    if info:
        main_f, memo = info.get("fno", ""), info.get("memo", "")
        with details_container.container():
            st.markdown(f'<div class="report-card"><h2 style="color:{user_color}">CI {main_f}</h2><p>備註：{memo}</p></div>', unsafe_allow_html=True)
