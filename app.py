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
EVENT_PINK = "#FF8DA1" # 月曆亮粉
BG_BLACK = "#0E0E0E"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 月曆字體：極致放大 */
    .fc-event-title {{ 
        font-size: 1.8em !important; /* 從 1.6 升級到 1.8 */
        font-weight: 900 !important; 
        color: white !important;
        text-align: center !important;
        padding: 8px 0 !important;
    }}
    
    .fc-v-event, .fc-h-event, .fc-event {{
        background-color: {EVENT_PINK} !important;
        border-color: {EVENT_PINK} !important;
        border-radius: 10px !important;
    }}

    /* 📋 右側卡片字體：同步放大 */
    .report-card {{
        background: #1A1A1A; border-radius: 25px; padding: 30px;
        border: 3px solid {WARM_PINK}; 
        box-shadow: 0 0 25px rgba(255,183,197,0.4);
        margin-bottom: 20px;
    }}
    
    .flight-no {{
        font-size: 2.5rem !important; /* 班號超大 */
        color: {WARM_PINK};
        font-weight: 900;
        margin: 0;
    }}

    .dest-text {{
        font-size: 2rem !important; /* 目的地超大 */
        font-weight: 800;
        margin: 20px 0 10px 0;
    }}

    .info-text {{
        font-size: 1.4rem !important; /* 報到與時間字體 */
        line-height: 1.8;
    }}

    .tag {{
        background: {WARM_PINK}; color: #333; padding: 6px 15px;
        border-radius: 8px; font-size: 1.1rem; font-weight: 900;
    }}

    /* Today 大按鈕 */
    div.stButton > button {{
        background-color: {WARM_PINK}; color: #333; border: none;
        font-weight: 900; width: 100%; border-radius: 15px; height: 4em;
        font-size: 1.3rem; /* 按鈕字也放大 */
    }}
    
    .fc .fc-toolbar-title {{
        font-size: 2em !important; /* 月份標題放大 */
        font-weight: 800;
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
    calendar_events.append({"title": f, "start": d, "end": d, "color": EVENT_PINK})

# --- 3. 讀取 CSV ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['班號'] = df['班號'].astype(str).str.replace('CI', '').str.strip()
except:
    st.error("CSV讀取失敗")
    st.stop()

# --- 4. 顯示介面 ---
st.title("💖 FLIGHT CALENDAR")

if st.button(f"📍 SHOW TODAY'S FLIGHT ({today_str})"):
    st.session_state.sel_f = ROSTER.get(today_str, "None")

col1, col2 = st.columns([2, 1.2]) # 微調比例讓卡片寬一點

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "initialDate": today_str,
        "contentHeight": "auto",
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
                tag = "GO" if (len(s_list)>1 and t==target) else ("RTN" if len(s_list)>1 else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h1 class="flight-no">CI {t}</h1>
                            <span class="tag">{tag}</span>
                        </div>
                        <p class="dest-text">📍 {r['目的地']}</p>
                        <p class="info-text">⏰ <b>報到:</b> <span style='color:{WARM_PINK}; font-size:1.8rem;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#555; margin:20px 0;'>
                        <p class="info-text" style='color:#BBB;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.write("✨ 點擊班號，或按大按鈕看今天班表")
