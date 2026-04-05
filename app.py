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

# --- 1. 視覺風格 (配色鎖死 + 2.2em 大字) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    div.fc-event, div.fc-event-main, .fc-daygrid-event {{
        background-color: {user_color} !important; background: {user_color} !important;
        border: none !important; border-radius: 0px !important; margin: 0 !important;
        min-height: 4.5em !important; display: flex !important; align-items: center !important; cursor: pointer !important;
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
    info_placeholder = st.sidebar.container() # 🚀 改為容器，方便噴發多個卡片

# --- 3. 數據解析 (🚀 核心：解析雙班號) ---
calendar_events = []
flight_db = pd.DataFrame()
click_lookup = {} 

try:
    if os.path.exists("my_flights.csv"):
        flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig')
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

        # 🚀 建立班號清單
        flight_list = [f_no]
        rtn_fno = ""
        
        # 抓取回程班號 (不管長班還是單日)
        rtn_match = re.search(r'回程\s*(\d+)', memo)
        if rtn_match:
            rtn_fno = rtn_match.group(1)
            # 如果是單日來回，當天就要顯示兩份資訊
            rtn_date_pattern = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', memo)
            if not rtn_date_pattern: # 代表是當天來回
                flight_list.append(rtn_fno)

        # 存入對照表
        click_lookup[d_key] = {"flights": flight_list, "memo": memo}
        calendar_events.append({"title": f_no, "start": d_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})

        # 長班跨日邏輯
        if rtn_date_pattern:
            try:
                end_dt = pd.to_datetime(rtn_date_pattern.group(1))
                if end_dt > start_dt:
                    if (end_dt - start_dt).days > 1:
                        calendar_events.append({"title": " ", "start": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "end": end_dt.strftime('%Y-%m-%d'), "allDay": True})
                    r_key = end_dt.strftime('%Y-%m-%d')
                    click_lookup[r_key] = {"flights": [rtn_fno], "memo": f"回程自 {start_dt.strftime('%m/%d')} CI{f_no}"}
                    calendar_events.append({"title": rtn_fno, "start": r_key, "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
            except: pass

except Exception as e:
    st.sidebar.error(f"Excel 讀取失敗：{e}")

# --- 4. 渲染月曆 ---
st.title(f"💖 {st.session_state.current_user}")
state = calendar(
    events=calendar_events, 
    options={"initialDate": "2026-04-01", "contentHeight": "auto", "displayEventTime": False, "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""}}, 
    custom_css=f".fc-event-title {{ font-size: 2.2em !important; font-weight: 900 !important; }}",
    key=f"cal_v110_{st.session_state.current_user}"
)

# --- 5. 🚀 點擊事件 (一次顯示去/回兩份 CSV 資料) ---
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
                    st.markdown(f"""
                        <div class="flight-card">
                            <h2 style='color:{user_color}; margin:0;'>CI {target_f}</h2>
                            <p style='font-size:2rem; font-weight:950; margin:10px 0;'>📍 {r['目的地']}</p>
                            <p style='font-size:1.1rem; margin-bottom:5px;'>⏰ 報到時間: {r.get('報到時間','--:--')}</p>
                            <div class="time-box">
                                <div style="text-align:center;"><p style="margin:0; font-size:0.8rem; color:#AAA;">起飛 DEP</p><p style="margin:0; font-size:1.3rem; font-weight:800;">{r.get('起飛時間','--:--')}</p></div>
                                <div style="align-self:center; color:#555;">✈️</div>
                                <div style="text-align:center;"><p style="margin:0; font-size:0.8rem; color:#AAA;">降落 ARR</p><p style="margin:0; font-size:1.3rem; font-weight:800;">{r.get('降落時間','--:--')}</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='flight-card'><h2>CI {target_f}</h2><p>CSV 找不到資訊</p></div>", unsafe_allow_html=True)
            st.caption(f"💡 資訊：{info['memo']}")
else:
    info_placeholder.info("✨ 點擊班號查看詳細資訊")
