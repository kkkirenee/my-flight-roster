import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz
import re

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

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    .fc-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        color: white !important;
        background: {user_color} !important;
    }}
    
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {user_color}; box-shadow: 0 0 20px rgba(240,118,153,0.3);
        margin-bottom: 15px;
    }}
    .tag {{
        background: {user_color}; color: white; padding: 4px 12px;
        border-radius: 6px; font-size: 0.9rem; font-weight: 900;
    }}

    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
        font-size: 1.1rem; transition: 0.3s; margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊導覽 ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color};'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.write("---")
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.write("---")
    st.subheader("📋 Flight Details")
    details_container = st.empty()

# --- 3. 數據讀取 (核心：讀取備註) ---
calendar_events = []
flight_db = pd.DataFrame()
roster_data = {} # 用來存「日期 -> (班號, 備註)」的關係

try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip() # 抓取備註欄
        
        # 存入字典供點擊時查詢
        roster_data[clean_date] = {"fno": f_no, "memo": memo}
        
        calendar_events.append({
            "title": f_no, "start": clean_date, "end": clean_date, "allDay": True
        })
except Exception as e:
    st.sidebar.error(f"讀取失敗，請確認 Excel 是否有「日期」、「班號」、「備註」這三欄")

# --- 4. 顯示主畫面 ---
st.title(f"💖 {st.session_state.current_user}")
custom_css = ".fc-event-title { font-size: 1.8em !important; font-weight: 900 !important; text-align: center !important; color: white !important; }"
state = calendar(events=calendar_events, options={"displayEventTime": False, "dayMaxEvents": False}, custom_css=custom_css, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示邏輯 (根據備註決定內容) ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    day_info = roster_data.get(clicked_date, {})
    main_fno = day_info.get("fno", "")
    memo = day_info.get("memo", "")
    
    # 🚀 從備註中提取所有班號 (例如備註寫 "116/117 來回"，會抓出 ['116', '117'])
    # 如果備註沒寫回程，就只顯示主班號
    flight_list = [main_fno]
    memo_fnos = re.findall(r'\d+', memo)
    for f in memo_fnos:
        if f not in flight_list:
            flight_list.append(f)

    with details_container.container():
        for t in flight_list:
            match = flight_db[flight_db['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                # 判定標籤：過夜班 or 來回班
                is_stay = "過夜" in memo or "Stay" in memo.lower()
                tag = "STAY" if is_stay else ("GO" if t == flight_list[0] and len(flight_list) > 1 else ("RTN" if len(flight_list) > 1 else "FLY"))
                
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{user_color}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:15px 0 5px 0; font-size:1.3rem;'>📍 <b>{r['目的地']}</b></p>
                        <p style='font-size:1.1rem; margin:2px 0;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:10px 0;'>
                        <p style='font-size:1rem; color:#AAA; margin:0;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
else:
    details_container.write("✨ 點擊班號看詳情")
