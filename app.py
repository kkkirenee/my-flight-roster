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

# --- 1. 視覺風格 (2.2em 大字 + 漂漂亮亮配色鎖死) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 強制色塊填滿與配色 */
    div.fc-event, div.fc-event-main, .fc-daygrid-event {{
        background-color: {user_color} !important;
        background: {user_color} !important;
        border: none !important;
        border-radius: 0px !important; 
        margin: 0 !important;
        min-height: 4.5em !important; 
        display: flex !important;
        align-items: center !important;
        cursor: pointer !important;
    }}
    
    /* 🚀 霸氣大字 */
    .fc-event-title {{
        font-size: 2.2em !important; 
        font-weight: 900 !important; 
        color: white !important;
        text-align: center !important;
        width: 100% !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }}

    .fc-daygrid-day-frame {{ min-height: 120px !important; }}

    /* 🚀 漂漂亮亮資訊卡片 */
    .flight-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 4px solid {user_color}; margin-top: 15px;
        box-shadow: 0 0 20px {user_color}44;
    }}
    
    .time-box {{
        display: flex; justify-content: space-between; background: #262626;
        padding: 15px; border-radius: 12px; margin: 10px 0; border: 1px solid #444;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center;'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    for name in CREW_CONFIG.keys():
        if st.button(name, key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    info_placeholder = st.container()

# --- 3. 數據解析 (保持功能一模一樣) ---
calendar_events = []
flight_db = pd.DataFrame()
click_lookup = {} 

try:
    if os.path.exists("my_flights.csv"):
        flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig').fillna("")
        flight_db.columns = flight_db.columns.str.strip()
        flight_db['f_clean'] = flight_db['班號'].astype(str).str.upper().str.replace('CI', '').str.strip()

    xl = pd.ExcelFile("CAL_Roster.xlsx")
    df = pd.read_excel(xl, sheet_name=CREW_CONFIG[st.session_state.current_user]["sheet"])
    df.columns = df.columns.str.strip()

    for _, row in df.iterrows():
        if pd.isna(row['日期']): continue
        start_dt = pd.to_datetime(row['日期'])
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()
        d_key = start_dt.strftime('%Y-%m-%d')

        flight_list = [f_no]
        rtn_fno = ""
        date_pattern = re.search(r'(\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}})', memo)
        rtn_match = re.search(r'回程\s*(\d+)', memo)
        
        if rtn_match:
            rtn_fno = rtn_match.group(1)
            if not date_pattern: flight_list.append(rtn_fno)

        click_lookup[d_key] = {"flights": flight_list, "memo": memo}
        calendar_events.append({"title": f_no, "start": d_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})

        if date_pattern:
            try:
                end_dt = pd.to_datetime(date_pattern.group(1))
                if end_dt > start_dt:
                    if (end_dt - start_dt).days > 1:
                        calendar_events.append({"title": " ", "start": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "end": end_dt.strftime('%Y-%m-%d'), "allDay": True})
                    r_key = end_dt.strftime('%Y-%m-%d')
                    click_lookup[r_key] = {"flights": [rtn_fno], "memo": f"回程自 {start_dt.strftime('%m/%d')} CI{f_no}"}
                    calendar_events.append({"title": rtn_fno, "start": r_key, "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
            except: pass
except Exception as e:
    st.sidebar.error(f"讀取錯誤：{e}")

# --- 4. 渲染月曆 ---
st.title(f"💖 {st.session_state.current_user}")
cal_custom_css = f"""
    .fc-event, div.fc-event-main {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 2.2em !important; font-weight: 900 !important; }}
"""
state = calendar(
    events=calendar_events, 
    options={{"initialDate": "2026-04-01", "displayEventTime": False, "headerToolbar": {{"left": "prev,next today", "center": "title", "right": ""}}}}, 
    custom_css=cal_custom_css,
    key=f"cal_final_ultimate_{st.session_state.current_user}"
)

# --- 5. 點擊顯示 (功能完美鎖定：目的地、報到、起飛、落地) ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = click_lookup.get(clicked_date)
    if info:
        with info_placeholder:
            for fno in info["flights"]:
                target_f = fno.upper().replace('CI', '').strip()
                match = flight_db[flight_db['f_clean'] == target_f] if not flight_db.empty else pd.DataFrame()
                
                if not match.empty:
                    r = match.iloc[0]
                    def get_v(keys):
                        for k in keys:
                            if k in r and str(r[k]).strip() != "": return str(r[k]).strip()
                        return "--:--"

                    dest = get_v(['目的地', '地點'])
                    report = get_v(['報到時間', '報到'])
                    dep_t = get_v(['起飛時間', '起飛'])
                    arr_t = get_v(['落地時間', '降落時間', '降落', 'ARR'])

                    st.markdown(f"""
                        <div class="flight-card">
                            <h2 style='color:{user_color}; margin:0;'>CI {target_f}</h2>
                            <p style='font-size:2.3rem; font-weight:950; margin:15px 0;'>📍 {dest}</p>
                            <p style='font-size:1.3rem; margin-bottom:10px;'>⏰ 報到時間: {report}</p>
                            <div class="time-box">
                                <div style="text-align:center;"><p style="margin:0; font-size:1rem; color:#AAA;">起飛 DEP</p><p style="margin:0; font-size:1.8rem; font-weight:800; color:white;">{dep_t}</p></div>
                                <div style="align-self:center; color:#555; font-size:1.5rem;">✈️</div>
                                <div style="text-align:center;"><p style="margin:0; font-size:1rem; color:#AAA;">落地 ARR</p><p style="margin:0; font-size:1.8rem; font-weight:800; color:white;">{arr_t}</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            st.caption(f"💡 資訊：{info['memo']}")
else:
    info_placeholder.info("✨ 點擊上方班號查看詳細資訊")
