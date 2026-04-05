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

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    div.fc-event, div.fc-event-main, div.fc-daygrid-event {{
        background-color: {user_color} !important;
        border: none !important;
        background: {user_color} !important;
        border-radius: 8px !important;
    }}
    
    .fc-event-title {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        text-align: center !important; 
        color: white !important;
        padding-top: 5px;
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
    st.divider()
    details_container = st.empty()

# --- 3. 數據讀取與長班邏輯 ---
calendar_events = []
flight_db = pd.DataFrame()
roster_lookup = {}

try:
    flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel("CAL_Roster.xlsx", sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_val = row['日期']
        if pd.isna(raw_val): continue
        
        # 🚀 日期容錯處理
        if isinstance(raw_val, datetime):
            start_dt = raw_val
        else:
            start_dt = pd.to_datetime(str(raw_val))
            
        start_date = start_dt.date()
        date_key = start_date.strftime('%Y-%m-%d')
        
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()
        
        # 🚀 長班判讀：從備註抓回程日期 (支援 4/10 或 04/10)
        end_date = start_date
        date_match = re.search(r'(\d+)/(\d+)', memo)
        if date_match:
            try:
                m, d = int(date_match.group(1)), int(date_match.group(2))
                # 自動補上年份
                end_date = datetime(start_dt.year, m, d).date()
            except: pass

        roster_lookup[date_key] = {"fno": f_no, "memo": memo}
        
        calendar_events.append({
            "title": f_no,
            "start": start_date.strftime('%Y-%m-%d'),
            # 色塊要蓋滿最後一天，end 必須是 回程日+1
            "end": (end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            "allDay": True
        })
except Exception as e:
    st.sidebar.error(f"讀取出錯：{str(e)}")

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
    main_f = info.get("fno", "")
    memo = info.get("memo", "")
    
    with details_container.container():
        # 🚀 待命判讀 (HS 或 S 開頭)
        if any(main_f.upper().startswith(x) for x in ['HS', 'S']):
            st.markdown(f"""<div class="report-card">
                <h2 style='color:{user_color}; margin:0;'>{main_f}</h2>
                <p style='margin:10px 0; font-size:1.3rem; font-weight:800;'>📢 待命 (Standby)</p>
                <p style='color:#AAA;'>備註：{memo}</p>
            </div>""", unsafe_allow_html=True)
        else:
            # 正常航班拆解 (包含備註裡的班號)
            display_list = [main_f]
            memo_nums = re.findall(r'\d+', memo)
            for n in memo_nums:
                # 排除日期格式中的數字 (例如 4/10 不會把 4 和 10 當成班號)
                if n not in memo.split('/')[0] and n not in display_list:
                    if len(n) >= 2: # 班號通常至少兩碼
                        display_list.append(n)

            for t in display_list:
                match = flight_db[flight_db['班號'] == t]
                if not match.empty:
                    r = match.iloc[0]
                    tag = "STAY" if ("/" in memo or "過夜" in memo) else ("GO" if (len(display_list)>1 and t==display_list[0]) else "FLY")
                    st.markdown(f"""<div class="report-card">
                        <h2 style='color:{user_color}; margin:0;'>CI {t} <span style='font-size:0.8rem; background:{user_color}; padding:2px 8px; border-radius:5px;'>{tag}</span></h2>
                        <p style='margin:10px 0; font-size:1.3rem; font-weight:800;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.1rem;'>⏰ 報到: {r.get('報到時間','--:--')}</p>
                        <hr style='border-color:#444;'>
                        <p style='font-size:0.9rem; color:#AAA;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>""", unsafe_allow_html=True)
else:
    details_container.write("✨ 點擊班號看詳情")
