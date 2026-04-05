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
    st.session_state.current_user = "Irene"
if "clicked_date" not in st.session_state:
    st.session_state.clicked_date = None

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; padding-bottom: 0rem !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    [data-testid="stHorizontalBlock"] {{ gap: 0px !important; justify-content: flex-start !important; margin-left: -10px !important; }}
    [data-testid="column"] {{ width: fit-content !important; flex: unset !important; padding: 0px !important; }}

    .stButton > button {{
        width: 78px !important; height: 38px !important;
        font-size: 0.85rem !important; font-weight: 800 !important;
        color: #888 !important; background-color: #1A1A1A !important;
        border: 1px solid #333 !important; border-radius: 0px !important;
        transition: all 0.3s ease !important;
    }}
    [data-testid="column"]:first-child button {{ border-top-left-radius: 12px !important; border-bottom-left-radius: 12px !important; }}
    [data-testid="column"]:nth-child(4) button {{ border-top-right-radius: 12px !important; border-bottom-right-radius: 12px !important; }}

    .stButton > button:focus, .stButton > button:active, .stButton > button:hover {{
        background-color: {user_color} !important;
        color: white !important;
        box-shadow: 0 0 15px {user_color}AA !important;
        border: 1px solid white !important;
        z-index: 10;
    }}

    .fc-event {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 1.6em !important; font-weight: 900 !important; text-align: center !important; }}
    .fc-daygrid-day-frame {{ min-height: 80px !important; }}
    .fc-day-other {{ visibility: hidden !important; }}
    
    @media (max-width: 768px) {{
        .fc-event-title {{ font-size: 1.1em !important; }}
        .fc-daygrid-day-frame {{ min-height: 60px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 頂部導覽 ---
st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center; margin-bottom:5px; font-size:1.3rem;'>✈️ CAL SCHEDULE</h1>", unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns([1,1,1,1,4])
for i, name in enumerate(CREW_CONFIG.keys()):
    with [c1, c2, c3, c4][i]:
        if st.button(name, key=f"nav_{name}"):
            st.session_state.current_user = name
            st.session_state.clicked_date = None
            st.rerun()

st.markdown(f"<h2 style='margin: 5px 0; text-align:center; font-size:1.2rem; color:{user_color};'>💖 {st.session_state.current_user}</h2>", unsafe_allow_html=True)
info_box = st.container()

# --- 3. 數據解析 (🚀 一條龍填色邏輯) ---
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
        d_dt = pd.to_datetime(row['日期'])
        d_str = d_dt.strftime('%Y-%m-%d')
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()
        
        if d_str not in click_lookup: click_lookup[d_str] = {"flights": [], "memo": memo}
        
        # 1. 去程
        if f_no and f_no.lower() != "nan":
            click_lookup[d_str]["flights"].append(f_no)
            calendar_events.append({"title": f_no, "start": d_str, "allDay": True})
        
        # 2. 回程與橫槓填色
        rtn_match = re.search(r'回程\s*(\d+)', memo)
        date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', memo)
        
        if rtn_match:
            r_fno = rtn_match.group(1)
            r_dt = d_dt
            if date_match:
                r_dt = pd.to_datetime(date_match.group(1))
                r_date_str = r_dt.strftime('%Y-%m-%d')
                
                # 🚀 關鍵：用「橫槓」填滿中間的日子
                if (r_dt - d_dt).days > 1:
                    # 從去程隔天開始，到回程前一天
                    stay_start = (d_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                    calendar_events.append({
                        "title": " ", # 空白標題，只顯示顏色槓槓
                        "start": stay_start, 
                        "end": r_date_str, # end 不包含在內，所以會畫到回程前一天
                        "allDay": True
                    })
                
                # 回程當天顯示班號 (如果不同天)
                if r_date_str != d_str:
                    calendar_events.append({"title": r_fno, "start": r_date_str, "allDay": True})
            
            # 不論是否同天，點擊資訊都要有
            final_r_str = r_dt.strftime('%Y-%m-%d')
            if final_r_str not in click_lookup: click_lookup[final_r_str] = {"flights": [], "memo": "回程航班"}
            if r_fno not in click_lookup[final_r_str]["flights"]:
                click_lookup[final_r_str]["flights"].append(r_fno)

except Exception as e:
    st.error(f"解析失敗: {e}")

# --- 4. 月曆渲染 ---
cal_state = calendar(
    events=calendar_events,
    options={
        "initialDate": "2026-04-01",
        "headerToolbar": {"left": "prev,next", "center": "title", "right": ""},
        "fixedWeekCount": False, "showNonCurrentDates": False, "height": "auto"
    },
    custom_css=f".fc-event {{ background-color: {user_color} !important; }}",
    key=f"cal_vfinal_{st.session_state.current_user}"
)

if cal_state.get("eventClick"):
    st.session_state.clicked_date = cal_state["eventClick"]["event"]["start"].split('T')[0]

# --- 5. 顯示卡片 (報到時間維持大字) ---
if st.session_state.clicked_date:
    day_data = click_lookup.get(st.session_state.clicked_date)
    if day_data and day_data["flights"]:
        with info_box:
            for fno in day_data["flights"]:
                target = fno.upper().replace('CI', '').strip()
                match = flight_db[flight_db['f_clean'] == target] if not flight_db.empty else pd.DataFrame()
                
                dest, report, dep, arr = "??", "--:--", "--:--", "--:--"
                if not match.empty:
                    r = match.iloc[0]
                    dest = r.get('目的地', r.get('地點', '??'))
                    report = r.get('報到時間', r.get('報到', '--:--'))
                    dep = r.get('起飛時間', r.get('起飛', '--:--'))
                    arr = r.get('落地時間', r.get('落地', '--:--'))

                st.markdown(f"""
                    <div style="background:#1A1A1A; border-radius:15px; padding:15px; border:3px solid {user_color}; margin-top:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                            <span style="color:{user_color}; font-size:1.1rem; font-weight:900;">CI {target}</span>
                            <span style="font-size:1.1rem; font-weight:900; color:#FFFFFF; background:{user_color}66; padding:3px 10px; border-radius:8px;">⏰ 報到: {report}</span>
                        </div>
                        <p style="font-size:1.6rem; font-weight:950; margin:10px 0;">📍 {dest}</p>
                        <div style="display:flex; justify-content:space-between; background:#262626; padding:12px; border-radius:10px;">
                            <div style="text-align:center;"><p style="font-size:0.75rem; color:#888; margin:0;">起飛 DEP</p><p style="font-size:1.3rem; font-weight:800; color:white; margin:0;">{dep}</p></div>
                            <div style="text-align:center;"><p style="font-size:0.75rem; color:#888; margin:0;">落地 ARR</p><p style="font-size:1.3rem; font-weight:800; color:white; margin:0;">{arr}</p></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
