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

# --- 1. 視覺風格 (2.2em 大字 + 配色鎖死) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    div.fc-event {{
        background-color: {user_color} !important;
        border: none !important; border-radius: 0px !important; 
        min-height: 4.5em !important; display: flex !important; align-items: center !important;
    }}
    .fc-event-title {{ font-size: 2.2em !important; font-weight: 900 !important; color: white !important; text-align: center !important; width: 100% !important; }}
    .fc-daygrid-day-frame {{ min-height: 120px !important; }}
    .flight-card {{ background: #1A1A1A; border-radius: 20px; padding: 20px; border: 3px solid {user_color}; margin-bottom: 15px; }}
    .time-box {{ display: flex; justify-content: space-between; background: #262626; padding: 12px; border-radius: 10px; margin: 8px 0; border: 1px solid #444; }}
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

# --- 3. 數據解析 (🚀 支援 "落地時間" 辨識) ---
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
        date_pattern = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', memo)
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
state = calendar(events=calendar_events, options={"initialDate": "2026-04-01", "displayEventTime": False}, key=f"cal_final_{st.session_state.current_user}")

# --- 5. 🚀 點擊顯示 (🚀 這裡會去抓 "落地時間") ---
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
                    # 🚀 多重欄位匹配，確保 "落地時間" 會被抓到
                    def get_v(keys):
                        for k in keys:
                            if k in r and str(r[k]).strip() != "": return str(r[k]).strip()
                        return "--:--"

                    dest = get_v(['目的地', '地點'])
                    report = get_v(['報到時間', '報到'])
                    dep_t = get_v(['起飛時間', '起飛'])
                    # 🚀 把「落地時間」排在第一順位抓取！
                    arr_t = get_v(['落地時間', '降落時間', '降落', 'ARR'])

                    st.markdown(f"""
                        <div class="flight-card">
                            <h2 style='color:{user_color}; margin:0;'>CI {target_f}</h2>
                            <p style='font-size:2.1rem; font-weight:950; margin:10px 0;'>📍 {dest}</p>
                            <p style='font-size:1.1rem; margin-bottom:5px;'>⏰ 報到時間: {report}</p>
                            <div class="time-box">
                                <div style="text-align:center;"><p style="margin:0; font-size:0.8rem; color:#AAA;">起飛 DEP</p><p style="margin:0; font-size:1.4rem; font-weight:800;">{dep_t}</p></div>
                                <div style="align-self:center; color:#555;">✈️</div>
                                <div style="text-align:center;"><p style="margin:0; font-size:0.8rem; color:#AAA;">落地 ARR</p><p style="margin:0; font-size:1.4rem; font-weight:800;">{arr_t}</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            st.caption(f"💡 資訊：{info['memo']}")
