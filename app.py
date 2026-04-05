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

# --- 1. 視覺風格 (🚀 橫向排排站 + 呼吸光 + 圓角) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; padding-bottom: 0rem !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 讓 columns 在手機上也絕對橫向並排 */
    [data-testid="column"] {{
        width: auto !important;
        flex: 0 0 auto !important; 
        padding: 0px !important;
        margin-right: 4px !important;
    }}
    div[data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: flex-start !important;
        margin-left: -5px !important;
    }}

    /* 🚀 姓名按鈕：獨立圓角 + 呼吸光 */
    .stButton > button {{
        width: 78px !important;
        height: 38px !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        color: #888 !important;
        background-color: #1A1A1A !important;
        border: 2px solid #333 !important;
        border-radius: 12px !important; 
        padding: 0px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}

    .stButton > button:focus, .stButton > button:active, .stButton > button:hover {{
        background-color: {user_color} !important;
        color: white !important;
        box-shadow: 0 0 15px {user_color}AA !important;
        border: 2px solid white !important;
        z-index: 10;
        transform: translateY(-2px);
    }}

    /* 月曆設定 (1.8em 字體) */
    .fc-event, .fc-event-main {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 1.6em !important; font-weight: 900 !important; color: white !important; text-align: center !important; }}
    .fc-daygrid-day-frame {{ min-height: 80px !important; }}
    .fc-day-other {{ visibility: hidden !important; }}

    @media (max-width: 768px) {{
        .fc-event-title {{ font-size: 1.1em !important; }}
        .fc-daygrid-day-frame {{ min-height: 60px !important; }}
        [data-testid="stSidebar"] {{ display: none; }}
    }}

    .fc .fc-button-primary {{ background-color: transparent !important; border: 2px solid {user_color} !important; color: {user_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 頂部導覽 (橫排按鈕) ---
st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center; margin-bottom:5px; font-size:1.3rem;'>✈️ CAL SCHEDULE</h1>", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns([1,1,1,1,2]) # 用一個比例來推擠
with c1: 
    if st.button("Irene"): st.session_state.current_user = "Irene"; st.rerun()
with c2: 
    if st.button("Isabelle"): st.session_state.current_user = "Isabelle"; st.rerun()
with c3: 
    if st.button("Elaine"): st.session_state.current_user = "Elaine"; st.rerun()
with c4: 
    if st.button("Bigpiao"): st.session_state.current_user = "Bigpiao"; st.rerun()

st.markdown(f"<h2 style='margin: 5px 0; text-align:center; font-size:1.2rem; color:{user_color};'>💖 {st.session_state.current_user}</h2>", unsafe_allow_html=True)
info_placeholder = st.empty() # 使用 empty 確保點擊後資訊能正確渲染

# --- 3. 數據解析 (🚀 全部找回來了！) ---
calendar_events = []
flight_db = pd.DataFrame()
click_lookup = {} 

try:
    # 讀取航班詳細資料
    if os.path.exists("my_flights.csv"):
        flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig').fillna("")
        flight_db.columns = flight_db.columns.str.strip()
        flight_db['f_clean'] = flight_db['班號'].astype(str).str.upper().str.replace('CI', '').str.strip()
    
    # 讀取 Excel 班表
    xl = pd.ExcelFile("CAL_Roster.xlsx")
    df = pd.read_excel(xl, sheet_name=CREW_CONFIG[st.session_state.current_user]["sheet"])
    df.columns = df.columns.str.strip()

    for _, row in df.iterrows():
        if pd.isna(row['日期']): continue
        start_dt = pd.to_datetime(row['日期'])
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()
        d_key = start_dt.strftime('%Y-%m-%d')
        
        # 建立基礎飛航清單
        flight_list = [f_no]
        rtn_fno = ""
        
        # 偵測回程日期與班號 (例如: "回程 158 2026/04/05")
        date_pattern = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', memo)
        rtn_match = re.search(r'回程\s*(\d+)', memo)
        
        if rtn_match:
            rtn_fno = rtn_match.group(1)
            if not date_pattern: flight_list.append(rtn_fno)
            
        click_lookup[d_key] = {"flights": flight_list, "memo": memo}
        calendar_events.append({"title": f_no, "start": d_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
        
        # 如果備註有寫回程日期，就在那天也加個事件
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
    st.error(f"讀取錯誤: {e}")

# --- 4. 渲染月曆 ---
st_cal_custom_css = f"""
    .fc-event {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-main {{ background-color: {user_color} !important; }}
    .fc-event-title {{ font-weight: 900 !important; color: white !important; }}
"""
state = calendar(
    events=calendar_events, 
    options={
        "initialDate": "2026-04-01",
        "displayEventTime": False,
        "headerToolbar": {"left": "prev,next", "center": "title", "right": ""},
        "fixedWeekCount": False,
        "showNonCurrentDates": False,
        "height": "auto"
    }, 
    custom_css=st_cal_custom_css,
    key=f"cal_vfinal_full_{st.session_state.current_user}"
)

# --- 5. 點擊顯示卡片 (🚀 資訊顯示完整版回歸) ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = click_lookup.get(clicked_date)
    if info:
        with info_placeholder.container():
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
                    arr_t = get_v(['落地時間', '降落時間', '落地'])
                    
                    st.markdown(f"""
                        <div style="background:#1A1A1A; border-radius:15px; padding:15px; border:3px solid {user_color}; margin-top:10px;">
                            <p style="color:{user_color}; font-size:1rem; font-weight:900; margin:0;">CI {target_f}</p>
                            <p style="font-size:1.5rem; font-weight:950; margin:5px 0;">📍 {dest}</p>
                            <p style="font-size:0.8rem; color:#BBB; margin-bottom:5px;">⏰ 報到: {report}</p>
                            <div style="display:flex; justify-content:space-between; background:#262626; padding:10px; border-radius:10px;">
                                <div style="text-align:center;"><p style="font-size:0.7rem; color:#888; margin:0;">起飛</p><p style="font-size:1.2rem; font-weight:800; color:white; margin:0;">{dep_t}</p></div>
                                <div style="text-align:center;"><p style="font-size:0.7rem; color:#888; margin:0;">落地</p><p style="font-size:1.2rem; font-weight:800; color:white; margin:0;">{arr_t}</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"CI {target_f} 暫無詳細航班資訊")
