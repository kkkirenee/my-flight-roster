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

# --- 1. 視覺風格 (1.8em 大字與配色) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    
    .fc-event-title {{
        font-size: 1.8em !important; 
        font-weight: 900 !important; 
        text-align: center !important; 
        color: white !important;
        padding: 5px 0;
        white-space: pre-wrap !important; /* 🚀 支援換行顯示回程 */
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

# --- 3. 數據讀取與長班顯示優化 ---
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
                
                # 🚀 長班判定
                end_dt = start_dt
                display_title = f_no
                date_match = re.search(r'(\d+)/(\d+)', memo)
                
                if date_match:
                    try:
                        m, d = int(date_match.group(1)), int(date_match.group(2))
                        end_dt = datetime(start_dt.year, m, d)
                        # 🚀 抓取回程班號 (備註裡日期後面的數字)
                        rtn_match = re.search(r'/\d+\s+(\d+)', memo)
                        if rtn_match:
                            rtn_fno = rtn_match.group(1)
                            # 在月曆標題顯示：去程班號 ... 回程班號
                            display_title = f"{f_no} → {rtn_fno}"
                    except: pass

                date_key = start_dt.strftime('%Y-%m-%d')
                roster_lookup[date_key] = {"fno": f_no, "memo": memo}
                
                calendar_events.append({
                    "title": display_title,
                    "start": start_dt.strftime('%Y-%m-%d'),
                    "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "allDay": True,
                    "backgroundColor": user_color
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

# --- 5. 詳情顯示 (保持不變) ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = roster_lookup.get(clicked_date, {})
    if info:
        main_f, memo = info.get("fno", ""), info.get("memo", "")
        with details_container.container():
            if any(x in main_f.upper() for x in ['HS', 'S']):
                st.markdown(f'<div class="report-card"><h2 style="color:{user_color}">{main_f}</h2><p>📢 待命 (Standby)</p></div>', unsafe_allow_html=True)
            else:
                display_list = [main_f]
                memo_nums = re.findall(r'\d+', memo)
                for n in memo_nums:
                    if n not in memo.split('/')[0] and n not in display_list:
                        if len(n) >= 2: display_list.append(n)
                for t in display_list:
                    match = flight_db[flight_db['班號'] == t] if not flight_db.empty else pd.DataFrame()
                    if not match.empty:
                        r = match.iloc[0]
                        st.markdown(f"""<div class="report-card">
                            <h2 style='color:{user_color};'>CI {t}</h2>
                            <p style='font-size:1.3rem; font-weight:800;'>📍 {r['目的地']}</p>
                            <p>⏰ 報到: {r.get('報到時間','--:--')}</p>
                        </div>""", unsafe_allow_html=True)
else:
    details_container.write("✨ 點擊班號看詳情")
