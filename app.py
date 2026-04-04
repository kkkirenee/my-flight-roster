import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 時區校準 (台灣時區) ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL Calendar", page_icon="📅", layout="wide")

# ✨ 這裡定義妳最愛的粉紅色調
MY_PINK = "#FF8DA1" # 亮粉紅
WARM_PINK = "#FFB7C5" # 淡粉紅 (用於邊框與按鈕)
BG_BLACK = "#0E0E0E"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {WARM_PINK}; box-shadow: 0 0 20px rgba(255,183,197,0.3);
        margin-bottom: 15px;
    }}
    .tag {{
        background: {WARM_PINK}; color: #333; padding: 4px 12px;
        border-radius: 6px; font-size: 0.9rem; font-weight: 900;
    }}
    /* 今天按鈕 */
    div.stButton > button {{
        background-color: {WARM_PINK}; color: #333; border: none;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
        font-size: 1.1rem;
    }}
    
    /* 🚀 月曆核心樣式：粉紅底、大白字 */
    .fc-event-title {{ 
        font-size: 1.6em !important; 
        font-weight: 900 !important; 
        color: white !important; /* 絕對是白色！ */
        text-align: center !important;
    }}
    .fc-dayGridMonth-view .fc-event {{
        background-color: {MY_PINK} !important; /* 絕對是粉紅！ */
        border-color: {MY_PINK} !important;
        border-radius: 8px !important;
        padding: 5px 0 !important;
    }}
    .fc .fc-button-primary {{
        background-color: #333 !important;
        border-color: {WARM_PINK} !important;
        color: {WARM_PINK} !important;
    }}
    .fc .fc-day-today {{
        background: rgba(255, 141, 161, 0.2) !important;
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
    calendar_events.append({"title": f, "start": d, "end": d})

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

col1, col2 = st.columns([2.5, 1])

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
                            <h2 style='color:{WARM_PINK}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:15px 0 5px 0; font-size:1.4rem; font-weight:700;'>📍 <b>{r['目的地']}</b></p>
                        <p style='font-size:1.1rem; color:#CCC;'>⏰ 報到: <span style='color:{WARM_PINK}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:15px 0;'>
                        <p style='margin:0; font-size:1.1rem; color:#AAA;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.write("✨ 點擊班號，或按大按鈕看今天班表")
