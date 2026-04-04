import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 時區校準 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL Calendar", page_icon="📅", layout="wide")

WARM_PINK = "#FFB7C5"  # 暖粉紅
EVENT_PINK = "#FF8DA1" # 亮粉紅
BG_BLACK = "#0E0E0E"

st.markdown(f"""
    <style>
    /* 全域背景 */
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 終極暴力法：強制把所有月曆相關的藍色通通洗掉 */
    div[data-testid="stHtml"] *, 
    .fc-event, 
    .fc-event-main, 
    .fc-daygrid-event, 
    .fc-v-event, 
    .fc-h-event,
    .fc-event-active,
    .fc-event-future {{
        background-color: {EVENT_PINK} !important;
        border-color: {EVENT_PINK} !important;
        background: {EVENT_PINK} !important;
        color: white !important;
        box-shadow: none !important;
    }}
    
    /* 🚀 數字字體：放大到 2.2em 並確保是白色 */
    .fc-event-title, .fc-event-main-frame {{ 
        font-size: 2.2em !important; 
        font-weight: 900 !important; 
        color: white !important;
        text-align: center !important;
    }}

    /* 詳情卡片樣式 */
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {WARM_PINK}; box-shadow: 0 0 20px rgba(255,183,197,0.3);
        margin-bottom: 15px;
    }}
    .tag {{
        background: {WARM_PINK}; color: #333; padding: 4px 12px;
        border-radius: 6px; font-size: 0.9rem; font-weight: 900;
    }}

    /* 大按鈕樣式 */
    div.stButton > button {{
        background-color: {WARM_PINK}; color: #333; border: none;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 班表資料 ---
ROSTER = {
    "2026-04-03": "116", "2026-04-05": "517", "2026-04-08": "108",
    "2026-04-10": "915", "2026-04-12": "150", "2026-04-13": "151",
    "2026-04-14": "130", "2026-04-15": "131", "2026-04-16": "527", 
    "2026-04-18": "731", "2026-04-19": "732", "2026-04-21": "186", 
    "2026-04-23": "783", "2026-04-25": "190", "2026-04-30": "156"
}

calendar_events = []
for d, f in ROSTER.items():
    calendar_events.append({
        "title": f, 
        "start": d, 
        "end": d,
        "backgroundColor": EVENT_PINK,
        "borderColor": EVENT_PINK,
        "allDay": True # 強制設為全天事件，避免它出現時間點的樣式
    })

# --- 3. 讀取 CSV ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['班號'] = df['班號'].astype(str).str.replace('CI', '').str.strip()
except:
    st.error("CSV 讀取失敗")
    st.stop()

# --- 4. 顯示介面 ---
st.title("💖 FLIGHT CALENDAR")

if st.button(f"📍 SHOW TODAY'S FLIGHT ({today_str})"):
    st.session_state.sel_f = ROSTER.get(today_str, "None")

col1, col2 = st.columns([2.5, 1])

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "initialDate": today_str,
        "contentHeight": "auto",
        "eventColor": EVENT_PINK, # 第五重保險
        "displayEventTime": False, # 絕對不要顯示時間
    }
    state = calendar(events=calendar_events, options=calendar_options, key="roster_cal")

with col2:
    st.subheader("📋 Flight Details")
    target = None
    if state.get("eventClick"):
        target = state["eventClick"]["event"]["title"].strip()
    elif "sel_f" in st.session_state:
        target = st.session_state.sel_f

    if target and target != "None":
        stay_list = ["150", "151", "130", "131", "731", "732"]
        s_list = [target]
        if target not in stay_list:
            try: s_list.append(str(int(target) + 1))
            except: pass
            
        for t in s_list:
            match = df[df['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                tag_txt = "GO" if (len(s_list)>1 and t==target) else ("RTN" if len(s_list)>1 else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{WARM_PINK}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag_txt}</span>
                        </div>
                        <p style='margin:15px 0 5px 0; font-size:1.4rem; font-weight:700;'>📍 <b>{r['目的地']}</b></p>
                        <p style='font-size:1.1rem; color:#CCC;'>⏰ 報到: <span style='color:{WARM_PINK}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:15px 0;'>
                        <p style='margin:0; font-size:1.1rem; color:#AAA;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.write("✨ 點擊班號，或按大按鈕看今天班表")
