import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime

# --- 0. 獲取今天日期 ---
today_date = datetime.now().strftime("%Y-%m-%d")

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL Calendar", page_icon="📅", layout="wide")

HOT_PINK = "#FF2E63"
BG_BLACK = "#0E0E0E"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {HOT_PINK}; box-shadow: 0 0 20px rgba(255,46,99,0.3);
        margin-bottom: 15px;
    }}
    .tag {{
        background: {HOT_PINK}; color: white; padding: 3px 10px;
        border-radius: 6px; font-size: 0.9rem; font-weight: 900;
    }}
    /* 讓 Streamlit 的按鈕變粉紅色 */
    div.stButton > button {{
        background-color: {HOT_PINK}; color: white; border: none;
        font-weight: 800; width: 100%; border-radius: 10px; height: 3em;
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
for date, flight in ROSTER.items():
    calendar_events.append({
        "title": flight, "start": date, "end": date,
        "backgroundColor": HOT_PINK, "borderColor": HOT_PINK
    })

# --- 3. 讀取 CSV ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['班號'] = df['班號'].astype(str)
except:
    st.error("找不到 CSV")
    st.stop()

# --- 4. 顯示介面 ---
st.title("💖 FLIGHT CALENDAR")

# 建立一個大大的 Today 按鈕
if st.button("📍 CLICK FOR TODAY'S FLIGHT"):
    st.session_state.current_flight = ROSTER.get(today_date)
    st.toast(f"Checking flight for {today_date}...")

col1, col2 = st.columns([2.5, 1])

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "contentHeight": "auto",
    }
    custom_css = ".fc-event-title { font-size: 1.6em !important; font-weight: 900 !important; }"
    state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="roster_cal")

with col2:
    st.subheader("📋 Flight Details")
    
    # 判定要顯示哪個班號：優先顯示點擊的，沒點擊則看 Today 按鈕有沒有被按
    target_f = None
    if state.get("eventClick"):
        target_f = state["eventClick"]["event"]["title"].strip()
    elif "current_flight" in st.session_state:
        target_f = st.session_state.current_flight

    if target_f:
        stay_rtn = ["150", "151", "130", "131", "731", "732"]
        search_list = [target_f]
        if target_f not in stay_rtn:
            try: search_list.append(str(int(target_f) + 1))
            except: pass
            
        for t in search_list:
            match = df[df['班號'].str.contains(t)]
            if not match.empty:
                r = match.iloc[0]
                label = "GO" if (len(search_list)>1 and t==target_f) else ("RTN" if len(search_list)>1 else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between;'>
                            <h2 style='color:{HOT_PINK}; margin:0;'>CI {t}</h2>
                            <span class="tag">{label}</span>
                        </div>
                        <p style='margin:15px 0 5px 0; font-size:1.2rem;'>📍 <b>{r['目的地']}</b></p>
                        <p style='font-size:1.1rem;'>⏰ 報到: <span style='color:{HOT_PINK}'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444;'>
                        <p style='margin:0; font-size:1.1rem;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.write("點擊月曆班號，或按上方按鈕看今天班表")
