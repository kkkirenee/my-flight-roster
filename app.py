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

# --- 1. 視覺風格 (1.8em 大字與色塊優化) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    /* 🚀 讓所有 Event 標籤都強制變大字、置中、專屬色 */
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        background: {user_color} !important;
        border-radius: 4px !important;
        margin: 1px 0 !important;
    }}
    
    .fc-event-title {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        text-align: center !important; 
        color: white !important;
        padding: 4px 0;
    }}

    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {user_color}; margin-bottom: 15px;
    }}
    
    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
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

# --- 3. 數據讀取與長班邏輯 (🚀 確保色塊連貫 + 末端顯示) ---
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
                
                # 判定長班
                end_dt = start_dt
                rtn_fno = ""
                date_match = re.search(r'(\d+)/(\d+)', memo)
                if date_match:
                    try:
                        m, d = int(date_match.group(1)), int(date_match.group(2))
                        # 建立回程日期 (如果是跨月如 4/30，這裡會精準抓到 4 月 30 日)
                        end_dt = datetime(start_dt.year, m, d)
                        # 抓取班號 (如 4/30 074 裡的 074)
                        rtn_match = re.search(r'\d+/\d+\s+(\d+)', memo)
                        if rtn_match: rtn_fno = rtn_match.group(1)
                    except: pass

                # 1. 建立「去程長色塊」：從去程日開始，長度拉到回程日
                calendar_events.append({
                    "title": f_no,
                    "start": start_dt.strftime('%Y-%m-%d'),
                    "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "allDay": True
                })

                # 2. 🚀 關鍵補強：如果在回程日有班號，就在那天「加蓋一個獨立色塊」顯示回程班號
                if end_dt > start_dt and rtn_fno:
                    calendar_events.append({
                        "title": rtn_fno,
                        "start": end_dt.strftime('%Y-%m-%d'),
                        "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                        "allDay": True,
                        "overlap": True # 允許重疊在長色塊之上
                    })

                roster_lookup[start_dt.strftime('%Y-%m-%d')] = {"fno": f_no, "memo": memo}
            except: continue
except Exception as e:
    st.sidebar.error(f"讀取錯誤：{str(e)}")

# --- 4. 主月曆 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")
calendar(
    events=calendar_events, 
    options={"initialDate": today_str, "contentHeight": "auto", "displayEventTime": False}, 
    custom_css=".fc-event-title { font-size: 1.8em !important; font-weight: 900 !important; }",
    key=f"cal_{st.session_state.current_user}"
)
